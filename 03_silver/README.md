# Layer 3: Silver (Cleaned & Normalized)

## Overview

The **Silver Layer** transforms raw bronze data into clean, validated, and normalized tables. This is where data quality remediation happens—deduplication, type casting, constraint enforcement, and foreign key validation.

## Key Principles

### 1. Proper Data Types
- TEXT → DATE, DATETIME, INTEGER as appropriate
- Boolean strings ('True'/'False') → INTEGER (0/1)
- Numeric strings → INTEGER

### 2. Data Cleaning
- **Trimmed whitespace** on all string fields
- **Normalized casing** (genres to Title Case, emails to lowercase)
- **Standardized dates** (multiple formats → ISO YYYY-MM-DD)
- **Deduplication** (removed duplicate streams using row hash)

### 3. Constraints Enforced
- PRIMARY KEY on all tables
- FOREIGN KEY relationships validated
- NOT NULL where required
- CHECK constraints (subscription_type, explicit flag, etc.)

### 4. Rejected Records Tracked
Records failing validation are logged to `silver_rejected_records` for audit.

## Files in This Layer

| File | Description |
|------|-------------|
| `01_create_tables.sql` | DDL with constraints |
| `02_transform_data.sql` | Transformation logic from bronze |
| `03_create_indexes.sql` | Performance indexes |
| `silver.db` | SQLite database (generated) |

## Schema

### listeners
```sql
CREATE TABLE listeners (
    listener_id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    birth_date DATE,
    city TEXT,
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
    genre TEXT NOT NULL,  -- normalized Title Case
    country TEXT NOT NULL,
    formed_year INTEGER,
    monthly_listeners INTEGER NOT NULL
);
```

### tracks
```sql
CREATE TABLE tracks (
    track_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    artist_id TEXT NOT NULL REFERENCES artists(artist_id),
    album TEXT,
    duration_ms INTEGER NOT NULL,
    genre TEXT NOT NULL,
    release_date DATE NOT NULL,
    explicit INTEGER NOT NULL CHECK (explicit IN (0, 1))
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
    shuffle_mode INTEGER NOT NULL CHECK (shuffle_mode IN (0, 1)),
    offline_mode INTEGER NOT NULL CHECK (offline_mode IN (0, 1))
);
```

## Data Transformations Applied

### 1. Genre Normalization
Bronze genres had inconsistent casing ("Rock", "rock", "ROCK"). Silver normalizes to Title Case.

```sql
UPPER(SUBSTR(LOWER(TRIM(genre)), 1, 1)) || LOWER(SUBSTR(TRIM(genre), 2))
```

### 2. Date Parsing
Bronze had multiple date formats. Silver standardizes to ISO format.

```sql
CASE
    WHEN release_date LIKE '____-__-__' THEN DATE(release_date)
    WHEN release_date LIKE '__/__/____' THEN
        DATE(SUBSTR(release_date, 7, 4) || '-' || ...)
    ELSE DATE(release_date)
END
```

### 3. Deduplication
Duplicate streams (same row hash) are reduced to single records using ROW_NUMBER().

### 4. FK Validation
Streams referencing non-existent tracks are rejected and logged.

## Running This Layer

```bash
cd 03_silver
python -c "
import sqlite3
conn = sqlite3.connect('silver.db')
for sql_file in ['01_create_tables.sql', '02_transform_data.sql', '03_create_indexes.sql']:
    with open(sql_file) as f:
        conn.executescript(f.read())
conn.close()
"
```

## Data Results

| Table | Bronze Rows | Silver Rows | Difference | Reason |
|-------|-------------|-------------|------------|--------|
| listeners | 50 | 50 | 0 | No issues |
| artists | 100 | 100 | 0 | No issues |
| tracks | 1,000 | 1,000 | 0 | All artist FKs valid |
| streams | 100,999 | 99,493 | -1,506 | Duplicates + invalid FKs |

### Rejected Records Summary
- **507 streams** rejected for invalid track_id (references to trk_1001-trk_1100 which don't exist)
- Remaining difference (~999) from duplicate removal

## Verification Queries

```sql
-- Check row counts
SELECT 'listeners' AS tbl, COUNT(*) FROM listeners
UNION ALL SELECT 'artists', COUNT(*) FROM artists
UNION ALL SELECT 'tracks', COUNT(*) FROM tracks
UNION ALL SELECT 'streams', COUNT(*) FROM streams;

-- Verify no duplicates
SELECT COUNT(*) - COUNT(DISTINCT stream_id) AS duplicates FROM streams;
-- Expected: 0

-- Verify genre normalization
SELECT DISTINCT genre FROM artists ORDER BY genre;
-- Should show Title Case only

-- Verify FK integrity
SELECT COUNT(*) FROM streams s
WHERE NOT EXISTS (SELECT 1 FROM tracks t WHERE t.track_id = s.track_id);
-- Expected: 0

-- Review rejected records
SELECT source_table, COUNT(*) AS rejected
FROM silver_rejected_records
GROUP BY source_table;
```

## Indexes Created

| Index | Table | Column(s) | Purpose |
|-------|-------|-----------|---------|
| idx_listeners_email | listeners | email | Account lookup |
| idx_listeners_country | listeners | country | Geographic analytics |
| idx_artists_genre | artists | genre | Genre browsing |
| idx_tracks_artist_id | tracks | artist_id | Artist discography |
| idx_streams_listener_id | streams | listener_id | User history |
| idx_streams_track_id | streams | track_id | Play counts |
| idx_streams_streamed_at | streams | streamed_at | Time-based analytics |
| idx_streams_listener_time | streams | listener_id, streamed_at | User activity over time |

## Key Concepts Demonstrated

1. **Third Normal Form (3NF)** - Each table represents one entity with no redundancy
2. **Type coercion** - Converting strings to proper types (DATE, INTEGER)
3. **Referential integrity** - Foreign keys enforced
4. **Data cleansing** - Whitespace, casing, date format standardization
5. **Deduplication** - Removing exact duplicate records
6. **Audit trail** - Rejected records logged with reasons

## Next Steps

After silver data is ready, proceed to **04_gold/** to build the dimensional model (star schema).
