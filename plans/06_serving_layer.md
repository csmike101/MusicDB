# Phase 6: Serving Layer

**Status:** Pending

---

## Goal

Create analytics-ready views and queries for the "Year in Review" (Spotify Wrapped-style) use case. This layer provides semantic abstractions over the gold layer for end-user consumption.

---

## Files to Create

| File | Purpose |
|------|---------|
| `04_serving/01_create_views.sql` | Semantic views for analytics |
| `04_serving/02_year_in_review.sql` | Year-in-Review queries |
| `04_serving/03_export_reports.py` | Export results to JSON/CSV |
| `04_serving/serving.db` | SQLite database (generated, attaches gold.db) |

---

## Semantic Views

### v_stream_details
```sql
-- Denormalized stream view for ad-hoc analysis
CREATE VIEW v_stream_details AS
SELECT
    f.stream_id,
    f.streamed_at,
    -- Listener info
    l.listener_id,
    l.full_name AS listener_name,
    l.age_group,
    l.country AS listener_country,
    l.subscription_type,
    -- Track info
    t.track_id,
    t.title AS track_title,
    t.album,
    t.duration_ms AS track_duration_ms,
    t.genre,
    t.release_year,
    t.explicit,
    -- Artist info
    a.artist_id,
    a.name AS artist_name,
    a.popularity_tier,
    -- Device info
    dv.device_type,
    dv.device_category,
    -- Date info
    d.full_date,
    d.year,
    d.month,
    d.month_name,
    d.day_name,
    d.is_weekend,
    -- Measures
    f.duration_played_ms,
    f.duration_played_pct,
    f.is_full_play,
    f.shuffle_mode,
    f.offline_mode
FROM fact_streams f
JOIN dim_listener l ON f.listener_key = l.listener_key
JOIN dim_track t ON f.track_key = t.track_key
JOIN dim_artist a ON t.artist_key = a.artist_key
JOIN dim_device dv ON f.device_key = dv.device_key
JOIN dim_date d ON f.date_key = d.date_key;
```

### v_listener_summary
```sql
-- Listener-level summary stats
CREATE VIEW v_listener_summary AS
SELECT
    l.listener_id,
    l.full_name,
    l.subscription_type,
    l.country,
    COUNT(*) AS total_streams,
    COUNT(DISTINCT t.track_id) AS unique_tracks,
    COUNT(DISTINCT a.artist_id) AS unique_artists,
    COUNT(DISTINCT t.genre) AS unique_genres,
    SUM(f.duration_played_ms) / 1000.0 / 60.0 AS total_minutes,
    SUM(f.duration_played_ms) / 1000.0 / 60.0 / 60.0 AS total_hours,
    AVG(f.duration_played_pct) AS avg_completion_pct,
    SUM(f.is_full_play) AS full_plays,
    SUM(f.shuffle_mode) AS shuffle_streams,
    SUM(f.offline_mode) AS offline_streams
FROM fact_streams f
JOIN dim_listener l ON f.listener_key = l.listener_key
JOIN dim_track t ON f.track_key = t.track_key
JOIN dim_artist a ON t.artist_key = a.artist_key
GROUP BY l.listener_key;
```

### v_track_popularity
```sql
-- Track popularity ranking
CREATE VIEW v_track_popularity AS
SELECT
    t.track_id,
    t.title,
    a.name AS artist_name,
    t.genre,
    COUNT(*) AS stream_count,
    COUNT(DISTINCT f.listener_key) AS unique_listeners,
    SUM(f.duration_played_ms) / 1000.0 / 60.0 AS total_minutes,
    AVG(f.duration_played_pct) AS avg_completion_pct,
    RANK() OVER (ORDER BY COUNT(*) DESC) AS popularity_rank
FROM fact_streams f
JOIN dim_track t ON f.track_key = t.track_key
JOIN dim_artist a ON t.artist_key = a.artist_key
GROUP BY t.track_key;
```

---

## Year in Review Queries

### Top 5 Artists per Listener
```sql
-- Each listener's most-played artists
WITH ranked_artists AS (
    SELECT
        l.listener_id,
        l.full_name,
        a.name AS artist_name,
        COUNT(*) AS stream_count,
        SUM(f.duration_played_ms) / 60000.0 AS minutes_listened,
        ROW_NUMBER() OVER (
            PARTITION BY l.listener_key
            ORDER BY COUNT(*) DESC
        ) AS artist_rank
    FROM fact_streams f
    JOIN dim_listener l ON f.listener_key = l.listener_key
    JOIN dim_track t ON f.track_key = t.track_key
    JOIN dim_artist a ON t.artist_key = a.artist_key
    GROUP BY l.listener_key, a.artist_key
)
SELECT *
FROM ranked_artists
WHERE artist_rank <= 5
ORDER BY listener_id, artist_rank;
```

### Top 5 Tracks per Listener
```sql
-- Each listener's most-played tracks
WITH ranked_tracks AS (
    SELECT
        l.listener_id,
        l.full_name,
        t.title AS track_title,
        a.name AS artist_name,
        COUNT(*) AS play_count,
        ROW_NUMBER() OVER (
            PARTITION BY l.listener_key
            ORDER BY COUNT(*) DESC
        ) AS track_rank
    FROM fact_streams f
    JOIN dim_listener l ON f.listener_key = l.listener_key
    JOIN dim_track t ON f.track_key = t.track_key
    JOIN dim_artist a ON t.artist_key = a.artist_key
    GROUP BY l.listener_key, t.track_key
)
SELECT *
FROM ranked_tracks
WHERE track_rank <= 5
ORDER BY listener_id, track_rank;
```

