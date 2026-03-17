# Phase 4: Gold Layer

**Status:** Complete

---

## Goal

Build a dimensional model (star schema) optimized for analytics. Create fact tables, dimension tables, and pre-aggregated tables for common query patterns.

---

## Files to Create

| File | Purpose |
|------|---------|
| `04_gold/01_create_dimensions.sql` | Dimension table DDL |
| `04_gold/02_create_facts.sql` | Fact table DDL |
| `04_gold/03_create_aggregates.sql` | Pre-aggregated table DDL |
| `04_gold/04_load_dimensions.sql` | Populate dimensions |
| `04_gold/05_load_facts.sql` | Populate facts |
| `04_gold/06_load_aggregates.sql` | Populate aggregates |
| `04_gold/gold.db` | SQLite database (generated) |

---

## Star Schema Design

```
                    ┌─────────────┐
                    │  dim_date   │
                    └──────┬──────┘
                           │
┌─────────────┐     ┌──────┴──────┐     ┌─────────────┐
│ dim_listener│─────│ fact_streams│─────│  dim_track  │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                           │                   │
                    ┌──────┴──────┐     ┌──────┴──────┐
                    │ dim_device  │     │ dim_artist  │
                    └─────────────┘     └─────────────┘
```

---

## Dimension Tables

### dim_date
```sql
CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,  -- YYYYMMDD format
    full_date DATE NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    week_of_year INTEGER NOT NULL,
    day_of_month INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,  -- 0=Sunday
    day_name TEXT NOT NULL,
    is_weekend INTEGER NOT NULL,   -- 0 or 1
    is_holiday INTEGER NOT NULL    -- 0 or 1 (US holidays)
);
```

### dim_listener
```sql
CREATE TABLE dim_listener (
    listener_key INTEGER PRIMARY KEY AUTOINCREMENT,
    listener_id TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL,
    username TEXT NOT NULL,
    full_name TEXT NOT NULL,  -- derived: first_name || ' ' || last_name
    birth_date DATE,
    age_group TEXT,  -- derived: '18-24', '25-34', etc.
    city TEXT,
    country TEXT NOT NULL,
    subscription_type TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    tenure_months INTEGER  -- derived: months since created_at
);
```

### dim_artist
```sql
CREATE TABLE dim_artist (
    artist_key INTEGER PRIMARY KEY AUTOINCREMENT,
    artist_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    genre TEXT NOT NULL,
    country TEXT NOT NULL,
    formed_year INTEGER,
    years_active INTEGER,  -- derived
    monthly_listeners INTEGER NOT NULL,
    popularity_tier TEXT   -- derived: 'emerging', 'established', 'star', 'superstar'
);
```

### dim_track
```sql
CREATE TABLE dim_track (
    track_key INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    artist_key INTEGER NOT NULL REFERENCES dim_artist(artist_key),
    album TEXT,
    duration_ms INTEGER NOT NULL,
    duration_bucket TEXT,  -- derived: 'short' (<3min), 'medium', 'long' (>5min)
    genre TEXT NOT NULL,
    release_date DATE NOT NULL,
    release_year INTEGER NOT NULL,
    explicit INTEGER NOT NULL
);
```

### dim_device
```sql
CREATE TABLE dim_device (
    device_key INTEGER PRIMARY KEY AUTOINCREMENT,
    device_type TEXT NOT NULL UNIQUE,
    device_category TEXT NOT NULL  -- 'mobile', 'desktop', 'other'
);
```

---

## Fact Tables

### fact_streams
```sql
CREATE TABLE fact_streams (
    stream_key INTEGER PRIMARY KEY AUTOINCREMENT,
    -- Dimension keys
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    listener_key INTEGER NOT NULL REFERENCES dim_listener(listener_key),
    track_key INTEGER NOT NULL REFERENCES dim_track(track_key),
    device_key INTEGER NOT NULL REFERENCES dim_device(device_key),
    -- Degenerate dimensions
    stream_id TEXT NOT NULL,
    streamed_at DATETIME NOT NULL,
    -- Measures
    duration_played_ms INTEGER NOT NULL,
    duration_played_pct REAL NOT NULL,  -- derived: played/total * 100
    shuffle_mode INTEGER NOT NULL,
    offline_mode INTEGER NOT NULL,
    is_full_play INTEGER NOT NULL       -- derived: played >= 90% of track
);
```

---

## Aggregate Tables

