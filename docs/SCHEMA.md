# Schema Reference

Visual guide to the MusicDB data models across all layers.

---

## Layer Overview

```
Raw (Files)       Bronze (Staging)      Silver (3NF)         Gold (Star)          Serving (Views)
──────────────    ────────────────      ────────────         ───────────          ───────────────
listeners.json    bronze_listeners  →   listeners        →   dim_listener     →   v_listener_summary
artists.json      bronze_artists    →   artists          →   dim_artist       →   v_artist_popularity
tracks.json       bronze_tracks     →   tracks           →   dim_track        →   v_track_popularity
streams.csv       bronze_streams    →   streams          →   fact_streams     →   v_stream_details
                                        rejected_records     dim_date             v_year_in_review_*
                                                             dim_device
                                                             agg_* tables
```

---

## Data Flow Summary

```
100,999 raw streams
    │
    ▼ Bronze (load as-is, add audit columns)
100,999 bronze_streams
    │
    ▼ Silver (dedupe ~999, reject ~507 invalid FKs)
 99,493 streams  +  507 rejected_records
    │
    ▼ Gold (add surrogate keys, derive measures)
 99,493 fact_streams  +  5 dimensions  +  3 aggregates
    │
    ▼ Serving (denormalized views)
 15 analytics views for Year-in-Review
```

---

## Silver Layer (3NF)

### Entity Relationship Diagram

```
┌─────────────────────┐
│      listeners      │
├─────────────────────┤
│ PK  listener_id     │
│     email           │
│     username        │
│     first_name      │
│     last_name       │
│     birth_date      │
│     city            │
│     country         │
│     subscription    │
│     created_at      │
└──────────┬──────────┘
           │
           │ 1:N
           ▼
┌─────────────────────┐         ┌─────────────────────┐         ┌─────────────────────┐
│       streams       │         │       tracks        │         │       artists       │
├─────────────────────┤         ├─────────────────────┤         ├─────────────────────┤
│ PK  stream_id       │         │ PK  track_id        │         │ PK  artist_id       │
│ FK  listener_id     │────────▶│     title           │────────▶│     name            │
│ FK  track_id        │         │ FK  artist_id       │         │     genre           │
│     streamed_at     │         │     album           │         │     country         │
│     duration_ms     │         │     duration_ms     │         │     formed_year     │
│     device_type     │         │     genre           │         │     monthly_        │
│     shuffle_mode    │         │     release_date    │         │       listeners     │
│     offline_mode    │         │     explicit        │         └─────────────────────┘
└─────────────────────┘         └─────────────────────┘

┌─────────────────────────────┐
│   silver_rejected_records   │
├─────────────────────────────┤
│     source_table            │
│     source_id               │
│     rejection_reason        │
│     rejected_at             │
└─────────────────────────────┘
```

### Table Summary

| Table | Rows | Primary Key | Foreign Keys |
|-------|------|-------------|--------------|
| listeners | 50 | listener_id | - |
| artists | 100 | artist_id | - |
| tracks | 1,000 | track_id | artist_id → artists |
| streams | ~99,500 | stream_id | listener_id → listeners, track_id → tracks |
| silver_rejected_records | ~500 | - | - |

---

## Gold Layer (Star Schema)

### Star Schema Diagram

```
                                 ┌───────────────────────┐
                                 │       dim_date        │
                                 ├───────────────────────┤
                                 │ PK  date_key (YYYYMMDD)│
                                 │     full_date         │
                                 │     year, quarter     │
                                 │     month, month_name │
                                 │     week_of_year      │
                                 │     day_of_month      │
                                 │     day_of_week       │
                                 │     day_name          │
                                 │     is_weekend        │
                                 │     is_holiday        │
                                 └───────────┬───────────┘
                                             │
                                             │
┌───────────────────────┐           ┌────────┴────────┐           ┌───────────────────────┐
│     dim_listener      │           │   fact_streams  │           │      dim_track        │
├───────────────────────┤           ├─────────────────┤           ├───────────────────────┤
│ PK  listener_key      │◀──────────│ PK  stream_key  │──────────▶│ PK  track_key         │
│     listener_id       │           │ FK  date_key    │           │     track_id          │
│     email             │           │ FK  listener_key│           │     title             │
│     username          │           │ FK  track_key   │           │ FK  artist_key        │──┐
│     full_name *       │           │ FK  device_key  │           │     album             │  │
│     birth_date        │           │     stream_id   │           │     duration_ms       │  │
│     age_group *       │           │     streamed_at │           │     duration_bucket * │  │
│     city              │           │     duration_ms │           │     genre             │  │
│     country           │           │     duration_pct│           │     release_date      │  │
│     subscription_type │           │     shuffle_mode│           │     release_year *    │  │
│     created_at        │           │     offline_mode│           │     explicit          │  │
│     tenure_months *   │           │     is_full_play│           └───────────────────────┘  │
└───────────────────────┘           └────────┬────────┘                                      │
                                             │                    ┌───────────────────────┐  │
                                             │                    │      dim_artist       │  │
                                    ┌────────┴────────┐           ├───────────────────────┤  │
                                    │    dim_device   │           │ PK  artist_key        │◀─┘
                                    ├─────────────────┤           │     artist_id         │
                                    │ PK  device_key  │           │     name              │
                                    │     device_type │           │     genre             │
                                    │     device_cat *│           │     country           │
                                    └─────────────────┘           │     formed_year       │
                                                                  │     years_active *    │
                                                                  │     monthly_listeners │
* = derived column                                                │     popularity_tier * │
                                                                  └───────────────────────┘
```

