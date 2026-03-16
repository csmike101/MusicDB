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
cd 00_raw
python generate_data.py
```

### 4. Follow the Layers

Work through each layer in order:

| Layer | Folder | Focus |
|-------|--------|-------|
| Raw | `00_raw/` | Data generation, understanding source formats |
| Bronze | `01_bronze/` | Staging, audit columns, preserving raw data |
| Silver | `02_silver/` | Cleaning, normalization, constraints |
| Gold | `03_gold/` | Dimensional modeling, star schema |
| Serving | `04_serving/` | Semantic views, analytics queries |

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
| Time Period | 1 year (2025) |

## Project Structure

```
data_modeling/
├── .gitignore             # Git ignore patterns
├── README.md              # This file
├── CLAUDE.md              # Project context
├── PLAN.md                # Implementation plan
├── requirements.txt       # Python dependencies
├── venv/                  # Python virtual environment (not in git)
│
├── 00_raw/                # Data generation
├── 01_bronze/             # Raw staging
├── 02_silver/             # Cleaned & normalized
├── 03_gold/               # Dimensional model
├── 04_serving/            # Analytics layer
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
