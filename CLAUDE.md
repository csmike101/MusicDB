# Music Streaming Data Modeling Workbook

## Project Overview

This is a tutorial-style workbook demonstrating **medallion architecture** (Raw → Bronze → Silver → Gold → Serving) using a music streaming domain in SQLite.

## Goals

1. Teach data modeling concepts through hands-on examples
2. Demonstrate progressive data refinement across layers
3. Show practical SQL patterns for each layer of the medallion architecture
4. Create a "Year in Review" analytics use case (like Spotify Wrapped)

## Data Scale

- ~50 listeners
- ~100 artists
- ~1000 tracks
- ~100k stream events
- 1 year of data (2025)

## Architecture Layers

| Layer | Directory | Purpose | Key Concepts |
|-------|-----------|---------|--------------|
| **Raw** | `00_raw/` | Generated source data | JSON, CSV formats; intentional data quality issues |
| **Bronze** | `01_bronze/` | Staging | All TEXT columns, audit columns (_source_file, _loaded_at, _row_hash), no constraints |
| **Silver** | `02_silver/` | Cleaned & normalized | 3NF, proper types, constraints, deduplication, FK validation |
| **Gold** | `03_gold/` | Dimensional model | Star schema, facts, dimensions, surrogate keys, aggregates |
| **Serving** | `04_serving/` | Analytics-ready | Semantic views, Year-in-Review queries, JSON exports |

## Project Structure

```
data_modeling/
├── CLAUDE.md              # This file - project context for Claude Code
├── README.md              # Workbook introduction and learning objectives
├── PLAN.md                # Master implementation plan
├── requirements.txt       # Python dependencies
│
├── plans/                 # Detailed phase documentation
│   ├── 01_foundation.md
│   ├── 02_raw_layer.md
│   ├── 03_bronze_layer.md
│   ├── 04_silver_layer.md
│   ├── 05_gold_layer.md
│   ├── 06_serving_layer.md
│   └── 07_integration.md
│
├── 00_raw/                # Layer 0: Raw data generation
├── 01_bronze/             # Layer 1: Staging (bronze.db)
├── 02_silver/             # Layer 2: Cleaned & normalized (silver.db)
├── 03_gold/               # Layer 3: Dimensional model (gold.db)
├── 04_serving/            # Layer 4: Analytics layer (serving.db)
└── scripts/               # Pipeline utilities (run_all.py, validate.py)
```

## Coding Conventions

### SQL Style
- Use UPPERCASE for SQL keywords (SELECT, FROM, WHERE, etc.)
- Use lowercase for table and column names with underscores
- Prefix bronze tables with `bronze_`
- Prefix dimension tables with `dim_`
- Prefix fact tables with `fact_`
- Prefix aggregate tables with `agg_`
- Prefix views with `v_`

### Python Style
- Follow PEP 8
- Use type hints where practical
- Use descriptive variable names
- Include docstrings for functions

### File Naming
- SQL files numbered for execution order: `01_`, `02_`, etc.
- Use descriptive names: `create_`, `load_`, `transform_`

## Key Design Decisions

1. **SQLite for simplicity** - No server setup required, portable databases
2. **Separate .db files per layer** - Clear separation, easy to inspect
3. **Intentional data quality issues** - Teaching deduplication, cleaning, validation
4. **Year 2025 data** - Recent, realistic timeframe
5. **Music streaming domain** - Familiar, relatable, good for analytics examples

## Intentional Data Quality Issues (Raw Layer)

For teaching purposes, the generated data includes:

| Issue | Rate | Fields Affected |
|-------|------|-----------------|
| Duplicate records | ~1% | streams |
| Null values | ~15-20% | city, album, formed_year |
| Inconsistent casing | ~10% | genre |
| Invalid foreign keys | ~0.5% | track_id in streams |
| Whitespace issues | ~2% | name fields |
| Date format variations | ~2% | release_date |

## Testing & Verification

After each layer transformation, verify:
- Row counts (expected increases/decreases)
- No constraint violations
- Foreign key integrity
- Aggregate reconciliation between layers

## Development Environment

- **Git** - Version control; generated files (.db, data/) are gitignored
- **Python virtual environment** - `venv/` directory, activate before running scripts
- On Windows: `venv\Scripts\activate`
- On macOS/Linux: `source venv/bin/activate`

## Dependencies

- Python 3.8+
- faker (for data generation)
- sqlite3 (standard library)

Install via: `pip install -r requirements.txt`
