# MusicDB

A tutorial workbook demonstrating **medallion architecture** (Raw → Bronze → Silver → Gold → Serving) using a music streaming domain in SQLite.

## Architecture

| Layer | Directory | Purpose |
|-------|-----------|---------|
| **Raw** | `01_raw/` | Generated source data (JSON, CSV) with intentional quality issues |
| **Bronze** | `02_bronze/` | Staging with TEXT columns, audit columns, no constraints |
| **Silver** | `03_silver/` | Cleaned & normalized (3NF, proper types, constraints) |
| **Gold** | `04_gold/` | Dimensional model (star schema, facts, dimensions) |
| **Serving** | `05_serving/` | Analytics views and Year-in-Review queries |

## Data Scale

~50 listeners, ~100 artists, ~1,000 tracks, ~100k streams, 1 year (2025)

## Coding Conventions

### SQL
- Keywords: `UPPERCASE` (SELECT, FROM, WHERE)
- Names: `lowercase_with_underscores`
- Prefixes: `bronze_`, `dim_`, `fact_`, `agg_`, `v_` (views)

### Python
- PEP 8, type hints, docstrings

### Files
- Numbered for execution order: `01_create_tables.sql`, `02_load_data.py`

## Quick Commands

```bash
# Setup (Windows)
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt

# Setup (macOS/Linux)
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run full pipeline
python scripts/run_all.py

# Validate data integrity
python scripts/validate.py

# Reset everything
python scripts/reset.py --force
```

## Project Structure

```
MusicDB/
├── CLAUDE.md              # This file
├── README.md              # User-facing documentation
├── requirements.txt       # Python dependencies
│
├── docs/                  # Documentation
│   ├── WALKTHROUGH.md     # Tutorial narrative
│   └── plans/v1.0/        # v1.0 implementation plans
│
├── sample_data/           # Pre-generated databases for testing
│
├── 01_raw/                # Data generation
├── 02_bronze/             # Staging layer
├── 03_silver/             # Cleaned & normalized
├── 04_gold/               # Dimensional model
├── 05_serving/            # Analytics layer
└── scripts/               # Pipeline utilities
```

---

## Development Process

This section documents the phased development approach used to build this project. Follow this pattern when creating new versions or extending functionality.

### Phased Implementation

Each major version is developed in phases, with each phase documented in a plan file:

1. **Create a version directory:** `docs/plans/v{X.Y}/`
2. **Write phase plans:** One markdown file per phase (e.g., `01_raw_layer.md`)
3. **Include a master plan:** `PLAN.md` in the version directory tracks overall status
4. **Implement sequentially:** Complete and verify each phase before proceeding
5. **Archive on completion:** Plans remain as historical documentation

### Plan File Structure

Each phase plan should include:
- **Objectives** - What this phase accomplishes
- **Tasks** - Specific implementation steps
- **Schema/Code** - Technical specifications
- **Verification** - How to confirm the phase is complete

### Version Numbering

- **Major (v2.0)** - Breaking changes, new architecture
- **Minor (v1.1)** - New features, backward compatible
- **Patch** - Bug fixes only (no plan needed)

### Current Plans

| Version | Status | Location |
|---------|--------|----------|
| v1.0 | Complete | `docs/plans/v1.0/` |
