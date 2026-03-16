# Music Streaming Data Modeling Workbook - Implementation Plan

## Overview
A tutorial-style workbook demonstrating medallion architecture (Raw → Bronze → Silver → Gold → Serving) using a music streaming domain in SQLite.

**Scale:** ~50 listeners, ~100 artists, ~1000 tracks, ~100k streams, 1 year of data

---

## Claude Project Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project context for Claude Code - coding conventions, project goals, key decisions |
| `PLAN.md` | This implementation plan - living document to track progress and iterate on design |

---

## Project Structure

```
data_modeling/
├── CLAUDE.md                     # Claude Code context file (project instructions)
├── README.md                     # Workbook introduction and learning objectives
├── requirements.txt              # Python dependencies (faker, sqlite3)
├── PLAN.md                       # This implementation plan (living document)
│
├── 00_raw/
│   ├── README.md                 # Raw layer concepts explanation
│   ├── generate_data.py          # Python data generator script
│   └── data/
│       ├── listeners.json        # Generated listener profiles
│       ├── artists.csv           # Generated artist data
│       ├── tracks.csv            # Generated track data
│       └── streams.csv           # Generated stream events
│
├── 01_bronze/
│   ├── README.md                 # Bronze layer concepts (staging, audit columns)
│   ├── 01_create_bronze_tables.sql
│   ├── 02_load_bronze_data.sql   # Or Python script for loading
│   └── bronze.db                 # SQLite database (generated)
│
├── 02_silver/
│   ├── README.md                 # Silver layer concepts (3NF, cleaning, constraints)
│   ├── 01_create_silver_tables.sql
│   ├── 02_transform_bronze_to_silver.sql
│   └── silver.db                 # SQLite database (generated)
│
├── 03_gold/
│   ├── README.md                 # Gold layer concepts (star schema, dimensions, facts)
│   ├── 01_create_dimension_tables.sql
│   ├── 02_create_fact_tables.sql
│   ├── 03_transform_silver_to_gold.sql
│   ├── 04_create_aggregations.sql
│   └── gold.db                   # SQLite database (generated)
│
├── 04_serving/
│   ├── README.md                 # Serving layer concepts (semantic views, exports)
│   ├── 01_create_semantic_views.sql
│   ├── 02_year_in_review_queries.sql  # Example analytics queries
│   └── 03_export_examples.sql    # Export-ready query patterns
│
└── scripts/
    ├── run_all.py                # Master script to run entire pipeline
    └── utils.py                  # Helper functions
```

---

## Layer Details

### Layer 0: Raw (Data Generation)

**Files to create:**
- `00_raw/generate_data.py`
- `00_raw/README.md`

**Data Generator Design:**

```python
# Entities to generate:

# 1. Listeners (JSON) - ~50 records
{
    "listener_id": "uuid",
    "email": "string",
    "username": "string",
    "age": int,
    "country": "string",
    "city": "string",
    "signup_date": "date",
    "subscription_tier": "free|premium"
}

# 2. Artists (CSV) - ~100 records
artist_id, name, genre, country, formed_year

# 3. Tracks (CSV) - ~1000 records
track_id, title, artist_id, album, duration_seconds, release_date, genre

# 4. Streams (CSV) - ~100k records
stream_id, listener_id, track_id, streamed_at, duration_listened, platform
```

**Intentional Data Quality Issues:**
- Duplicate stream records (~1%)
- Null values in optional fields (city, album)
- Inconsistent genre casing ("Rock", "rock", "ROCK")
- Invalid foreign keys (~0.5% streams reference non-existent tracks)
- Date format inconsistencies in some records
- Whitespace issues in string fields

---

### Layer 1: Bronze (Raw Staging)

**Files to create:**
- `01_bronze/01_create_bronze_tables.sql`
- `01_bronze/02_load_bronze_data.py` (Python for JSON + CSV loading)
- `01_bronze/README.md`

**Schema Design:**

```sql
-- Staging tables preserve source structure exactly
-- Add audit columns for lineage tracking

CREATE TABLE bronze_listeners (
    -- Source fields (all TEXT to preserve raw data)
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

CREATE TABLE bronze_artists (
    artist_id TEXT,
    name TEXT,
    genre TEXT,
    country TEXT,
    formed_year TEXT,
    _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    _source_file TEXT,
    _row_number INTEGER
);

CREATE TABLE bronze_tracks (
    track_id TEXT,
    title TEXT,
    artist_id TEXT,
    album TEXT,
    duration_seconds TEXT,
    release_date TEXT,
    genre TEXT,
    _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    _source_file TEXT,
    _row_number INTEGER
);

CREATE TABLE bronze_streams (
    stream_id TEXT,
    listener_id TEXT,
    track_id TEXT,
    streamed_at TEXT,
    duration_listened TEXT,
    platform TEXT,
    _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    _source_file TEXT,
    _row_number INTEGER
);
```

