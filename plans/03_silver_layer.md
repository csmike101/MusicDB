# Phase 3: Silver Layer

**Status:** Complete

---

## Goal

Transform bronze data into clean, normalized (3NF) tables with proper data types, constraints, and deduplication. This layer handles all data quality remediation.

---

## Files to Create

| File | Purpose |
|------|---------|
| `03_silver/01_create_tables.sql` | DDL for silver tables with constraints |
| `03_silver/02_transform_data.sql` | SQL transformations from bronze |
| `03_silver/03_create_indexes.sql` | Performance indexes |
| `03_silver/silver.db` | SQLite database (generated) |

---

## Silver Table Schemas

### listeners
```sql
CREATE TABLE listeners (
    listener_id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    birth_date DATE,
    city TEXT,  -- nullable
    country TEXT NOT NULL,
    subscription_type TEXT NOT NULL CHECK (subscription_type IN ('free', 'premium')),
    created_at DATETIME NOT NULL
);
```

### artists
```sql
CREATE TABLE artists (
    artist_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    genre TEXT NOT NULL,  -- normalized casing
    country TEXT NOT NULL,
    formed_year INTEGER,  -- nullable
    monthly_listeners INTEGER NOT NULL
);
```

### tracks
```sql
CREATE TABLE tracks (
    track_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    artist_id TEXT NOT NULL REFERENCES artists(artist_id),
    album TEXT,  -- nullable
    duration_ms INTEGER NOT NULL,
    genre TEXT NOT NULL,
    release_date DATE NOT NULL,
    explicit INTEGER NOT NULL  -- 0 or 1
);
```

### streams
```sql
CREATE TABLE streams (
    stream_id TEXT PRIMARY KEY,
    listener_id TEXT NOT NULL REFERENCES listeners(listener_id),
    track_id TEXT NOT NULL REFERENCES tracks(track_id),
    streamed_at DATETIME NOT NULL,
    duration_played_ms INTEGER NOT NULL,
    device_type TEXT NOT NULL,
    shuffle_mode INTEGER NOT NULL,  -- 0 or 1
    offline_mode INTEGER NOT NULL   -- 0 or 1
);
```

---

## Transformation Logic

### Genre Normalization
```sql
-- Standardize genre casing to Title Case
SELECT
    artist_id,
    TRIM(name) AS name,
    -- Normalize genre: first letter uppercase, rest lowercase
    UPPER(SUBSTR(LOWER(TRIM(genre)), 1, 1)) ||
    LOWER(SUBSTR(TRIM(genre), 2)) AS genre,
    country,
    CAST(formed_year AS INTEGER) AS formed_year,
    CAST(monthly_listeners AS INTEGER) AS monthly_listeners
FROM bronze_artists;
```

### Date Parsing
```sql
-- Handle multiple date formats in release_date
-- Common formats: YYYY-MM-DD, MM/DD/YYYY, DD-MM-YYYY
CASE
    WHEN release_date LIKE '____-__-__' THEN release_date
    WHEN release_date LIKE '__/__/____' THEN
        SUBSTR(release_date, 7, 4) || '-' ||
        SUBSTR(release_date, 1, 2) || '-' ||
        SUBSTR(release_date, 4, 2)
    ELSE NULL  -- log unparseable dates
END AS release_date
```

### Deduplication
```sql
-- Remove duplicate streams using row_hash (keep first occurrence)
INSERT INTO streams
SELECT
    stream_id,
    listener_id,
    track_id,
    streamed_at,
    CAST(duration_played_ms AS INTEGER),
    device_type,
    CASE WHEN LOWER(shuffle_mode) IN ('true', '1') THEN 1 ELSE 0 END,
    CASE WHEN LOWER(offline_mode) IN ('true', '1') THEN 1 ELSE 0 END
FROM bronze_streams
WHERE _row_hash IN (
    SELECT _row_hash
    FROM bronze_streams
    GROUP BY _row_hash
    HAVING COUNT(*) = 1

    UNION

    SELECT _row_hash
    FROM (
        SELECT _row_hash, ROW_NUMBER() OVER (PARTITION BY _row_hash ORDER BY _loaded_at) AS rn
        FROM bronze_streams
    )
    WHERE rn = 1
);
```

