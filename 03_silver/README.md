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

## Real-World Analogies

**Silver = Quality Control on a Production Line**

Imagine a car factory. Raw materials (Bronze) arrive from suppliers. Before assembly, Quality Control (Silver) checks each part:
- Is it the right size? (type validation)
- Is it the correct part? (FK validation)
- Is it a duplicate shipment? (deduplication)

Defective parts don't disappear—they go to a rejection bin with a tag explaining why (rejected records table). This lets you trace issues back to the supplier.

**Deduplication = Removing Photocopies**

If someone accidentally photocopied a document and put both copies in the filing cabinet, you'd want to remove the duplicate. But you need to decide *which* copy to keep. We keep the first one (by `_loaded_at` timestamp), just like you'd keep the original.

## Common Mistakes to Avoid

**1. Silently dropping bad data**
```sql
-- BAD: Where did these rows go?
INSERT INTO silver_table SELECT * FROM bronze_table WHERE valid = 1;

-- GOOD: Log what you're rejecting
INSERT INTO rejected_records SELECT id, 'Invalid data' FROM bronze_table WHERE valid = 0;
INSERT INTO silver_table SELECT * FROM bronze_table WHERE valid = 1;
```

**2. Case-sensitive duplicate handling**
```sql
-- BAD: These look like duplicates but aren't matched
WHERE email = 'User@Example.com'  -- won't match 'user@example.com'

-- GOOD: Normalize before comparing
WHERE LOWER(TRIM(email)) = LOWER(TRIM(other_email))
```

**3. Assuming dates parse correctly**
```sql
-- BAD: SQLite silently returns NULL for unparseable dates
SELECT DATE('not-a-date');  -- Returns NULL, no error!

-- GOOD: Validate the result
CASE WHEN DATE(release_date) IS NOT NULL THEN DATE(release_date)
     ELSE [log error and handle] END
```

**4. Forgetting to index foreign keys**
```sql
-- Silver has FK relationships, but SQLite doesn't auto-index them
-- Without indexes, JOIN performance degrades badly at scale
CREATE INDEX idx_streams_track_id ON streams(track_id);
```

## Exploration Exercises

```sql
-- 1. Compare genre values before/after normalization
-- (Attach bronze database first)
ATTACH '../02_bronze/bronze.db' AS bronze;

SELECT 'bronze' AS layer, genre, COUNT(*)
FROM bronze.bronze_artists GROUP BY genre
UNION ALL
SELECT 'silver', genre, COUNT(*)
FROM artists GROUP BY genre
ORDER BY genre;

-- 2. Find the most common rejection reasons
SELECT rejection_reason, COUNT(*) as count
FROM silver_rejected_records
GROUP BY rejection_reason
ORDER BY count DESC
LIMIT 10;

-- 3. Verify deduplication worked
SELECT
    (SELECT COUNT(*) FROM bronze.bronze_streams) as bronze_count,
    (SELECT COUNT(*) FROM streams) as silver_count,
    (SELECT COUNT(*) FROM bronze.bronze_streams) -
    (SELECT COUNT(*) FROM streams) as removed;

-- 4. Check data type conversions
SELECT typeof(duration_ms) as type, COUNT(*)
FROM streams
GROUP BY typeof(duration_ms);
-- Should show 'integer' for all rows
```

## Design Decisions Explained

**Why reject streams with invalid track_ids instead of keeping them?**

A stream without a valid track is meaningless for analytics. "User X listened to [unknown]" doesn't help. We reject these but log them so we can investigate why tracks are missing.

**Why normalize genre casing?**

"Rock" and "rock" are the same genre to humans. If we don't normalize, analytics queries need `LOWER()` everywhere, which is error-prone and slow.

**Why use INTEGER for booleans instead of TEXT 'true'/'false'?**

- Storage: INTEGER uses 1 byte; TEXT 'false' uses 5 bytes
- Performance: Integer comparison is faster
- Aggregation: `SUM(shuffle_mode)` counts TRUE values directly

## Next Steps

After silver data is ready, proceed to **04_gold/** to build the dimensional model (star schema).