**Key Concepts Covered:**
- All fields as TEXT (preserve raw data fidelity)
- Audit columns (_loaded_at, _source_file, _row_number)
- No constraints (accept all data, clean later)

---

### Layer 2: Silver (Cleaned & Normalized)

**Files to create:**
- `02_silver/01_create_silver_tables.sql`
- `02_silver/02_transform_bronze_to_silver.sql`
- `02_silver/README.md`

**Schema Design (3NF):**

```sql
-- Proper data types, constraints, referential integrity

CREATE TABLE listeners (
    listener_id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL,
    age INTEGER CHECK (age >= 13 AND age <= 120),
    country TEXT NOT NULL,
    city TEXT,  -- nullable
    signup_date DATE NOT NULL,
    subscription_tier TEXT NOT NULL CHECK (subscription_tier IN ('free', 'premium'))
);

CREATE TABLE artists (
    artist_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    genre TEXT NOT NULL,  -- Standardized casing
    country TEXT,
    formed_year INTEGER CHECK (formed_year >= 1900 AND formed_year <= 2026)
);

CREATE TABLE albums (
    album_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    artist_id TEXT NOT NULL REFERENCES artists(artist_id),
    UNIQUE(title, artist_id)
);

CREATE TABLE tracks (
    track_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    artist_id TEXT NOT NULL REFERENCES artists(artist_id),
    album_id INTEGER REFERENCES albums(album_id),  -- nullable
    duration_seconds INTEGER NOT NULL CHECK (duration_seconds > 0),
    release_date DATE,
    genre TEXT NOT NULL
);

CREATE TABLE streams (
    stream_id TEXT PRIMARY KEY,
    listener_id TEXT NOT NULL REFERENCES listeners(listener_id),
    track_id TEXT NOT NULL REFERENCES tracks(track_id),
    streamed_at TIMESTAMP NOT NULL,
    duration_listened INTEGER NOT NULL CHECK (duration_listened >= 0),
    platform TEXT NOT NULL
);

-- Indexes for common queries
CREATE INDEX idx_streams_listener ON streams(listener_id);
CREATE INDEX idx_streams_track ON streams(track_id);
CREATE INDEX idx_streams_timestamp ON streams(streamed_at);
CREATE INDEX idx_tracks_artist ON tracks(artist_id);
```

**Transformation Logic:**
- Deduplicate streams (keep first occurrence)
- Standardize genre casing (title case)
- Trim whitespace from strings
- Parse dates to consistent format
- Filter out invalid foreign key references
- Extract albums into separate table (normalization)
- Cast to proper data types

**Key Concepts Covered:**
- Third Normal Form (3NF)
- Primary and foreign keys
- Check constraints
- Data type casting
- Deduplication strategies
- Index creation

---

### Layer 3: Gold (Dimensional Model)

**Files to create:**
- `03_gold/01_create_dimension_tables.sql`
- `03_gold/02_create_fact_tables.sql`
- `03_gold/03_transform_silver_to_gold.sql`
- `03_gold/04_create_aggregations.sql`
- `03_gold/README.md`

**Star Schema Design:**

