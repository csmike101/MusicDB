# MusicDB

A hands-on tutorial demonstrating **medallion architecture** through a music streaming use case. Build a complete data pipeline from raw event data to analytics-ready "Year in Review" insights.

## Quick Start

```bash
# Clone and setup
git clone https://github.com/csmike101/MusicDB.git
cd MusicDB
python -m venv venv

# Activate virtual environment
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Option 1: Use sample data (instant)
# Copy databases from sample_data/ to layer directories

# Option 2: Generate fresh data
python scripts/run_all.py

# Explore the data
sqlite3 04_gold/gold.db "SELECT * FROM dim_artist LIMIT 5;"
```

## What You'll Learn

| Concept | Layer | Example |
|---------|-------|---------|
| **Data Staging** | Bronze | Audit columns, preserving raw data |
| **Data Cleaning** | Silver | Deduplication, type casting, normalization |
| **Dimensional Modeling** | Gold | Star schema, fact/dimension tables |
| **Analytics** | Serving | Window functions, aggregations, JSON export |

## The Domain: Music Streaming

We're modeling a simplified streaming service (like Spotify):

| Entity | Count | Description |
|--------|-------|-------------|
| Listeners | ~50 | User profiles with demographics |
| Artists | ~100 | Musicians and bands |
| Tracks | ~1,000 | Songs with metadata |
| Streams | ~100,000 | Listening events over 1 year (2025) |

### Sample Analytics (Year in Review)

The serving layer enables queries like:
- Top 5 artists for each listener
- Total minutes listened per month
- Most popular genres by time of day
- Listening streaks and discovery metrics

## Architecture

```
Raw → Bronze → Silver → Gold → Serving
 │       │        │       │       │
JSON   TEXT    3NF     Star    Views
CSV    Audit   Types   Schema  JSON
       Cols    FKs     Facts   Export
```

| Layer | Directory | Database |
|-------|-----------|----------|
| Raw | `01_raw/` | JSON/CSV files |
| Bronze | `02_bronze/` | `bronze.db` |
| Silver | `03_silver/` | `silver.db` |
| Gold | `04_gold/` | `gold.db` |
| Serving | `05_serving/` | Views in `gold.db` |

## Data Quality Challenges

The raw data intentionally includes real-world issues for learning:

| Issue | Rate | What You'll Learn |
|-------|------|-------------------|
| Duplicate records | ~1% | Deduplication strategies |
| Null values | ~15-20% | Handling missing data |
| Inconsistent casing | ~10% | Data standardization |
| Invalid foreign keys | ~0.5% | Referential integrity |

## Project Structure

```
MusicDB/
├── README.md              # This file
├── CLAUDE.md              # Claude Code context
├── requirements.txt       # Python dependencies
│
├── docs/
│   ├── WALKTHROUGH.md     # Narrative tutorial
│   └── plans/v1.0/        # Implementation plans
│
├── sample_data/           # Pre-generated databases
│
├── 01_raw/                # Data generation scripts
├── 02_bronze/             # Staging layer
├── 03_silver/             # Cleaned & normalized
├── 04_gold/               # Dimensional model
├── 05_serving/            # Analytics views
└── scripts/               # Pipeline utilities
```

## Prerequisites

- Python 3.8+
- Basic SQL knowledge (SELECT, JOIN, GROUP BY)
- SQLite (included with Python)

## Documentation

- **[Tutorial Walkthrough](docs/WALKTHROUGH.md)** - Story-driven guide through the architecture
- **Layer READMEs** - Each layer directory has detailed documentation
- **[Implementation Plans](docs/plans/v1.0/)** - Technical design documents

## Pipeline Commands

```bash
# Run everything
python scripts/run_all.py

# Run specific layers
python scripts/run_all.py --start silver --end gold

# Validate data integrity
python scripts/validate.py

# Reset and start fresh
python scripts/reset.py --force
```

## License

This workbook is provided for educational purposes.
