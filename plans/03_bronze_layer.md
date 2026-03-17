# Phase 3: Bronze Layer

**Status:** Complete

---

## Goal

Create staging tables that preserve raw data exactly as-is, with audit columns for lineage tracking. All columns are TEXT type to handle any input format.

---

## Files to Create

| File | Purpose |
|------|---------|
| `01_bronze/01_create_tables.sql` | DDL for bronze tables |
| `01_bronze/02_load_data.py` | Python script to load raw files into bronze |
| `01_bronze/bronze.db` | SQLite database (generated) |

---

## Bronze Table Schemas

### bronze_listeners
```sql
CREATE TABLE bronze_listeners (
    listener_id TEXT,
    email TEXT,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    birth_date TEXT,
    city TEXT,
    country TEXT,
    subscription_type TEXT,
    created_at TEXT,
    -- Audit columns
    _source_file TEXT,
    _loaded_at TEXT,
    _row_hash TEXT
);
```

### bronze_artists
```sql
CREATE TABLE bronze_artists (
    artist_id TEXT,
    name TEXT,
    genre TEXT,
    country TEXT,
    formed_year TEXT,
    monthly_listeners TEXT,
    -- Audit columns
    _source_file TEXT,
    _loaded_at TEXT,
    _row_hash TEXT
);
```

### bronze_tracks
```sql
CREATE TABLE bronze_tracks (
    track_id TEXT,
    title TEXT,
    artist_id TEXT,
    album TEXT,
    duration_ms TEXT,
    genre TEXT,
    release_date TEXT,
    explicit TEXT,
    -- Audit columns
    _source_file TEXT,
    _loaded_at TEXT,
    _row_hash TEXT
);
```

### bronze_streams
```sql
CREATE TABLE bronze_streams (
    stream_id TEXT,
    listener_id TEXT,
    track_id TEXT,
    streamed_at TEXT,
    duration_played_ms TEXT,
    device_type TEXT,
    shuffle_mode TEXT,
    offline_mode TEXT,
    -- Audit columns
    _source_file TEXT,
    _loaded_at TEXT,
    _row_hash TEXT
);
```

---

## Loading Script Design

```python
# 01_bronze/02_load_data.py

import sqlite3
import json
import csv
import hashlib
from datetime import datetime
from pathlib import Path

def compute_row_hash(row: dict) -> str:
    """Compute MD5 hash of row contents for deduplication."""
    content = json.dumps(row, sort_keys=True)
    return hashlib.md5(content.encode()).hexdigest()

def load_json_to_bronze(db_path: str, table: str, json_path: str):
    """Load JSON file into bronze table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    with open(json_path, 'r') as f:
        records = json.load(f)

    loaded_at = datetime.utcnow().isoformat()
    source_file = Path(json_path).name

    for record in records:
        row_hash = compute_row_hash(record)
        # Insert with audit columns
        ...

    conn.commit()
    conn.close()

def load_csv_to_bronze(db_path: str, table: str, csv_path: str):
    """Load CSV file into bronze table."""
    # Similar pattern for CSV files
    ...

if __name__ == "__main__":
    DB_PATH = "01_bronze/bronze.db"
    RAW_PATH = "00_raw/data"

    # Create tables first (run 01_create_tables.sql)

    # Load all raw files
    load_json_to_bronze(DB_PATH, "bronze_listeners", f"{RAW_PATH}/listeners.json")
    load_json_to_bronze(DB_PATH, "bronze_artists", f"{RAW_PATH}/artists.json")
    load_json_to_bronze(DB_PATH, "bronze_tracks", f"{RAW_PATH}/tracks.json")
    load_csv_to_bronze(DB_PATH, "bronze_streams", f"{RAW_PATH}/streams.csv")
```

---

## Key Concepts

1. **All TEXT columns** - Preserves raw data exactly, handles any format
2. **No constraints** - Accept all data, including invalid/malformed records
3. **Audit columns** - Track lineage:
   - `_source_file`: Original filename
   - `_loaded_at`: UTC timestamp of load
   - `_row_hash`: MD5 hash for deduplication tracking
4. **Idempotent loads** - Can reload safely (truncate and load pattern)

---

## Tasks

- [x] Create `01_bronze/01_create_tables.sql`
- [x] Create `01_bronze/02_load_data.py`
- [x] Run DDL to create tables
- [x] Load all raw files into bronze tables
- [x] Verify row counts match raw data
- [x] Verify audit columns populated correctly

---

## Verification

Run these queries after loading:

```sql
-- Row counts should match raw files
SELECT 'bronze_listeners' AS table_name, COUNT(*) AS row_count FROM bronze_listeners
UNION ALL
SELECT 'bronze_artists', COUNT(*) FROM bronze_artists
UNION ALL
SELECT 'bronze_tracks', COUNT(*) FROM bronze_tracks
UNION ALL
SELECT 'bronze_streams', COUNT(*) FROM bronze_streams;

-- Verify audit columns populated
SELECT
    _source_file,
    _loaded_at,
    COUNT(*) AS records
FROM bronze_streams
GROUP BY _source_file, _loaded_at;

-- Check for duplicates (should exist in streams)
SELECT _row_hash, COUNT(*) AS occurrences
FROM bronze_streams
GROUP BY _row_hash
HAVING COUNT(*) > 1
LIMIT 10;
```

### Actual Results
| Table | Rows | Notes |
|-------|------|-------|
| bronze_listeners | 50 | All loaded |
| bronze_artists | 100 | All loaded |
| bronze_tracks | 1,000 | All loaded |
| bronze_streams | 100,999 | Includes 999 duplicates (detectable via _row_hash) |