```sql
-- DIMENSION TABLES

CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,  -- YYYYMMDD format
    full_date DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    week_of_year INTEGER NOT NULL,
    day_of_month INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name TEXT NOT NULL,
    is_weekend INTEGER NOT NULL  -- 0 or 1
);

CREATE TABLE dim_time (
    time_key INTEGER PRIMARY KEY,  -- HHMM format
    hour INTEGER NOT NULL,
    minute INTEGER NOT NULL,
    hour_12 INTEGER NOT NULL,
    am_pm TEXT NOT NULL,
    time_of_day TEXT NOT NULL  -- 'Morning', 'Afternoon', 'Evening', 'Night'
);

CREATE TABLE dim_listener (
    listener_key INTEGER PRIMARY KEY AUTOINCREMENT,
    listener_id TEXT NOT NULL UNIQUE,  -- Natural key
    email TEXT NOT NULL,
    username TEXT NOT NULL,
    age INTEGER,
    age_group TEXT,  -- '13-17', '18-24', '25-34', '35-44', '45-54', '55+'
    country TEXT NOT NULL,
    city TEXT,
    signup_date DATE NOT NULL,
    subscription_tier TEXT NOT NULL,
    -- SCD Type 1 (overwrite) for simplicity
    effective_date DATE NOT NULL,
    is_current INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE dim_track (
    track_key INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    artist_name TEXT NOT NULL,
    artist_country TEXT,
    album_title TEXT,
    duration_seconds INTEGER NOT NULL,
    duration_bucket TEXT,  -- 'Short (<3min)', 'Medium (3-5min)', 'Long (>5min)'
    release_date DATE,
    release_year INTEGER,
    genre TEXT NOT NULL
);

CREATE TABLE dim_platform (
    platform_key INTEGER PRIMARY KEY AUTOINCREMENT,
    platform_name TEXT NOT NULL UNIQUE,
    platform_type TEXT NOT NULL  -- 'Mobile', 'Desktop', 'Web', 'Smart Speaker'
);

-- FACT TABLE

CREATE TABLE fact_streams (
    stream_key INTEGER PRIMARY KEY AUTOINCREMENT,
    -- Dimension keys
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    time_key INTEGER NOT NULL REFERENCES dim_time(time_key),
    listener_key INTEGER NOT NULL REFERENCES dim_listener(listener_key),
    track_key INTEGER NOT NULL REFERENCES dim_track(track_key),
    platform_key INTEGER NOT NULL REFERENCES dim_platform(platform_key),
    -- Degenerate dimension
    stream_id TEXT NOT NULL,
    -- Measures
    duration_listened_seconds INTEGER NOT NULL,
    is_full_listen INTEGER NOT NULL,  -- 1 if listened >= 90% of track
    -- For additivity
    stream_count INTEGER NOT NULL DEFAULT 1
);

-- Indexes for common query patterns
CREATE INDEX idx_fact_streams_date ON fact_streams(date_key);
CREATE INDEX idx_fact_streams_listener ON fact_streams(listener_key);
CREATE INDEX idx_fact_streams_track ON fact_streams(track_key);

-- AGGREGATE TABLES

CREATE TABLE agg_daily_listener_stats (
    date_key INTEGER NOT NULL,
    listener_key INTEGER NOT NULL,
    total_streams INTEGER NOT NULL,
    total_duration_seconds INTEGER NOT NULL,
    unique_tracks INTEGER NOT NULL,
    unique_artists INTEGER NOT NULL,
    PRIMARY KEY (date_key, listener_key)
);

CREATE TABLE agg_monthly_track_stats (
    year_month TEXT NOT NULL,  -- 'YYYY-MM'
    track_key INTEGER NOT NULL,
    total_streams INTEGER NOT NULL,
    unique_listeners INTEGER NOT NULL,
    total_duration_seconds INTEGER NOT NULL,
    PRIMARY KEY (year_month, track_key)
);
```

**Key Concepts Covered:**
- Star schema design
- Fact vs dimension tables
- Surrogate keys vs natural keys
- Date and time dimensions
- Conformed dimensions
- Derived attributes (age_group, duration_bucket)
- Aggregate tables for performance
- Additive measures

---

### Layer 4: Serving (Semantic Views & Exports)

**Files to create:**
- `04_serving/01_create_semantic_views.sql`
- `04_serving/02_year_in_review_queries.sql`
- `04_serving/03_export_examples.sql`
- `04_serving/README.md`

**Semantic Views:**

```sql
-- Business-friendly views with clear naming

CREATE VIEW v_listener_profile AS
SELECT
    listener_id,
    username,
    email,
    age,
    age_group,
    country,
    city,
    subscription_tier,
    signup_date
FROM dim_listener
WHERE is_current = 1;

CREATE VIEW v_track_catalog AS
SELECT
    track_id,
    title AS track_title,
    artist_name,
    album_title,
    genre,
    duration_seconds,
    duration_bucket,
    release_year
FROM dim_track;

CREATE VIEW v_daily_listening_activity AS
SELECT
    d.full_date AS listen_date,
    l.username,
    l.country,
    l.subscription_tier,
    t.track_title,
    t.artist_name,
    t.genre,
    p.platform_name,
    f.duration_listened_seconds,
    f.is_full_listen
FROM fact_streams f
JOIN dim_date d ON f.date_key = d.date_key
JOIN dim_listener l ON f.listener_key = l.listener_key
JOIN dim_track t ON f.track_key = t.track_key
JOIN dim_platform p ON f.platform_key = p.platform_key;
```

**Year in Review Queries:**

```sql
-- Top 5 Artists for a Listener
-- Total Minutes Listened
-- Most Listened Genre
-- Listening by Time of Day
-- Listening Streak (consecutive days)
-- Top Month for Listening
-- Unique Artists Discovered
```

**Export Patterns:**
- Flattened denormalized export for BI tools
- Listener summary CSV export
- Track popularity rankings

---

## Implementation Order

> **Process:** Each phase is executed one at a time. After completing a phase, we pause for user review and feedback before proceeding to the next phase. This ensures alignment and allows for iterative refinement.

---

### Phase 1: Foundation
**Goal:** Set up project structure and Claude context files