### Top Genre per Listener
```sql
-- Each listener's dominant genre
WITH genre_stats AS (
    SELECT
        l.listener_id,
        l.full_name,
        t.genre,
        COUNT(*) AS stream_count,
        SUM(f.duration_played_ms) / 60000.0 AS minutes_listened,
        ROW_NUMBER() OVER (
            PARTITION BY l.listener_key
            ORDER BY SUM(f.duration_played_ms) DESC
        ) AS genre_rank
    FROM fact_streams f
    JOIN dim_listener l ON f.listener_key = l.listener_key
    JOIN dim_track t ON f.track_key = t.track_key
    GROUP BY l.listener_key, t.genre
)
SELECT
    listener_id,
    full_name,
    genre AS top_genre,
    stream_count,
    ROUND(minutes_listened, 1) AS minutes_in_genre
FROM genre_stats
WHERE genre_rank = 1;
```

### Listening Personality
```sql
-- Classify listeners by behavior
SELECT
    l.listener_id,
    l.full_name,
    CASE
        WHEN SUM(f.shuffle_mode) * 1.0 / COUNT(*) > 0.7 THEN 'Shuffler'
        WHEN COUNT(DISTINCT t.genre) <= 3 THEN 'Genre Purist'
        WHEN COUNT(DISTINCT a.artist_key) > 50 THEN 'Explorer'
        WHEN SUM(f.is_full_play) * 1.0 / COUNT(*) > 0.8 THEN 'Deep Listener'
        ELSE 'Casual Listener'
    END AS listening_personality,
    COUNT(*) AS total_streams,
    COUNT(DISTINCT a.artist_key) AS unique_artists,
    COUNT(DISTINCT t.genre) AS unique_genres,
    ROUND(SUM(f.shuffle_mode) * 100.0 / COUNT(*), 1) AS shuffle_pct,
    ROUND(SUM(f.is_full_play) * 100.0 / COUNT(*), 1) AS completion_pct
FROM fact_streams f
JOIN dim_listener l ON f.listener_key = l.listener_key
JOIN dim_track t ON f.track_key = t.track_key
JOIN dim_artist a ON t.artist_key = a.artist_key
GROUP BY l.listener_key;
```

### Monthly Listening Trends
```sql
-- Listening patterns by month
SELECT
    l.listener_id,
    d.month,
    d.month_name,
    COUNT(*) AS streams,
    SUM(f.duration_played_ms) / 60000.0 AS minutes,
    COUNT(DISTINCT t.track_key) AS unique_tracks
FROM fact_streams f
JOIN dim_listener l ON f.listener_key = l.listener_key
JOIN dim_track t ON f.track_key = t.track_key
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY l.listener_key, d.month
ORDER BY l.listener_id, d.month;
```

### Peak Listening Times
```sql
-- When do listeners stream most?
SELECT
    l.listener_id,
    CASE
        WHEN CAST(strftime('%H', f.streamed_at) AS INTEGER) BETWEEN 6 AND 11 THEN 'Morning'
        WHEN CAST(strftime('%H', f.streamed_at) AS INTEGER) BETWEEN 12 AND 17 THEN 'Afternoon'
        WHEN CAST(strftime('%H', f.streamed_at) AS INTEGER) BETWEEN 18 AND 21 THEN 'Evening'
        ELSE 'Night'
    END AS time_of_day,
    COUNT(*) AS stream_count
FROM fact_streams f
JOIN dim_listener l ON f.listener_key = l.listener_key
GROUP BY l.listener_key, time_of_day
ORDER BY l.listener_id, stream_count DESC;
```

---

## Export Script Design

```python
# 04_serving/03_export_reports.py

import sqlite3
import json
import csv
from pathlib import Path

def export_year_in_review(db_path: str, output_dir: str):
    """Generate Year-in-Review JSON for each listener."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    listeners = conn.execute("SELECT DISTINCT listener_id FROM dim_listener").fetchall()

    for listener in listeners:
        listener_id = listener['listener_id']
        report = {
            'listener_id': listener_id,
            'year': 2025,
            'summary': get_listener_summary(conn, listener_id),
            'top_artists': get_top_artists(conn, listener_id, limit=5),
            'top_tracks': get_top_tracks(conn, listener_id, limit=5),
            'top_genre': get_top_genre(conn, listener_id),
            'personality': get_listening_personality(conn, listener_id),
            'monthly_trends': get_monthly_trends(conn, listener_id)
        }

        output_path = Path(output_dir) / f"{listener_id}_wrapped.json"
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

    conn.close()

if __name__ == "__main__":
    export_year_in_review("04_serving/serving.db", "04_serving/reports")
```

---

## Tasks

- [ ] Create `04_serving/01_create_views.sql`
- [ ] Create `04_serving/02_year_in_review.sql`
- [ ] Create `04_serving/03_export_reports.py`
- [ ] Create semantic views
- [ ] Test Year-in-Review queries
- [ ] Export sample reports for a few listeners
- [ ] Verify query performance

---

## Verification

```sql
-- View row counts
SELECT 'v_stream_details' AS view_name, COUNT(*) FROM v_stream_details
UNION ALL SELECT 'v_listener_summary', COUNT(*) FROM v_listener_summary
UNION ALL SELECT 'v_track_popularity', COUNT(*) FROM v_track_popularity;

-- Year-in-Review completeness
SELECT COUNT(DISTINCT listener_id) AS listeners_with_data
FROM v_listener_summary
WHERE total_streams > 0;
-- Should equal total listeners

-- Sample Year-in-Review output
SELECT * FROM v_listener_summary LIMIT 5;
```

### Sample Output Files
```
04_serving/
├── reports/
│   ├── listener_001_wrapped.json
│   ├── listener_002_wrapped.json
│   └── ...
```
