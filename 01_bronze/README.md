# Layer 1: Bronze (Raw Staging)

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
| `_loaded_at` | Timestamp when the record was loaded |
| `_source_file` | Name of the source file |
| `_row_number` | Row position in the source file |

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
    age TEXT,
    country TEXT,
    city TEXT,
    signup_date TEXT,
    subscription_tier TEXT,
    -- Audit columns
    _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    _source_file TEXT,
    _row_number INTEGER
);
```

Note: Even numeric fields like `age` are stored as TEXT. This prevents load failures if the source contains invalid values like "twenty-five" or empty strings.

## Files in This Layer

| File | Description |
|------|-------------|
| `01_create_bronze_tables.sql` | DDL to create all bronze tables |
| `02_load_bronze_data.py` | Python script to load JSON/CSV into SQLite |
| `bronze.db` | SQLite database (generated) |

## Loading Process

The `02_load_bronze_data.py` script:

1. Creates the SQLite database
2. Executes the table creation DDL
3. Loads each source file:
   - `listeners.json` → `bronze_listeners`
   - `artists.csv` → `bronze_artists`
   - `tracks.csv` → `bronze_tracks`
   - `streams.csv` → `bronze_streams`
4. Adds audit columns during load

## Running This Layer

```bash
# Ensure virtual environment is activated
cd 01_bronze
python 02_load_bronze_data.py
```

## Verification Queries

After loading, verify the data:

```sql
-- Check row counts match source files
SELECT 'bronze_listeners' AS table_name, COUNT(*) AS row_count FROM bronze_listeners
UNION ALL
SELECT 'bronze_artists', COUNT(*) FROM bronze_artists
UNION ALL
SELECT 'bronze_tracks', COUNT(*) FROM bronze_tracks
UNION ALL
SELECT 'bronze_streams', COUNT(*) FROM bronze_streams;

-- Verify audit columns are populated
SELECT _source_file, MIN(_row_number), MAX(_row_number), COUNT(*)
FROM bronze_streams
GROUP BY _source_file;

-- Spot check for data quality issues (these should exist!)
SELECT stream_id, COUNT(*)
FROM bronze_streams
GROUP BY stream_id
HAVING COUNT(*) > 1
LIMIT 5;  -- Should find duplicates
```

## Key Concepts Demonstrated

1. **Staging tables** - Intermediate storage before transformation
2. **Schema-on-read** - Store as TEXT, interpret types later
3. **Data lineage** - Track where every record came from
4. **Idempotent loads** - Can safely re-run the load process

## Next Steps

After loading bronze data, proceed to **02_silver/** to clean and normalize.
