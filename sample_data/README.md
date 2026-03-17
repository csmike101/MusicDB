# Sample Data

This directory contains pre-generated SQLite databases for testing and exploration without running the full pipeline.

## Included Databases

| File | Size | Description |
|------|------|-------------|
| `bronze.db` | ~19 MB | Staged raw data with audit columns |
| `silver.db` | ~32 MB | Cleaned and normalized (3NF) |
| `gold.db` | ~22 MB | Star schema with serving views |

## Data Characteristics

- **Listeners:** ~50 users
- **Artists:** ~100 musicians/bands
- **Tracks:** ~1,000 songs
- **Streams:** ~100,000 events
- **Time Period:** Full year 2025
- **Seed:** Randomly generated (not reproducible)

## Usage

### Option 1: Copy to Layer Directories

```bash
# From repository root
cp sample_data/bronze.db 02_bronze/
cp sample_data/silver.db 03_silver/
cp sample_data/gold.db 04_gold/
```

### Option 2: Query Directly

```bash
sqlite3 sample_data/gold.db "SELECT * FROM dim_artist LIMIT 10;"
```

## Generate Fresh Data

To create a new dataset with different random values:

```bash
python scripts/reset.py --force
python scripts/run_all.py
```

The generated databases will appear in each layer's directory (not here in sample_data/).

## Notes

- These databases were generated with a specific Faker seed and may differ from freshly generated data
- The sample data includes intentional quality issues that are cleaned through the pipeline
- Use these for learning and testing; generate fresh data for your own experiments
