# Phase 1: Setup + Home Page

## Dependencies

### Infrastructure Dependencies
- None (this phase creates the foundation)

### Data Dependencies
| Database | Tables/Views | Notes |
|----------|--------------|-------|
| `02_bronze/bronze.db` | `bronze_streams`, `bronze_listeners`, `bronze_artists`, `bronze_tracks` | Row counts only |
| `03_silver/silver.db` | `streams` | Row count only |
| `04_gold/gold.db` | `fact_streams`, `sqlite_master` | Row count + view count |

**Verification before starting:** Run `python scripts/validate.py` to confirm all databases exist and contain expected data.

### Page Dependencies
- None (this is the first phase)

---

## Objectives

1. Create `06_streamlit/` directory structure
2. Set up dependencies and configuration
3. Implement database connection utilities with error handling
4. Build the Home page (pipeline health dashboard)
5. Produce a functional, launchable app

---

## Tasks

### 1.1 Directory Structure

Create:
```
06_streamlit/
├── README.md
├── app.py
├── pages/
│   └── 1_Home.py
├── components/
│   ├── __init__.py
│   └── database.py
└── .streamlit/
    └── config.toml
```

### 1.2 Dependencies

Update `requirements.txt`:
```
faker==40.11.0
streamlit>=1.36.0
plotly>=5.18.0
pandas>=2.0.0
```

### 1.3 Streamlit Configuration

`.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#6B4EAA"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F5F5F5"
textColor = "#262626"

[server]
headless = true
```

### 1.4 Database Utilities

`components/database.py`:

```python
"""Database connection utilities for MusicDB Streamlit app."""

import sqlite3
from pathlib import Path
from typing import Optional
import pandas as pd
import streamlit as st

# Database paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATHS = {
    "bronze": PROJECT_ROOT / "02_bronze" / "bronze.db",
    "silver": PROJECT_ROOT / "03_silver" / "silver.db",
    "gold": PROJECT_ROOT / "04_gold" / "gold.db",
}


def get_db_path(layer: str) -> Path:
    """Get the path to a layer's database file."""
    return DB_PATHS.get(layer)


def db_exists(layer: str) -> bool:
    """Check if a database file exists."""
    path = get_db_path(layer)
    return path is not None and path.exists()


def get_db_size_mb(layer: str) -> Optional[float]:
    """Get database file size in MB."""
    path = get_db_path(layer)
    if path and path.exists():
        return path.stat().st_size / (1024 * 1024)
    return None


def get_connection(layer: str) -> Optional[sqlite3.Connection]:
    """Get a database connection for the specified layer."""
    path = get_db_path(layer)
    if path and path.exists():
        return sqlite3.connect(path)
    return None


def query_df(layer: str, sql: str) -> Optional[pd.DataFrame]:
    """Execute a query and return results as a DataFrame."""
    conn = get_connection(layer)
    if conn:
        try:
            return pd.read_sql_query(sql, conn)
        finally:
            conn.close()
    return None


def check_all_databases() -> dict:
    """Check status of all databases."""
    status = {}
    for layer in DB_PATHS:
        status[layer] = {
            "exists": db_exists(layer),
            "size_mb": get_db_size_mb(layer),
            "path": str(get_db_path(layer)),
        }
    return status


def show_missing_db_warning():
    """Display a warning when databases are missing."""
    st.warning(
        "**Databases not found.** Run the pipeline first:\n\n"
        "```bash\n"
        "python scripts/run_all.py\n"
        "```\n\n"
        "Or use sample data:\n\n"
        "```bash\n"
        "python scripts/use_sample_data.py\n"
        "```"
    )
```

### 1.5 App Entry Point

`app.py`:

```python
"""MusicDB Streamlit App - Entry Point."""

import streamlit as st