### Invalid FK Handling
```sql
-- Only include streams with valid track_id references
INSERT INTO streams
SELECT ...
FROM bronze_streams bs
WHERE EXISTS (
    SELECT 1 FROM tracks t WHERE t.track_id = bs.track_id
);

-- Log rejected records
INSERT INTO silver_rejected_records
SELECT 'streams', stream_id, 'Invalid track_id: ' || track_id, CURRENT_TIMESTAMP
FROM bronze_streams bs
WHERE NOT EXISTS (
    SELECT 1 FROM tracks t WHERE t.track_id = bs.track_id
);
```

---

## Indexes

```sql
-- 03_silver/03_create_indexes.sql

-- Listener lookups
CREATE INDEX idx_listeners_email ON listeners(email);
CREATE INDEX idx_listeners_country ON listeners(country);

-- Artist lookups
CREATE INDEX idx_artists_genre ON artists(genre);
CREATE INDEX idx_artists_country ON artists(country);

-- Track lookups
CREATE INDEX idx_tracks_artist_id ON tracks(artist_id);
CREATE INDEX idx_tracks_genre ON tracks(genre);
CREATE INDEX idx_tracks_release_date ON tracks(release_date);

-- Stream analysis (critical for performance)
CREATE INDEX idx_streams_listener_id ON streams(listener_id);
CREATE INDEX idx_streams_track_id ON streams(track_id);
CREATE INDEX idx_streams_streamed_at ON streams(streamed_at);
CREATE INDEX idx_streams_device_type ON streams(device_type);
```

---

## Rejected Records Table

```sql
CREATE TABLE silver_rejected_records (
    source_table TEXT NOT NULL,
    source_id TEXT,
    rejection_reason TEXT NOT NULL,
    rejected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---

## Tasks

- [x] Create `03_silver/01_create_tables.sql`
- [x] Create `03_silver/02_transform_data.sql`
- [x] Create `03_silver/03_create_indexes.sql`
- [x] Run DDL to create tables
- [x] Execute transformations
- [x] Create indexes
- [x] Verify data quality improvements
- [x] Review rejected records

---

## Verification

```sql
-- Row counts (should be slightly less than bronze due to dedup/FK filtering)
SELECT 'listeners' AS table_name, COUNT(*) AS row_count FROM listeners
UNION ALL
SELECT 'artists', COUNT(*) FROM artists
UNION ALL
SELECT 'tracks', COUNT(*) FROM tracks
UNION ALL
SELECT 'streams', COUNT(*) FROM streams;

-- Verify no duplicate streams
SELECT COUNT(*) - COUNT(DISTINCT stream_id) AS duplicate_count FROM streams;
-- Expected: 0

-- Verify genre normalization
SELECT DISTINCT genre FROM artists ORDER BY genre;
-- Should show consistent Title Case

-- Verify FK integrity
SELECT COUNT(*) FROM streams s
WHERE NOT EXISTS (SELECT 1 FROM tracks t WHERE t.track_id = s.track_id);
-- Expected: 0

-- Check rejected records
SELECT source_table, rejection_reason, COUNT(*) AS count
FROM silver_rejected_records
GROUP BY source_table, rejection_reason;
```

### Actual Results
| Table | Bronze Rows | Silver Rows | Difference |
|-------|-------------|-------------|------------|
| listeners | 50 | 50 | 0 (no issues) |
| artists | 100 | 100 | 0 (no issues) |
| tracks | 1,000 | 1,000 | 0 (all artist FKs valid) |
| streams | 100,999 | 99,493 | -1,506 (dupes + invalid track FKs) |

**Rejected Records:** 507 streams with invalid track_id references (trk_1001-trk_1100)
