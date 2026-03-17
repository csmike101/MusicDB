# Layer 5: Serving (Analytics Layer)

## Overview

The **Serving Layer** provides analytics-ready views and queries on top of the gold layer. This is where we create semantic abstractions that hide the complexity of the star schema and deliver business-friendly interfaces for end users and applications.

## Key Principles

### 1. Semantic Abstraction
- Views provide business-friendly names (`listener_name` not `full_name`)
- Hide surrogate keys, expose natural identifiers
- Pre-calculate common metrics (minutes, hours, percentages)

### 2. Query Simplification
- Flatten star schema joins into single views
- End users query one view instead of joining 5 tables
- Complex window functions wrapped in easy-to-query views

### 3. Performance via Materialization
- Views can be materialized (cached) in production systems
- Pre-aggregated metrics avoid repeated computation
- Indexes on gold layer support efficient view queries

## Architecture Note

The serving layer views are created **directly in gold.db** because SQLite views cannot reference attached databases. In production data warehouses (Snowflake, BigQuery, etc.), you would create these in a separate schema or database.

```
gold.db
├── Tables (from Phase 4)
│   ├── dim_date, dim_listener, dim_artist, dim_track, dim_device
│   ├── fact_streams
│   └── agg_* tables
│
└── Views (from Phase 5)  <-- Serving layer
    ├── v_stream_details
    ├── v_listener_summary
    ├── v_track_popularity
    ├── v_year_in_review_summary
    └── ... (15 views total)
```

## Files in This Layer

| File | Description |
|------|-------------|
| `01_create_views.sql` | Semantic views for general analytics |
| `02_year_in_review.sql` | Year-in-Review (Wrapped) specific views |
| `03_export_reports.py` | Export reports to JSON/CSV |
| `reports/` | Generated report files (gitignored) |

## Views Created

### General Analytics Views (01_create_views.sql)

| View | Rows | Purpose |
|------|------|---------|
| `v_stream_details` | 99,493 | Fully denormalized stream data |
| `v_listener_summary` | 50 | Per-listener aggregate stats |
| `v_track_popularity` | 1,000 | Track rankings with engagement |
| `v_artist_popularity` | 100 | Artist rankings with catalog stats |
| `v_genre_trends` | 216 | Genre performance by month |
| `v_daily_platform_stats` | 365 | Platform-wide daily metrics |

### Year-in-Review Views (02_year_in_review.sql)

| View | Rows | Purpose |
|------|------|---------|
| `v_top_artists_by_listener` | 250 | Top 5 artists per listener |
| `v_top_tracks_by_listener` | 250 | Top 5 tracks per listener |
| `v_top_genre_by_listener` | 50 | Dominant genre per listener |
| `v_listening_personality` | 50 | Behavioral classification |
| `v_monthly_trends_by_listener` | 600 | Monthly listening patterns |
| `v_peak_listening_times` | 150 | Time-of-day preferences |
| `v_weekday_vs_weekend` | 50 | Weekday vs weekend habits |
| `v_discovery_stats` | 50 | New artist/track discovery |
| `v_year_in_review_summary` | 50 | Complete summary per listener |

## Running This Layer

```bash
cd data_modeling

# Create views in gold.db
python -c "
import sqlite3
conn = sqlite3.connect('04_gold/gold.db')
with open('05_serving/01_create_views.sql') as f:
    conn.executescript(f.read())
with open('05_serving/02_year_in_review.sql') as f:
    conn.executescript(f.read())
conn.close()
"

# Export Year-in-Review reports
cd 05_serving
python 03_export_reports.py --limit 5 --csv
```

## Export Script Usage

```bash
# Export all listeners
python 03_export_reports.py

# Export first 10 listeners only
python 03_export_reports.py --limit 10

# Also generate summary CSV
python 03_export_reports.py --csv

# Custom database path
python 03_export_reports.py --db /path/to/gold.db --output /path/to/reports
```

## Sample Queries

### Find Top Listeners by Total Hours
```sql
SELECT
    listener_name,
    total_hours,
    unique_artists,
    listening_percentile
FROM v_year_in_review_summary
ORDER BY total_hours DESC
LIMIT 10;
```

### Genre Trends Over the Year
```sql
SELECT
    month_name,
    genre,
    stream_count,
    month_share_pct
FROM v_genre_trends
WHERE genre IN ('Rock', 'Pop', 'Hip-Hop')
ORDER BY month, stream_count DESC;
```

### Find "Explorer" Personality Listeners
```sql
SELECT
    listener_name,
    unique_artists,
    unique_genres,
    total_streams
FROM v_listening_personality
WHERE listening_personality = 'Explorer';
```