st.set_page_config(
    page_title="MusicDB Dashboard",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Import pages
from pages import Home

# Navigation
pg = st.navigation([
    st.Page("pages/1_Home.py", title="Home", icon="🏠"),
    # Future pages will be added here as they're implemented
])

pg.run()
```

### 1.6 Home Page

`pages/1_Home.py`:

**Purpose**: Pipeline health dashboard and entry point.

**Narrative Connection**: "Your Mission" from WALKTHROUGH.md—transforms messy data into insights.

**Layout**:
```
┌─────────────────────────────────────────────────────────────────┐
│  MusicDB Pipeline Dashboard                                     │
├─────────────────────────────────────────────────────────────────┤
│  [Raw Files]  →  [Bronze]  →  [Silver]  →  [Gold]  →  [Serving] │
│    JSON/CSV       100,999     99,493      99,493      15 views  │
├─────────────────────────────────────────────────────────────────┤
│  Pipeline Health                    │  Data Flow Sankey         │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │                            │
│  │ Raw │ │Brnz │ │Slvr │ │Gold │   │  [Sankey diagram showing   │
│  │ ✓   │ │ ✓   │ │ ✓   │ │ ✓   │   │   record flow with losses] │
│  └─────┘ └─────┘ └─────┘ └─────┘   │                            │
├─────────────────────────────────────┴───────────────────────────┤
│  Database Sizes                     │  Record Counts            │
│  [Bar chart: bronze.db, silver.db,  │  [Table: layer → count]   │
│   gold.db sizes in MB]              │                           │
└─────────────────────────────────────────────────────────────────┘
```

**Components**:

| Component | Type | Source | Business Question |
|-----------|------|--------|-------------------|
| Layer status indicators | st.metric | Check .db file existence | Is the pipeline healthy? |
| Record flow Sankey | Plotly Sankey | Row counts from each layer | How much data flows through? |
| Database sizes | Plotly bar | File system stats | How much storage used? |
| Record counts table | st.dataframe | COUNT(*) per table | What's in each layer? |

**Key Queries**:

```sql
-- Bronze record counts
SELECT 'bronze_listeners' as table_name, COUNT(*) as rows FROM bronze_listeners
UNION ALL SELECT 'bronze_artists', COUNT(*) FROM bronze_artists
UNION ALL SELECT 'bronze_tracks', COUNT(*) FROM bronze_tracks
UNION ALL SELECT 'bronze_streams', COUNT(*) FROM bronze_streams;

-- Silver record counts
SELECT 'listeners' as table_name, COUNT(*) as rows FROM listeners
UNION ALL SELECT 'artists', COUNT(*) FROM artists
UNION ALL SELECT 'tracks', COUNT(*) FROM tracks
UNION ALL SELECT 'streams', COUNT(*) FROM streams;

-- Gold record counts
SELECT 'fact_streams' as table_name, COUNT(*) as rows FROM fact_streams
UNION ALL SELECT 'dim_listener', COUNT(*) FROM dim_listener
UNION ALL SELECT 'dim_artist', COUNT(*) FROM dim_artist
UNION ALL SELECT 'dim_track', COUNT(*) FROM dim_track
UNION ALL SELECT 'dim_date', COUNT(*) FROM dim_date
UNION ALL SELECT 'dim_device', COUNT(*) FROM dim_device;

-- Serving view count (gold.db)
SELECT COUNT(*) as view_count
FROM sqlite_master
WHERE type = 'view' AND name LIKE 'v_%';
```

**Sankey Data Structure**:

```python
# Nodes: Raw, Bronze, Silver, Gold, Rejected
# Links:
#   Raw → Bronze: 100,999 (all records)
#   Bronze → Silver: 99,493 (cleaned)
#   Bronze → Rejected: 1,506 (duplicates + invalid FKs)
#   Silver → Gold: 99,493 (all clean records)
```

---

## File Structure (Phase 1 Output)

```
06_streamlit/
├── README.md                 # Basic readme (expanded in later phases)
├── app.py                    # Entry point
├── pages/
│   └── 1_Home.py             # Pipeline dashboard
├── components/
│   ├── __init__.py
│   └── database.py           # DB utilities
└── .streamlit/
    └── config.toml           # Theme config
```

---

## Verification Checklist

After implementation:

**Setup**
- [ ] `pip install -r requirements.txt` succeeds
- [ ] `06_streamlit/` directory structure created
- [ ] `.streamlit/config.toml` has custom theme

**App Launch**
- [ ] `streamlit run 06_streamlit/app.py` launches without errors
- [ ] Home page displays when app opens
- [ ] Sidebar navigation visible

**Home Page Functionality**
- [ ] All 4 database status indicators show correctly (✓ or ✗)
- [ ] Database size bar chart renders
- [ ] Sankey diagram shows data flow with correct counts
- [ ] Record counts table displays all layers

**Error Handling**
- [ ] Missing database warning appears if DBs don't exist
- [ ] App works with `sample_data/` databases

**Documentation**
- [ ] `06_streamlit/README.md` created and complete
- [ ] `docs/WALKTHROUGH.md` has Phase 7 section added

---

## Sample Code: Home Page Implementation

```python
"""Home page - Pipeline health dashboard."""

import streamlit as st
import plotly.graph_objects as go
from components.database import (
    check_all_databases,
    query_df,
    db_exists,
    get_db_size_mb,
    show_missing_db_warning,
)

st.title("🎵 MusicDB Pipeline Dashboard")
st.markdown("*Medallion architecture: Raw → Bronze → Silver → Gold → Serving*")

# Check database status
db_status = check_all_databases()
all_exist = all(s["exists"] for s in db_status.values())

if not all_exist:
    show_missing_db_warning()
    st.stop()

# --- Layer Status Metrics ---
st.subheader("Pipeline Health")

col1, col2, col3, col4 = st.columns(4)

with col1:
    raw_exists = (Path("01_raw/data").exists()
                  if Path("01_raw/data").exists() else False)
    st.metric("Raw", "✓ Ready" if raw_exists else "✗ Missing")

with col2:
    st.metric("Bronze", "✓ Ready" if db_status["bronze"]["exists"] else "✗ Missing")

with col3:
    st.metric("Silver", "✓ Ready" if db_status["silver"]["exists"] else "✗ Missing")

with col4:
    st.metric("Gold", "✓ Ready" if db_status["gold"]["exists"] else "✗ Missing")

# --- Data Flow Sankey ---
st.subheader("Data Flow")

# Get counts
bronze_streams = query_df("bronze", "SELECT COUNT(*) as n FROM bronze_streams")["n"][0]
silver_streams = query_df("silver", "SELECT COUNT(*) as n FROM streams")["n"][0]
rejected = bronze_streams - silver_streams

fig = go.Figure(go.Sankey(
    node=dict(
        label=["Raw Files", "Bronze", "Silver", "Gold", "Rejected"],
        color=["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"]
    ),
    link=dict(
        source=[0, 1, 1, 2],
        target=[1, 2, 4, 3],
        value=[bronze_streams, silver_streams, rejected, silver_streams]
    )
))
fig.update_layout(height=300, margin=dict(t=20, b=20))
st.plotly_chart(fig, use_container_width=True)

# --- Database Sizes ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Database Sizes")
    sizes = {k: v["size_mb"] for k, v in db_status.items()}
    fig = go.Figure(go.Bar(
        x=list(sizes.values()),
        y=list(sizes.keys()),
        orientation='h',
        text=[f"{v:.1f} MB" for v in sizes.values()],
        textposition='outside'
    ))
    fig.update_layout(height=200, margin=dict(t=20, b=20, l=20, r=80))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Record Counts")
    counts = []
    for layer, tables in [
        ("bronze", ["bronze_listeners", "bronze_artists", "bronze_tracks", "bronze_streams"]),
        ("silver", ["listeners", "artists", "tracks", "streams"]),
        ("gold", ["fact_streams", "dim_listener", "dim_artist", "dim_track", "dim_date"]),
    ]:
        for table in tables:
            df = query_df(layer, f"SELECT COUNT(*) as n FROM {table}")
            if df is not None:
                counts.append({"Layer": layer.title(), "Table": table, "Rows": df["n"][0]})

    st.dataframe(counts, hide_index=True, use_container_width=True)
```

---

## Documentation Tasks

### 1.7 Create 06_streamlit/README.md

Create initial README following the style of other layer READMEs:

```markdown
# Layer 6: Streamlit (Visualization)

## Overview

Interactive dashboard for exploring the MusicDB medallion architecture. Each page corresponds to a pipeline layer, providing visual insights into data flow, quality metrics, and analytics.

## Key Principles

### 1. One Page Per Layer
Each medallion layer has its own page with relevant visualizations.

### 2. Metrics First, Details on Demand
Pages show summary metrics at the top, with drill-down tables below.

### 3. Consistent Layout Pattern
All pages follow: Header → Metrics → Charts → Data Explorer.

## Running the App

```bash
cd 06_streamlit
streamlit run app.py
```

Or from project root:
```bash
streamlit run 06_streamlit/app.py
```

## Pages

| Page | Database | Purpose |
|------|----------|---------|
| Home | All .db files | Pipeline health dashboard |
| Bronze | bronze.db | Raw ingestion stats, audit metadata |
| Silver | silver.db | Data quality metrics, rejections |
| Gold | gold.db | Star schema explorer |
| Serving | gold.db (views) | Year-in-Review analytics |

## Files in This Layer

| File | Description |
|------|-------------|
| `app.py` | Entry point with navigation |
| `pages/*.py` | Individual page modules |
| `components/database.py` | Database connection utilities |
| `components/metrics.py` | Reusable metric helpers |
| `components/charts.py` | Chart configuration helpers |
| `.streamlit/config.toml` | Streamlit theme configuration |

## Prerequisites

- Pipeline must be run first: `python scripts/run_all.py`
- Or use sample data: `python scripts/use_sample_data.py`

## Common Questions

**Q: The app shows "Databases not found" error**

A: Run the pipeline first to generate the databases, or use sample data.

**Q: How do I add a new chart?**

A: See `components/charts.py` for examples. Use Plotly for all visualizations.

**Q: Can I customize the theme?**

A: Edit `.streamlit/config.toml` to change colors and styling.
```

### 1.8 Add Section to docs/WALKTHROUGH.md

Add Phase 7 section after Phase 6 (Integration):

```markdown
---

## Phase 7: Visualization (Streamlit App)

> **Folder:** `06_streamlit/`
> **Goal:** Interactive exploration of the entire medallion pipeline

### The Story

Your data pipeline is complete, but stakeholders don't want to write SQL. They want dashboards. The Streamlit app brings the medallion architecture to life—from raw ingestion stats to personalized Year-in-Review reports.

This is the "last mile" of your data pipeline: transforming database queries into interactive visualizations that anyone can explore.

### What You'll Learn

1. **Pipeline observability** - Monitor data flow between layers
2. **Data quality dashboards** - Visualize cleaning and rejection metrics
3. **Dimensional model exploration** - Understand star schema relationships
4. **End-user analytics** - Deliver Year-in-Review insights interactively

### The App Architecture

```
06_streamlit/
├── app.py                    # Entry point
├── pages/
│   ├── 1_Home.py             # Pipeline health
│   ├── 2_Bronze.py           # Raw staging stats
│   ├── 3_Silver.py           # Data quality
│   ├── 4_Gold.py             # Star schema
│   └── 5_Serving.py          # Year-in-Review
└── components/
    └── database.py           # Shared DB utilities
```

Each page corresponds to a medallion layer:

| Page | Database | Purpose |
|------|----------|---------|
| Home | All .db files | Pipeline health overview |
| Bronze | bronze.db | Raw ingestion stats, audit metadata |
| Silver | silver.db | Data quality metrics, rejections |
| Gold | gold.db | Star schema explorer |
| Serving | gold.db (views) | Year-in-Review analytics |

### Running the App

```bash
cd 06_streamlit
streamlit run app.py
```

The app opens in your browser at `http://localhost:8501`.

### Key Concepts Demonstrated

1. **Separation of concerns** - Each page focuses on one layer
2. **Progressive disclosure** - High-level metrics → drill-down details
3. **Connecting views to stories** - Every chart answers a business question
4. **Session state** - Listener selection persists across pages

### Explore It Yourself

```bash
# Launch the app
streamlit run 06_streamlit/app.py

# Try these interactions:
# 1. Check pipeline health on Home page
# 2. Find duplicate records on Bronze page
# 3. See rejection reasons on Silver page
# 4. Explore dimension distributions on Gold page
# 5. Generate your Year-in-Review on Serving page
```

**Question to ponder:** How would you extend this app to support real-time streaming data?

> **Deep dive:** See `06_streamlit/README.md` for component details.
```

---

## Notes

- This phase establishes the foundation that all subsequent pages will use
- The `components/database.py` module is reused by all pages
- Error handling ensures graceful degradation when DBs are missing
- Light theming is applied via `config.toml`
- Documentation (README + WALKTHROUGH section) is created as part of this phase
