# Layer 4: Gold (Dimensional Model)

## Overview

The **Gold Layer** transforms normalized silver data into a **dimensional model** (star schema) optimized for analytics. This is where we trade storage efficiency for query performance.

## Key Principles

### 1. Star Schema Design
- **Fact table** at the center with measures (numbers we aggregate)
- **Dimension tables** around it with descriptive attributes
- **Surrogate keys** (integers) for efficient joins

### 2. Pre-computed Derived Columns
- `age_group`: Calculated from birth_date
- `popularity_tier`: Calculated from monthly_listeners
- `duration_bucket`: Calculated from duration_ms
- `is_full_play`: Calculated from duration_played_pct

### 3. Pre-aggregated Tables
Common query patterns pre-computed for instant results:
- Daily listener activity
- Daily track performance
- Monthly genre trends

## Star Schema

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

## Files in This Layer

| File | Description |
|------|-------------|
| `01_create_dimensions.sql` | Dimension table DDL |
| `02_create_facts.sql` | Fact table DDL |
| `03_create_aggregates.sql` | Aggregate table DDL |
| `04_load_dimensions.sql` | Populate dimensions from silver |
| `05_load_facts.sql` | Populate fact table with surrogate keys |
| `06_load_aggregates.sql` | Build aggregate tables |
| `gold.db` | SQLite database (generated) |

## Dimension Tables

### dim_date (365 rows)
Calendar dimension for time-based analysis.

| Column | Description |
|--------|-------------|
| date_key | YYYYMMDD integer (e.g., 20250115) |
| full_date | DATE value |
| year, quarter, month, week_of_year | Time hierarchy |
| day_of_week, day_name | Day analysis |
| is_weekend, is_holiday | Flags |

### dim_listener (50 rows)
User dimension with derived attributes.

| Column | Description |
|--------|-------------|
| listener_key | Surrogate key (auto-increment) |
| listener_id | Natural key from source |
| full_name | Derived: first_name + last_name |
| age_group | Derived: 'Under 18', '18-24', '25-34', etc. |
| tenure_months | Derived: months since signup |

### dim_artist (100 rows)
Artist dimension with popularity tiers.

| Column | Description |
|--------|-------------|
| artist_key | Surrogate key |
| years_active | Derived: 2025 - formed_year |
| popularity_tier | Derived: 'emerging', 'established', 'star', 'superstar' |

### dim_track (1,000 rows)
Track dimension with duration buckets.

| Column | Description |
|--------|-------------|
| track_key | Surrogate key |
| artist_key | FK to dim_artist |
| duration_bucket | Derived: 'short' (<3min), 'medium' (3-5min), 'long' (>5min) |
| release_year | Derived from release_date |

### dim_device (5 rows)
Small/static device dimension.

| device_type | device_category |
|-------------|-----------------|
| mobile | mobile |
| tablet | mobile |
| desktop | desktop |
| web | desktop |
| smart_speaker | other |

## Fact Table

### fact_streams (99,493 rows)
Grain: One row per stream event.

| Column | Type | Description |
|--------|------|-------------|
| stream_key | INTEGER | Surrogate PK |
| date_key | INTEGER | FK to dim_date |
| listener_key | INTEGER | FK to dim_listener |
| track_key | INTEGER | FK to dim_track |
| device_key | INTEGER | FK to dim_device |
| stream_id | TEXT | Degenerate dimension |
| streamed_at | DATETIME | Exact timestamp |
| duration_played_ms | INTEGER | Measure: play duration |
| duration_played_pct | REAL | Derived: % of track played |
| shuffle_mode | INTEGER | Measure: 0 or 1 |
| offline_mode | INTEGER | Measure: 0 or 1 |
| is_full_play | INTEGER | Derived: 1 if >= 90% played |

## Aggregate Tables

### agg_daily_listener_streams (18,108 rows)
Pre-computed listener activity by day.

```sql
SELECT date_key, listener_key,
       stream_count, total_duration_ms, unique_tracks, unique_artists,
       shuffle_streams, offline_streams, full_plays
```

### agg_daily_track_streams (87,143 rows)
Pre-computed track performance by day.

```sql
SELECT date_key, track_key,
       stream_count, unique_listeners, total_duration_ms, full_plays
```

### agg_monthly_genre_streams (216 rows)
Pre-computed genre trends by month.

```sql
SELECT year, month, genre,
       stream_count, unique_listeners, unique_tracks, total_duration_ms
```

## Running This Layer

```bash
cd 04_gold
python -c "
import sqlite3
conn = sqlite3.connect('gold.db')
for i in range(1, 7):
    with open(f'0{i}_*.sql'.replace('*', ['create_dimensions', 'create_facts', 'create_aggregates', 'load_dimensions', 'load_facts', 'load_aggregates'][i-1])) as f:
        conn.executescript(f.read())
conn.close()
"
```

