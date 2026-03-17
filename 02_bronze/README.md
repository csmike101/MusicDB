# Layer 2: Bronze (Raw Staging)

## Overview

The **Bronze Layer** is the first database layer in the medallion architecture. It serves as a staging area where raw data is loaded with minimal transformation, preserving the original data exactly as received.

## Key Principles

### 1. Preserve Raw Data Fidelity
- **All columns stored as TEXT** - No type coercion that might fail or lose data
- **No data cleaning** - Duplicates, nulls, and invalid values are kept
- **Exact representation** - What came in is what gets stored

### 2. Add Audit Columns
Every bronze table includes metadata for tracking data lineage:

| Column | Purpose |
|--------|---------|
| `_source_file` | Name of the source file |
| `_loaded_at` | UTC timestamp when the record was loaded |
| `_row_hash` | MD5 hash of row contents for deduplication tracking |

### 3. No Constraints
- No PRIMARY KEY enforcement (duplicates allowed)
- No FOREIGN KEY checks (invalid references allowed)
- No CHECK constraints (invalid values allowed)

This accepts all data and defers validation to the Silver layer.

## Why This Approach?

### Benefits
1. **Never lose data** - Even "bad" records are preserved for investigation
2. **Debugging** - Can trace any downstream record back to its source
3. **Reprocessing** - Can re-run transformations without re-loading from source
4. **Audit trail** - Know exactly when and where data came from
5. **Deduplication** - Row hashes enable identifying duplicate records

### Trade-offs
- Uses more storage (TEXT types are less efficient)
- No data validation at load time
- Queries are slower (no indexes, no type optimization)

## Schema Design

```sql
CREATE TABLE bronze_listeners (
    -- Source fields (all TEXT)
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

Note: Even numeric fields like `duration_ms` are stored as TEXT. This prevents load failures if the source contains invalid values.

## Files in This Layer

| File | Description |
|------|-------------|
| `01_create_tables.sql` | DDL to create all bronze tables |
| `02_load_data.py` | Python script to load JSON/CSV into SQLite |
| `bronze.db` | SQLite database (generated) |

## Loading Process

The `02_load_data.py` script:

1. Creates/recreates the bronze tables (idempotent)
2. Loads each source file with audit columns:
   - `listeners.json` → `bronze_listeners`
   - `artists.json` → `bronze_artists`
   - `tracks.json` → `bronze_tracks`
   - `streams.csv` → `bronze_streams`
3. Computes row hashes for deduplication tracking

## Running This Layer

```bash
# Ensure virtual environment is activated
cd 02_bronze
python 02_load_data.py
```

## Data Loaded

| Table | Records | Source Format |
|-------|---------|---------------|
| bronze_listeners | 50 | JSON |
| bronze_artists | 100 | JSON |
| bronze_tracks | 1,000 | JSON |
| bronze_streams | 100,999 | CSV |

## Verification Queries

After loading, verify the data:

```sql
-- Check row counts
SELECT 'bronze_listeners' AS table_name, COUNT(*) AS row_count FROM bronze_listeners
UNION ALL
SELECT 'bronze_artists', COUNT(*) FROM bronze_artists
UNION ALL
SELECT 'bronze_tracks', COUNT(*) FROM bronze_tracks
UNION ALL
SELECT 'bronze_streams', COUNT(*) FROM bronze_streams;

-- Verify audit columns are populated
SELECT _source_file, _loaded_at, COUNT(*) AS records
FROM bronze_streams
GROUP BY _source_file, _loaded_at;

-- Find duplicate records using row hash
SELECT _row_hash, COUNT(*) AS occurrences
FROM bronze_streams
GROUP BY _row_hash
HAVING COUNT(*) > 1
LIMIT 10;
-- Expected: ~999 duplicate pairs (1% of 100k)
```

## Key Concepts Demonstrated

1. **Staging tables** - Intermediate storage before transformation
2. **Schema-on-read** - Store as TEXT, interpret types later
3. **Data lineage** - Track where every record came from
4. **Row hashing** - Enable deduplication without losing duplicates
5. **Idempotent loads** - Can safely re-run the load process

## Next Steps

After loading bronze data, proceed to **03_silver/** to clean and normalize.