### Dimension Tables

| Dimension | Rows | Surrogate Key | Natural Key | Derived Attributes |
|-----------|------|---------------|-------------|-------------------|
| dim_date | 365 | date_key (YYYYMMDD) | full_date | is_weekend, is_holiday |
| dim_listener | 50 | listener_key | listener_id | full_name, age_group, tenure_months |
| dim_artist | 100 | artist_key | artist_id | years_active, popularity_tier |
| dim_track | 1,000 | track_key | track_id | duration_bucket, release_year |
| dim_device | 5 | device_key | device_type | device_category |

### Fact Table

| Fact | Rows | Grain | Measures |
|------|------|-------|----------|
| fact_streams | ~99,500 | One row per stream event | duration_played_ms, duration_played_pct, shuffle_mode, offline_mode, is_full_play |

### Aggregate Tables

| Aggregate | Rows | Grain | Pre-computed Measures |
|-----------|------|-------|----------------------|
| agg_daily_listener_streams | ~18K | listener + date | stream_count, total_duration, unique_tracks/artists, full_plays |
| agg_daily_track_streams | ~200K | track + date | stream_count, unique_listeners, total_duration, full_plays |
| agg_monthly_genre_streams | ~144 | genre + month | stream_count, unique_listeners/tracks, total_duration |

---

## Derived Column Definitions

### Age Groups (dim_listener.age_group)

```sql
CASE
    WHEN age < 18 THEN 'Under 18'
    WHEN age BETWEEN 18 AND 24 THEN '18-24'
    WHEN age BETWEEN 25 AND 34 THEN '25-34'
    WHEN age BETWEEN 35 AND 44 THEN '35-44'
    WHEN age BETWEEN 45 AND 54 THEN '45-54'
    ELSE '55+'
END
```

### Popularity Tiers (dim_artist.popularity_tier)

```sql
CASE
    WHEN monthly_listeners < 10000 THEN 'emerging'
    WHEN monthly_listeners < 100000 THEN 'established'
    WHEN monthly_listeners < 1000000 THEN 'star'
    ELSE 'superstar'
END
```

### Duration Buckets (dim_track.duration_bucket)

```sql
CASE
    WHEN duration_ms < 180000 THEN 'short'    -- < 3 min
    WHEN duration_ms <= 300000 THEN 'medium'  -- 3-5 min
    ELSE 'long'                               -- > 5 min
END
```

### Full Play Flag (fact_streams.is_full_play)

```sql
CASE WHEN duration_played_pct >= 90 THEN 1 ELSE 0 END
```

---

## Serving Layer Views

```
gold.db Views
│
├── General Analytics
│   ├── v_stream_details      (~99,500 rows)  Fully denormalized stream fact
│   ├── v_listener_summary    (50 rows)       Listener-level aggregates
│   ├── v_track_popularity    (1,000 rows)    Track rankings with window functions
│   ├── v_artist_popularity   (100 rows)      Artist rankings
│   └── v_daily_platform_stats (365 rows)     Platform-wide daily metrics
│
└── Year in Review
    ├── v_top_artists_by_listener  (250 rows)  Top 5 artists per listener
    ├── v_top_tracks_by_listener   (250 rows)  Top 5 tracks per listener
    ├── v_top_genre_by_listener    (50 rows)   Dominant genre per listener
    ├── v_listening_personality    (50 rows)   Behavioral classification
    ├── v_monthly_listening_trends (600 rows)  12 months × 50 listeners
    ├── v_peak_listening_times     (200 rows)  4 time slots × 50 listeners
    ├── v_weekday_weekend_patterns (100 rows)  2 categories × 50 listeners
    └── v_year_in_review_summary   (50 rows)   Complete wrapped data per listener
```

---

## Quick Reference

### Row Count Progression

| Layer | listeners | artists | tracks | streams | notes |
|-------|-----------|---------|--------|---------|-------|
| Raw | 50 | 100 | 1,000 | ~101,000 | Includes quality issues |
| Bronze | 50 | 100 | 1,000 | ~101,000 | 1:1 with raw |
| Silver | 50 | 100 | 1,000 | ~99,500 | -1,500 (dupes + invalid FKs) |
| Gold | 50 | 100 | 1,000 | ~99,500 | + surrogate keys + derived cols |

### Database Files

| Database | Location | Size | Contents |
|----------|----------|------|----------|
| bronze.db | `02_bronze/` | ~19 MB | 4 staging tables |
| silver.db | `03_silver/` | ~32 MB | 4 normalized tables + rejected |
| gold.db | `04_gold/` | ~22 MB | 5 dims + 1 fact + 3 aggs + 15 views |
