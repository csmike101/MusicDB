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

### Option 1: Use Helper Script (Recommended)

```bash
# From repository root
python scripts/use_sample_data.py
```

### Option 2: Copy Manually

```bash
# From repository root (Unix/macOS)
cp sample_data/bronze.db 02_bronze/
cp sample_data/silver.db 03_silver/
cp sample_data/gold.db 04_gold/

# Windows (PowerShell)
Copy-Item sample_data\bronze.db 02_bronze\
Copy-Item sample_data\silver.db 03_silver\
Copy-Item sample_data\gold.db 04_gold\
```

### Option 3: Query Directly

```bash
# Using sqlite3 CLI (if installed)
sqlite3 sample_data/gold.db "SELECT * FROM dim_artist LIMIT 10;"

# Using Python (works everywhere)
python -c "import sqlite3; c=sqlite3.connect('sample_data/gold.db'); print([r for r in c.execute('SELECT * FROM dim_artist LIMIT 10')])"
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