Or execute each file in order:
```bash
sqlite3 gold.db < 01_create_dimensions.sql
# ... etc
```

## Verification Queries

```sql
-- Row counts
SELECT 'dim_date', COUNT(*) FROM dim_date
UNION ALL SELECT 'dim_listener', COUNT(*) FROM dim_listener
UNION ALL SELECT 'dim_artist', COUNT(*) FROM dim_artist
UNION ALL SELECT 'dim_track', COUNT(*) FROM dim_track
UNION ALL SELECT 'dim_device', COUNT(*) FROM dim_device
UNION ALL SELECT 'fact_streams', COUNT(*) FROM fact_streams;

-- FK integrity (all should return 0)
SELECT COUNT(*) FROM fact_streams f
WHERE NOT EXISTS (SELECT 1 FROM dim_listener d WHERE d.listener_key = f.listener_key);

-- Aggregate reconciliation (should match fact count)
SELECT SUM(stream_count) FROM agg_daily_listener_streams;
SELECT COUNT(*) FROM fact_streams;
```

## Real-World Analogies

**Star Schema = A Well-Organized Report**

Imagine you're building a report about sales:
- The **fact table** is like your list of transactions (who bought what, when, for how much)
- The **dimension tables** are like reference sheets (customer details, product catalog, calendar)

Instead of repeating "John Smith, 123 Main St, Premium Member" on every transaction, you just reference "customer #42" and look up details when needed.

**Surrogate Keys = Library Card Numbers**

Your library doesn't use your name as your ID—they give you a card number. Why?
- Names change (marriage, legal changes)
- Names aren't unique
- Numbers are faster to look up

Same principle: `listener_key` (integer) is faster and more stable than `listener_id` (UUID string).

**Pre-aggregation = Pre-cooked Meals**

You *could* make dinner from scratch every night (query fact_streams directly). But if you always want the same thing (daily summaries), it's faster to meal-prep on Sunday (build aggregate tables).

## Common Questions

**Q: Why use surrogate keys instead of natural keys?**

A: Performance and stability. Integer joins are faster than string joins. And if a listener_id ever needed to change (rare but possible), the surrogate key stays stable.

**Q: Why pre-aggregate? Can't the database handle it?**

A: It can, but at scale (billions of rows), computing `SUM(duration_ms) GROUP BY date, listener` takes seconds or minutes. Pre-computing takes milliseconds. Trade-off: storage space vs query time.

**Q: What's a "degenerate dimension"?**

A: A dimension value stored directly in the fact table rather than in its own dimension table. `stream_id` is unique per row—there's no point making a dimension table for it. But we keep it for drill-through to the original record.

## Exploration Exercises

```sql
-- 1. Most popular genre by month
SELECT month_name, genre, stream_count
FROM agg_monthly_genre_streams a
JOIN dim_date d ON a.year = d.year AND a.month = d.month
WHERE (a.year, a.month, a.stream_count) IN (
    SELECT year, month, MAX(stream_count)
    FROM agg_monthly_genre_streams
    GROUP BY year, month
)
ORDER BY a.year, a.month;

-- 2. Top 10 listeners by total listening time
SELECT dl.full_name, SUM(f.duration_played_ms) / 60000.0 as total_minutes
FROM fact_streams f
JOIN dim_listener dl ON f.listener_key = dl.listener_key
GROUP BY f.listener_key
ORDER BY total_minutes DESC
LIMIT 10;

-- 3. Distribution of plays by age group
SELECT dl.age_group, COUNT(*) as streams,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM fact_streams), 1) as pct
FROM fact_streams f
JOIN dim_listener dl ON f.listener_key = dl.listener_key
GROUP BY dl.age_group
ORDER BY streams DESC;

-- 4. Weekend vs weekday listening
SELECT
    CASE WHEN dd.is_weekend = 1 THEN 'Weekend' ELSE 'Weekday' END as day_type,
    COUNT(*) as streams,
    ROUND(AVG(f.duration_played_pct), 1) as avg_completion
FROM fact_streams f
JOIN dim_date dd ON f.date_key = dd.date_key
GROUP BY dd.is_weekend;
```

## Key Concepts Demonstrated

1. **Star schema** - Fact table surrounded by dimensions
2. **Surrogate keys** - Integer keys for performance
3. **Derived attributes** - Pre-calculated for convenience
4. **Date dimension** - Every analytics system needs one
5. **Pre-aggregation** - Trading storage for query speed
6. **Slowly Changing Dimensions** - Not implemented here, but mentioned in design

## Next Steps

After gold layer is ready, proceed to **05_serving/** to create analytics views and Year-in-Review queries.
