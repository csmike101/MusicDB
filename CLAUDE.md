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
| **Raw** | `01_raw/` | Generated source data | JSON, CSV formats; intentional data quality issues |
| **Bronze** | `02_bronze/` | Staging | All TEXT columns, audit columns (_source_file, _loaded_at, _row_hash), no constraints |
| **Silver** | `03_silver/` | Cleaned & normalized | 3NF, proper types, constraints, deduplication, FK validation |
| **Gold** | `04_gold/` | Dimensional model | Star schema, facts, dimensions, surrogate keys, aggregates |
| **Serving** | `05_serving/` | Analytics-ready | Semantic views, Year-in-Review queries, JSON exports |

## Project Structure

```
data_modeling/
├── CLAUDE.md              # This file - project context for Claude Code
├── README.md              # Workbook introduction and learning objectives
├── PLAN.md                # Master implementation plan
├── requirements.txt       # Python dependencies
│
├── plans/                 # Detailed phase documentation
│   ├── 00_foundation.md
│   ├── 01_raw_layer.md
│   ├── 02_bronze_layer.md
│   ├── 03_silver_layer.md
│   ├── 04_gold_layer.md
│   ├── 05_serving_layer.md
│   └── 06_integration.md
│
├── 01_raw/                # Raw data generation
├── 02_bronze/             # Staging (bronze.db)
├── 03_silver/             # Cleaned & normalized (silver.db)
├── 04_gold/               # Dimensional model (gold.db)
├── 05_serving/            # Analytics layer (serving.db)
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

### Python Virtual Environment (Required)

**Always activate the venv before running any Python scripts.**

```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

The venv must be active when:
- Running data generation scripts
- Executing pipeline scripts
- Installing dependencies

### Other Tools
- **Git** - Version control; generated files (.db, data/) are gitignored
- **SQLite** - Included with Python standard library

## Dependencies

- Python 3.8+
- faker (for data generation)
- sqlite3 (standard library)

Install via: `pip install -r requirements.txt`

## Implementation Process

### Phase-by-Phase Workflow

This project is implemented one phase at a time. **Each phase must be reviewed and approved before proceeding to the next.**

| Phase | Plan File | Description |
|-------|-----------|-------------|
| 0 | `plans/00_foundation.md` | Project setup |
| 1 | `plans/01_raw_layer.md` | Data generation |
| 2 | `plans/02_bronze_layer.md` | Staging tables |
| 3 | `plans/03_silver_layer.md` | Cleaned & normalized |
| 4 | `plans/04_gold_layer.md` | Dimensional model |
| 5 | `plans/05_serving_layer.md` | Analytics views |
| 6 | `plans/06_integration.md` | Pipeline scripts |

### For Each Phase

1. **Read** the phase plan file for detailed requirements
2. **Implement** all tasks listed in the plan
3. **Run verification** queries/checks specified in the plan
4. **Pause and await user review** before proceeding to the next phase

### Verification Requirements

Each phase includes verification steps. Do not mark a phase complete until:
- All tasks are implemented
- All verification queries pass
- User has reviewed and approved

### Keeping Documentation in Sync

When a plan file is updated (schema changes, new fields, etc.), also update:

1. **Layer README** - Each layer directory has a `README.md` explaining its data:
   - `01_raw/README.md` - Entity schemas, file formats, quality issues
   - `02_bronze/README.md` - Bronze table schemas, audit columns
   - `03_silver/README.md` - Cleaned schemas, transformation logic
   - `04_gold/README.md` - Dimensional model, star schema
   - `05_serving/README.md` - Views, analytics queries

2. **Downstream plans** - If schema changes affect later phases, update those plan files

3. **CLAUDE.md** - Update this file if architecture or conventions change

4. **PLAN.md** - Update status and summaries as phases complete
