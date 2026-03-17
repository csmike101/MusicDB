-- Serving Layer: Semantic Views
-- Creates analytics-ready views over the gold layer
-- These views hide complexity and provide business-friendly names
--
-- Note: These views are created directly in gold.db since SQLite views
-- cannot reference attached databases. Run this script against gold.db.

-- Drop existing views if they exist (for idempotent runs)
DROP VIEW IF EXISTS v_stream_details;
DROP VIEW IF EXISTS v_listener_summary;
DROP VIEW IF EXISTS v_track_popularity;
DROP VIEW IF EXISTS v_artist_popularity;
DROP VIEW IF EXISTS v_genre_trends;
DROP VIEW IF EXISTS v_daily_platform_stats;

-- ============================================================================
-- v_stream_details: Fully denormalized stream view
-- ============================================================================
-- Use case: Ad-hoc analysis, data exploration, detailed drill-down
-- One row per stream with all dimensional context flattened

CREATE VIEW v_stream_details AS
SELECT
    -- Stream identifiers
    f.stream_id,
    f.streamed_at,

    -- Listener info
    l.listener_id,
    l.full_name AS listener_name,
    l.email AS listener_email,
    l.age_group,
    l.country AS listener_country,
    l.subscription_type,
    l.tenure_months,

    -- Track info
    t.track_id,
    t.title AS track_title,
    t.album,
    t.duration_ms AS track_duration_ms,
    ROUND(t.duration_ms / 1000.0, 1) AS track_duration_sec,
    t.duration_bucket,
    t.genre,
    t.release_year,
    t.explicit,

    -- Artist info
    a.artist_id,
    a.name AS artist_name,
    a.genre AS artist_genre,
    a.popularity_tier,
    a.years_active AS artist_years_active,

    -- Device info
    dv.device_type,
    dv.device_category,

    -- Date info
    d.full_date AS stream_date,
    d.year,
    d.quarter,
    d.month,
    d.month_name,
    d.week_of_year,
    d.day_of_week,
    d.day_name,
    d.is_weekend,
    d.is_holiday,

    -- Measures (with user-friendly transformations)
    f.duration_played_ms,
    ROUND(f.duration_played_ms / 1000.0, 1) AS duration_played_sec,
    ROUND(f.duration_played_ms / 60000.0, 2) AS duration_played_min,
    ROUND(f.duration_played_pct, 1) AS completion_pct,
    f.is_full_play,
    f.shuffle_mode,
    f.offline_mode

FROM fact_streams f
JOIN dim_listener l ON f.listener_key = l.listener_key
JOIN dim_track t ON f.track_key = t.track_key
JOIN dim_artist a ON t.artist_key = a.artist_key
JOIN dim_device dv ON f.device_key = dv.device_key
JOIN dim_date d ON f.date_key = d.date_key;

-- ============================================================================
-- v_listener_summary: Aggregated listener statistics
-- ============================================================================
-- Use case: User dashboards, engagement metrics, segmentation
-- One row per listener with their total activity

CREATE VIEW v_listener_summary AS
SELECT
    l.listener_id,
    l.full_name,
    l.email,
    l.age_group,
    l.country,
    l.subscription_type,
    l.tenure_months,

    -- Stream counts
    COUNT(*) AS total_streams,
    SUM(f.is_full_play) AS full_plays,
    SUM(f.shuffle_mode) AS shuffle_streams,
    SUM(f.offline_mode) AS offline_streams,

    -- Diversity metrics
    COUNT(DISTINCT t.track_key) AS unique_tracks,
    COUNT(DISTINCT a.artist_key) AS unique_artists,
    COUNT(DISTINCT t.genre) AS unique_genres,

    -- Time metrics
    SUM(f.duration_played_ms) AS total_ms,
    ROUND(SUM(f.duration_played_ms) / 1000.0 / 60.0, 1) AS total_minutes,
    ROUND(SUM(f.duration_played_ms) / 1000.0 / 60.0 / 60.0, 1) AS total_hours,

    -- Averages
    ROUND(AVG(f.duration_played_pct), 1) AS avg_completion_pct,
    ROUND(AVG(f.duration_played_ms) / 1000.0, 1) AS avg_stream_duration_sec,

    -- Behavior percentages
    ROUND(SUM(f.is_full_play) * 100.0 / COUNT(*), 1) AS full_play_pct,
    ROUND(SUM(f.shuffle_mode) * 100.0 / COUNT(*), 1) AS shuffle_pct,
    ROUND(SUM(f.offline_mode) * 100.0 / COUNT(*), 1) AS offline_pct,

    -- Activity span
    MIN(d.full_date) AS first_stream_date,
    MAX(d.full_date) AS last_stream_date,
    COUNT(DISTINCT d.full_date) AS active_days

FROM fact_streams f
JOIN dim_listener l ON f.listener_key = l.listener_key
JOIN dim_track t ON f.track_key = t.track_key
JOIN dim_artist a ON t.artist_key = a.artist_key
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY l.listener_key;

-- ============================================================================
-- v_track_popularity: Track rankings with engagement metrics
-- ============================================================================
-- Use case: Chart rankings, playlist curation, content performance
-- One row per track with popularity metrics

