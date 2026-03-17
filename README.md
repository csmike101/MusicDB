# Music Streaming Data Modeling Workbook

A hands-on tutorial demonstrating **medallion architecture** through a music streaming use case. Build a complete data pipeline from raw event data to analytics-ready "Year in Review" insights.

## Learning Objectives

By completing this workbook, you will understand:

### Data Architecture
- **Medallion Architecture** - Progressive data refinement through Raw → Bronze → Silver → Gold → Serving layers
- **Layer Responsibilities** - When and why to transform data at each stage
- **Data Quality Management** - Handling messy real-world data systematically

### Data Modeling Concepts
- **Third Normal Form (3NF)** - Eliminating redundancy in operational data
- **Star Schema** - Designing dimensional models for analytics
- **Fact vs Dimension Tables** - Understanding measures and descriptive attributes
- **Surrogate Keys** - Why and how to use synthetic identifiers

### SQL Skills
- **DDL** - Creating tables with constraints, indexes, and relationships
- **DML** - Loading, transforming, and aggregating data
- **Views** - Building semantic layers for business users
- **Window Functions** - Advanced analytics queries

### Practical Patterns
- **Audit Columns** - Tracking data lineage
- **Deduplication** - Identifying and removing duplicate records
- **Type Casting** - Converting string data to proper types
- **Aggregation Tables** - Pre-computing metrics for performance

## Prerequisites

- Basic SQL knowledge (SELECT, JOIN, GROUP BY)
- Python 3.8+ installed
- SQLite (included with Python)
- A text editor or IDE

## Getting Started

### 1. Clone and Set Up Virtual Environment

```bash
# Clone the repository (if applicable)
git clone <repository-url>
cd data_modeling

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Generate Sample Data

```bash
cd 01_raw
python generate_data.py
```

### 4. Follow the Layers

Work through each layer in order:

| Layer | Folder | Focus |
|-------|--------|-------|
| Raw | `01_raw/` | Data generation, understanding source formats |
| Bronze | `02_bronze/` | Staging, audit columns, preserving raw data |
| Silver | `03_silver/` | Cleaning, normalization, constraints |
| Gold | `04_gold/` | Dimensional modeling, star schema |
| Serving | `05_serving/` | Semantic views, analytics queries |

Each folder contains:
- `README.md` - Concepts and explanations
- SQL/Python files - Numbered for execution order

### 5. Run the Complete Pipeline

```bash
python scripts/run_all.py
```

## The Domain: Music Streaming

We're modeling a simplified music streaming service similar to Spotify. The data includes:

- **Listeners** - User profiles with demographics
- **Artists** - Musicians and bands
- **Tracks** - Songs with metadata
- **Streams** - Listening events (who played what, when)

### Sample Analytics (Year in Review)

The final serving layer enables queries like:
- Top 5 artists for each listener
- Total minutes listened per month
- Most popular genres by time of day
- Listening streaks (consecutive days)
- Discovery metrics (new artists explored)

## Data Scale

| Entity | Count |
|--------|-------|
| Listeners | ~50 |
| Artists | ~100 |
| Tracks | ~1,000 |
| Streams | ~100,000 |
| Time Period | Full year 2025 |

## Data Quality Challenges

The raw data intentionally includes real-world quality issues for learning:

| Issue | Rate | What You'll Learn |
|-------|------|-------------------|
| Duplicate records | ~1% | Deduplication strategies |
| Null values | ~15-20% | Handling missing data |
| Inconsistent casing | ~10% | Data standardization |
| Invalid foreign keys | ~0.5% | Referential integrity |
| Whitespace issues | ~2% | String cleaning |
| Date format variations | ~2% | Date parsing |

## Project Structure

```
data_modeling/
├── .gitignore             # Git ignore patterns
├── README.md              # This file
├── CLAUDE.md              # Project context for Claude Code
├── PLAN.md                # Master implementation plan
├── requirements.txt       # Python dependencies
├── venv/                  # Python virtual environment (not in git)
│
├── plans/                 # Detailed phase documentation
│   ├── 00_foundation.md   # Project setup
│   ├── 01_raw_layer.md    # Data generation design
│   ├── 02_bronze_layer.md # Staging layer design
│   ├── 03_silver_layer.md # Normalization design
│   ├── 04_gold_layer.md   # Star schema design
│   ├── 05_serving_layer.md # Analytics queries
│   └── 06_integration.md  # Pipeline orchestration
│
├── 01_raw/                # Data generation
├── 02_bronze/             # Raw staging (bronze.db)
├── 03_silver/             # Cleaned & normalized (silver.db)
├── 04_gold/               # Dimensional model (gold.db)
├── 05_serving/            # Analytics layer (serving.db)
└── scripts/               # Pipeline utilities
```

## Key Takeaways

After completing this workbook, you'll be able to:

1. **Design** a multi-layer data architecture
2. **Implement** data quality checks and transformations
3. **Model** data for both operational and analytical workloads
4. **Write** SQL for complex analytics queries
5. **Explain** tradeoffs between different modeling approaches

## License

This workbook is provided for educational purposes.