### agg_daily_listener_streams
```sql
-- Pre-aggregated: listener activity by day
CREATE TABLE agg_daily_listener_streams (
    date_key INTEGER NOT NULL,
    listener_key INTEGER NOT NULL,
    stream_count INTEGER NOT NULL,
    total_duration_ms INTEGER NOT NULL,
    unique_tracks INTEGER NOT NULL,
    unique_artists INTEGER NOT NULL,
    shuffle_streams INTEGER NOT NULL,
    offline_streams INTEGER NOT NULL,
    full_plays INTEGER NOT NULL,
    PRIMARY KEY (date_key, listener_key)
);
```

### agg_daily_track_streams
```sql
-- Pre-aggregated: track performance by day
CREATE TABLE agg_daily_track_streams (
    date_key INTEGER NOT NULL,
    track_key INTEGER NOT NULL,
    stream_count INTEGER NOT NULL,
    unique_listeners INTEGER NOT NULL,
    total_duration_ms INTEGER NOT NULL,
    full_plays INTEGER NOT NULL,
    PRIMARY KEY (date_key, track_key)
);
```

### agg_monthly_genre_streams
```sql
-- Pre-aggregated: genre trends by month
CREATE TABLE agg_monthly_genre_streams (
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    genre TEXT NOT NULL,
    stream_count INTEGER NOT NULL,
    unique_listeners INTEGER NOT NULL,
    unique_tracks INTEGER NOT NULL,
    total_duration_ms INTEGER NOT NULL,
    PRIMARY KEY (year, month, genre)
);
```

---

## Derived Column Logic

### Age Groups
```sql
CASE
    WHEN age < 18 THEN 'Under 18'
    WHEN age BETWEEN 18 AND 24 THEN '18-24'
    WHEN age BETWEEN 25 AND 34 THEN '25-34'
    WHEN age BETWEEN 35 AND 44 THEN '35-44'
    WHEN age BETWEEN 45 AND 54 THEN '45-54'
    ELSE '55+'
END AS age_group
```

### Popularity Tiers
```sql
CASE
    WHEN monthly_listeners < 10000 THEN 'emerging'
    WHEN monthly_listeners < 100000 THEN 'established'
    WHEN monthly_listeners < 1000000 THEN 'star'
    ELSE 'superstar'
END AS popularity_tier
```

### Duration Buckets
```sql
CASE
    WHEN duration_ms < 180000 THEN 'short'      -- < 3 min
    WHEN duration_ms <= 300000 THEN 'medium'    -- 3-5 min
    ELSE 'long'                                  -- > 5 min
END AS duration_bucket
```

---

## Tasks

- [x] Create `04_gold/01_create_dimensions.sql`
- [x] Create `04_gold/02_create_facts.sql`
- [x] Create `04_gold/03_create_aggregates.sql`
- [x] Create `04_gold/04_load_dimensions.sql`
- [x] Create `04_gold/05_load_facts.sql`
- [x] Create `04_gold/06_load_aggregates.sql`
- [x] Generate date dimension for 2025
- [x] Populate all dimensions from silver
- [x] Populate fact table with surrogate keys
- [x] Build aggregate tables
- [x] Verify dimensional integrity

---

## Verification

```sql
-- Dimension row counts
SELECT 'dim_date' AS table_name, COUNT(*) FROM dim_date
UNION ALL SELECT 'dim_listener', COUNT(*) FROM dim_listener
UNION ALL SELECT 'dim_artist', COUNT(*) FROM dim_artist
UNION ALL SELECT 'dim_track', COUNT(*) FROM dim_track
UNION ALL SELECT 'dim_device', COUNT(*) FROM dim_device
UNION ALL SELECT 'fact_streams', COUNT(*) FROM fact_streams;

-- Fact to dimension joins (should all match)
SELECT COUNT(*) AS orphan_listeners
FROM fact_streams f
WHERE NOT EXISTS (SELECT 1 FROM dim_listener d WHERE d.listener_key = f.listener_key);
-- Expected: 0

-- Aggregate reconciliation
SELECT SUM(stream_count) FROM agg_daily_listener_streams;
SELECT COUNT(*) FROM fact_streams;
-- These should match

-- Date dimension coverage
SELECT MIN(full_date), MAX(full_date), COUNT(*) FROM dim_date;
-- Expected: 2025-01-01, 2025-12-31, 365
```

### Expected Results
| Table | Expected Rows |
|-------|---------------|
| dim_date | 365 |
| dim_listener | ~50 |
| dim_artist | ~100 |
| dim_track | ~995 |
| dim_device | 5 |
| fact_streams | ~98.5k |
