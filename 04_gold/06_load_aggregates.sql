-- Gold Layer: Load Aggregate Tables
-- Pre-computes common aggregations for performance
-- Run after 05_load_facts.sql

-- ============================================================================
-- agg_daily_listener_streams: Listener activity by day
-- ============================================================================
INSERT INTO agg_daily_listener_streams (
    date_key,
    listener_key,
    stream_count,
    total_duration_ms,
    unique_tracks,
    unique_artists,
    shuffle_streams,
    offline_streams,
    full_plays
)
SELECT
    f.date_key,
    f.listener_key,
    COUNT(*) AS stream_count,
    SUM(f.duration_played_ms) AS total_duration_ms,
    COUNT(DISTINCT f.track_key) AS unique_tracks,
    COUNT(DISTINCT dt.artist_key) AS unique_artists,
    SUM(f.shuffle_mode) AS shuffle_streams,
    SUM(f.offline_mode) AS offline_streams,
    SUM(f.is_full_play) AS full_plays
FROM fact_streams f
JOIN dim_track dt ON f.track_key = dt.track_key
GROUP BY f.date_key, f.listener_key;

-- ============================================================================
-- agg_daily_track_streams: Track performance by day
-- ============================================================================
INSERT INTO agg_daily_track_streams (
    date_key,
    track_key,
    stream_count,
    unique_listeners,
    total_duration_ms,
    full_plays
)
SELECT
    f.date_key,
    f.track_key,
    COUNT(*) AS stream_count,
    COUNT(DISTINCT f.listener_key) AS unique_listeners,
    SUM(f.duration_played_ms) AS total_duration_ms,
    SUM(f.is_full_play) AS full_plays
FROM fact_streams f
GROUP BY f.date_key, f.track_key;

-- ============================================================================
-- agg_monthly_genre_streams: Genre trends by month
-- ============================================================================
INSERT INTO agg_monthly_genre_streams (
    year,
    month,
    genre,
    stream_count,
    unique_listeners,
    unique_tracks,
    total_duration_ms
)
SELECT
    dd.year,
    dd.month,
    dt.genre,
    COUNT(*) AS stream_count,
    COUNT(DISTINCT f.listener_key) AS unique_listeners,
    COUNT(DISTINCT f.track_key) AS unique_tracks,
    SUM(f.duration_played_ms) AS total_duration_ms
FROM fact_streams f
JOIN dim_date dd ON f.date_key = dd.date_key
JOIN dim_track dt ON f.track_key = dt.track_key
GROUP BY dd.year, dd.month, dt.genre;