CREATE VIEW v_track_popularity AS
SELECT
    t.track_id,
    t.title,
    t.album,
    a.name AS artist_name,
    a.artist_id,
    t.genre,
    t.release_year,
    t.duration_bucket,
    t.explicit,

    -- Popularity metrics
    COUNT(*) AS stream_count,
    COUNT(DISTINCT f.listener_key) AS unique_listeners,
    SUM(f.is_full_play) AS full_plays,

    -- Time metrics
    ROUND(SUM(f.duration_played_ms) / 1000.0 / 60.0, 1) AS total_minutes_played,

    -- Engagement metrics
    ROUND(AVG(f.duration_played_pct), 1) AS avg_completion_pct,
    ROUND(SUM(f.is_full_play) * 100.0 / COUNT(*), 1) AS full_play_rate,

    -- Rankings
    RANK() OVER (ORDER BY COUNT(*) DESC) AS overall_rank,
    RANK() OVER (PARTITION BY t.genre ORDER BY COUNT(*) DESC) AS genre_rank

FROM fact_streams f
JOIN dim_track t ON f.track_key = t.track_key
JOIN dim_artist a ON t.artist_key = a.artist_key
GROUP BY t.track_key;

-- ============================================================================
-- v_artist_popularity: Artist rankings with engagement metrics
-- ============================================================================
-- Use case: Artist performance, royalty insights, discovery features
-- One row per artist with aggregated metrics

CREATE VIEW v_artist_popularity AS
SELECT
    a.artist_id,
    a.name AS artist_name,
    a.genre,
    a.country,
    a.popularity_tier,
    a.years_active,
    a.monthly_listeners,

    -- Catalog metrics
    COUNT(DISTINCT t.track_key) AS tracks_in_catalog,
    COUNT(DISTINCT t.album) AS albums,

    -- Stream metrics
    COUNT(*) AS total_streams,
    COUNT(DISTINCT f.listener_key) AS unique_listeners,
    SUM(f.is_full_play) AS full_plays,

    -- Time metrics
    ROUND(SUM(f.duration_played_ms) / 1000.0 / 60.0, 1) AS total_minutes_played,
    ROUND(SUM(f.duration_played_ms) / 1000.0 / 60.0 / 60.0, 1) AS total_hours_played,

    -- Engagement
    ROUND(AVG(f.duration_played_pct), 1) AS avg_completion_pct,

    -- Rankings
    RANK() OVER (ORDER BY COUNT(*) DESC) AS overall_rank,
    RANK() OVER (PARTITION BY a.genre ORDER BY COUNT(*) DESC) AS genre_rank

FROM fact_streams f
JOIN dim_track t ON f.track_key = t.track_key
JOIN dim_artist a ON t.artist_key = a.artist_key
GROUP BY a.artist_key;

-- ============================================================================
-- v_genre_trends: Genre performance over time
-- ============================================================================
-- Use case: Content strategy, trend analysis, seasonal patterns
-- One row per genre per month

CREATE VIEW v_genre_trends AS
SELECT
    d.year,
    d.month,
    d.month_name,
    t.genre,

    -- Volume metrics
    COUNT(*) AS stream_count,
    COUNT(DISTINCT f.listener_key) AS unique_listeners,
    COUNT(DISTINCT t.track_key) AS unique_tracks,
    COUNT(DISTINCT a.artist_key) AS unique_artists,

    -- Time metrics
    ROUND(SUM(f.duration_played_ms) / 1000.0 / 60.0 / 60.0, 1) AS total_hours,

    -- Engagement
    ROUND(AVG(f.duration_played_pct), 1) AS avg_completion_pct,

    -- Genre share of month
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY d.year, d.month), 1) AS month_share_pct

FROM fact_streams f
JOIN dim_track t ON f.track_key = t.track_key
JOIN dim_artist a ON t.artist_key = a.artist_key
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.year, d.month, t.genre
ORDER BY d.year, d.month, stream_count DESC;

-- ============================================================================
-- v_daily_platform_stats: Platform-wide daily metrics
-- ============================================================================
-- Use case: Executive dashboards, platform health monitoring
-- One row per day with platform-wide totals

CREATE VIEW v_daily_platform_stats AS
SELECT
    d.full_date,
    d.year,
    d.month,
    d.month_name,
    d.day_name,
    d.is_weekend,
    d.is_holiday,

    -- Volume
    COUNT(*) AS total_streams,
    COUNT(DISTINCT f.listener_key) AS active_listeners,
    COUNT(DISTINCT t.track_key) AS unique_tracks_played,
    COUNT(DISTINCT a.artist_key) AS unique_artists_played,

    -- Time
    ROUND(SUM(f.duration_played_ms) / 1000.0 / 60.0 / 60.0, 1) AS total_hours_streamed,

    -- Engagement
    ROUND(AVG(f.duration_played_pct), 1) AS avg_completion_pct,
    ROUND(SUM(f.is_full_play) * 100.0 / COUNT(*), 1) AS full_play_rate,

    -- Mode breakdown
    ROUND(SUM(f.shuffle_mode) * 100.0 / COUNT(*), 1) AS shuffle_pct,
    ROUND(SUM(f.offline_mode) * 100.0 / COUNT(*), 1) AS offline_pct

FROM fact_streams f
JOIN dim_track t ON f.track_key = t.track_key
JOIN dim_artist a ON t.artist_key = a.artist_key
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.date_key
ORDER BY d.full_date;