**Tasks:**
1. [x] Create project directory structure (all folders)
2. [x] Create CLAUDE.md (project context for Claude Code)
3. [x] Copy PLAN.md into project (this living document)
4. [ ] Create requirements.txt
5. [ ] Create main README.md with learning objectives

**Verification:**
- [x] All directories exist
- [x] CLAUDE.md contains project goals and conventions
- [x] PLAN.md is in project root
- [ ] README.md outlines workbook structure

**PAUSE: Review with user before proceeding to Phase 2**

---

### Phase 2: Raw Layer
**Goal:** Create data generation pipeline with intentional quality issues

**Tasks:**
1. [ ] Write 00_raw/README.md explaining raw layer concepts
2. [ ] Implement generate_data.py with all entities
3. [ ] Run generator to create data files

**Verification:**
- [ ] listeners.json contains ~50 records
- [ ] artists.csv contains ~100 records
- [ ] tracks.csv contains ~1000 records
- [ ] streams.csv contains ~100k records
- [ ] Data quality issues are present (spot check for duplicates, nulls, casing issues)

**PAUSE: Review generated data with user before proceeding to Phase 3**

---

### Phase 3: Bronze Layer
**Goal:** Load raw files into staging tables with audit columns

**Tasks:**
1. [ ] Write 01_bronze/README.md explaining bronze concepts
2. [ ] Create 01_create_bronze_tables.sql
3. [ ] Implement 02_load_bronze_data.py
4. [ ] Execute loading and create bronze.db

**Verification:**
- [ ] All bronze tables created
- [ ] Row counts match source files exactly
- [ ] Audit columns populated (_loaded_at, _source_file, _row_number)
- [ ] All data stored as TEXT (no type coercion)

**PAUSE: Review bronze layer with user before proceeding to Phase 4**

---

### Phase 4: Silver Layer
**Goal:** Clean, normalize, and apply constraints

**Tasks:**
1. [ ] Write 02_silver/README.md explaining silver concepts (3NF, cleaning)
2. [ ] Create 01_create_silver_tables.sql with constraints
3. [ ] Create 02_transform_bronze_to_silver.sql
4. [ ] Execute transforms and create silver.db

**Verification:**
- [ ] streams count < bronze_streams count (duplicates removed)
- [ ] No constraint violations (run PRAGMA integrity_check)
- [ ] Genre values are consistently cased (SELECT DISTINCT genre)
- [ ] Foreign keys are valid (no orphan records)
- [ ] albums table populated from track data

**PAUSE: Review silver layer with user before proceeding to Phase 5**

---

### Phase 5: Gold Layer
**Goal:** Build star schema with dimensions, facts, and aggregates

**Tasks:**
1. [ ] Write 03_gold/README.md explaining dimensional modeling
2. [ ] Create 01_create_dimension_tables.sql
3. [ ] Create 02_create_fact_tables.sql
4. [ ] Create 03_transform_silver_to_gold.sql
5. [ ] Create 04_create_aggregations.sql
6. [ ] Execute all and create gold.db

**Verification:**
- [ ] dim_date covers full year range
- [ ] dim_time has 1440 rows (24 hours x 60 minutes)
- [ ] dim_listener count matches silver listeners
- [ ] dim_track count matches silver tracks
- [ ] fact_streams count matches silver streams (cleaned)
- [ ] Aggregate totals reconcile with fact detail:
  - `SUM(total_streams)` from agg table = `COUNT(*)` from fact table

**PAUSE: Review gold layer with user before proceeding to Phase 6**

---

### Phase 6: Serving Layer
**Goal:** Create semantic views and analytics queries

**Tasks:**
1. [ ] Write 04_serving/README.md explaining serving concepts
2. [ ] Create 01_create_semantic_views.sql
3. [ ] Create 02_year_in_review_queries.sql
4. [ ] Create 03_export_examples.sql

**Verification:**
- [ ] All views are queryable
- [ ] Year-in-review queries return sensible results
- [ ] Run sample queries for a specific listener (their top artist, total minutes, etc.)

**PAUSE: Review serving layer with user before proceeding to Phase 7**

---

### Phase 7: Integration
**Goal:** Create master run script and validate end-to-end

**Tasks:**
1. [ ] Create scripts/run_all.py
2. [ ] Create scripts/utils.py with helper functions
3. [ ] Run full pipeline from scratch
4. [ ] Final documentation review

**Verification:**
- [ ] `python scripts/run_all.py` completes without errors
- [ ] All .db files are created
- [ ] Sample analytics query returns expected format
- [ ] All README files are complete and accurate

**COMPLETE: Final review with user**

---

## Dependencies

```
# requirements.txt
faker>=18.0.0
```

SQLite is included with Python standard library.