### Track Discovery by Quarter
```sql
SELECT
    listener_name,
    q1_new_artists,
    q2_new_artists,
    q3_new_artists,
    q4_new_artists
FROM v_discovery_stats
ORDER BY total_artists_played DESC;
```

## Year-in-Review Report Structure

Each exported JSON report contains:

```json
{
  "listener_id": "abc123...",
  "listener_name": "John Smith",
  "year": 2025,
  "generated_at": "2025-12-31T12:00:00",
  "summary": {
    "total_streams": 2500,
    "total_hours": 150.5,
    "unique_artists": 85,
    "listening_percentile": 92
  },
  "top_artists": [...],
  "top_tracks": [...],
  "top_genre": {...},
  "listening_personality": {...},
  "monthly_trends": [...],
  "peak_listening_times": [...],
  "weekday_vs_weekend": {...}
}
```

## Listening Personalities

The `v_listening_personality` view classifies listeners based on their behavior:

| Personality | Criteria |
|-------------|----------|
| **Explorer** | Listened to 80+ unique artists |
| **Genre Loyalist** | Stuck to 3 or fewer genres |
| **The Shuffler** | >70% of streams in shuffle mode |
| **Deep Listener** | >85% full play completion rate |
| **Offline Adventurer** | >50% offline listening |
| **Power User** | >2,500 total streams |
| **Casual Listener** | Default category |

## Real-World Analogies

**Semantic Views = A Friendly Receptionist**

Imagine calling a large company. You don't want to navigate their internal phone directory (star schema). You want a receptionist (semantic view) who understands your request and connects you to the right people.

```sql
-- Without serving layer (navigate the schema yourself)
SELECT l.first_name || ' ' || l.last_name, COUNT(*)
FROM fact_streams f
JOIN dim_listener l ON f.listener_key = l.listener_key
JOIN dim_track t ON f.track_key = t.track_key
JOIN dim_artist a ON t.artist_key = a.artist_key
WHERE a.name = 'Taylor Swift'
GROUP BY l.listener_key;

-- With serving layer (just ask)
SELECT listener_name, COUNT(*)
FROM v_stream_details
WHERE artist_name = 'Taylor Swift'
GROUP BY listener_id;
```

**Year-in-Review = Annual Report Card**

Like a school report card summarizes a year of learning, Year-in-Review summarizes a year of listening. Instead of showing every test grade (stream), it shows overall performance (total hours), strengths (top genres), and growth (discovery stats).

## Common Questions

**Q: Why create views instead of just running the queries?**

A: Views provide:
1. **Consistency** - Everyone uses the same calculations
2. **Simplicity** - Users don't need to know the schema
3. **Performance** - Can be materialized/cached
4. **Security** - Can grant access to views without exposing raw tables

**Q: Can views be slow?**

A: In SQLite, views are computed on-demand. For large datasets, consider:
- Materialized views (supported in PostgreSQL, not SQLite)
- Creating summary tables (like our `agg_*` tables)
- Caching results in your application

**Q: How would this differ in a production system?**

A: In production (Snowflake, BigQuery, Databricks):
- Views would be in a separate `serving` schema
- Materialized views would cache expensive computations
- Access controls would limit who sees what
- Real-time views might use streaming data

## Exploration Exercises

1. **Find your "twin listener"** - Who has similar taste?
   ```sql
   -- Hint: Compare top genres and artists between listeners
   ```

2. **Seasonal analysis** - Do listening habits change by season?
   ```sql
   -- Hint: Use v_monthly_trends_by_listener and compare Q1 vs Q3
   ```

3. **Weekend warrior identification** - Who listens more on weekends?
   ```sql
   -- Hint: Use v_weekday_vs_weekend
   ```

4. **Create a "mood" classification** - Based on genre preferences
   ```sql
   -- Hint: Map genres to moods (Rock=Energetic, Classical=Relaxed, etc.)
   ```

## Key Concepts Demonstrated

1. **Semantic layer** - Business-friendly abstraction over technical schema
2. **View composition** - Building complex analytics from simpler views
3. **Window functions** - RANK(), ROW_NUMBER(), PERCENT_RANK() for rankings
4. **Behavioral classification** - Using CASE statements for user segmentation
5. **Data export** - Generating consumable outputs (JSON, CSV)

## Next Steps

The serving layer completes the medallion architecture pipeline:
- **Raw** → Source data with quality issues
- **Bronze** → Preserved as-is with audit metadata
- **Silver** → Cleaned, validated, normalized
- **Gold** → Dimensional model optimized for analytics
- **Serving** → Business-friendly views and reports

Proceed to **Phase 6 (Integration)** to create end-to-end pipeline orchestration.
