-- Serving Layer: Year in Review Queries
-- Spotify Wrapped-style analytics for each listener
-- These queries power the personalized year-end summary
--
-- Note: These views are created directly in gold.db.
-- Run this script against gold.db after 01_create_views.sql.

-- Drop existing views if they exist (for idempotent runs)
DROP VIEW IF EXISTS v_top_artists_by_listener;
DROP VIEW IF EXISTS v_top_tracks_by_listener;
DROP VIEW IF EXISTS v_top_genre_by_listener;
DROP VIEW IF EXISTS v_listening_personality;
DROP VIEW IF EXISTS v_monthly_trends_by_listener;
DROP VIEW IF EXISTS v_peak_listening_times;
DROP VIEW IF EXISTS v_weekday_vs_weekend;
DROP VIEW IF EXISTS v_discovery_stats;
DROP VIEW IF EXISTS v_year_in_review_summary;

-- ============================================================================
-- QUERY 1: Top 5 Artists per Listener
-- ============================================================================
-- "Your top artists of 2025"

CREATE VIEW v_top_artists_by_listener AS
WITH ranked_artists AS (
    SELECT
        l.listener_id,
        l.full_name AS listener_name,
        a.artist_id,
        a.name AS artist_name,
        a.genre AS artist_genre,
        a.popularity_tier,
        COUNT(*) AS stream_count,
        SUM(f.is_full_play) AS full_plays,
        ROUND(SUM(f.duration_played_ms) / 60000.0, 1) AS minutes_listened,
        ROW_NUMBER() OVER (
            PARTITION BY l.listener_key
            ORDER BY SUM(f.duration_played_ms) DESC
        ) AS artist_rank
    FROM fact_streams f
    JOIN dim_listener l ON f.listener_key = l.listener_key
    JOIN dim_track t ON f.track_key = t.track_key
    JOIN dim_artist a ON t.artist_key = a.artist_key
    GROUP BY l.listener_key, a.artist_key
)
SELECT *
FROM ranked_artists
WHERE artist_rank <= 5;

-- ============================================================================
-- QUERY 2: Top 5 Tracks per Listener
-- ============================================================================
-- "Your most played songs"

CREATE VIEW v_top_tracks_by_listener AS
WITH ranked_tracks AS (
    SELECT
        l.listener_id,
        l.full_name AS listener_name,
        t.track_id,
        t.title AS track_title,
        t.album,
        a.name AS artist_name,
        t.genre,
        COUNT(*) AS play_count,
        SUM(f.is_full_play) AS full_plays,
        ROUND(SUM(f.duration_played_ms) / 60000.0, 1) AS minutes_listened,
        ROUND(AVG(f.duration_played_pct), 1) AS avg_completion_pct,
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
WHERE track_rank <= 5;

-- ============================================================================
-- QUERY 3: Top Genre per Listener
-- ============================================================================
-- "Your audio aura" / dominant genre

CREATE VIEW v_top_genre_by_listener AS
WITH genre_stats AS (
    SELECT
        l.listener_id,
        l.full_name AS listener_name,
        t.genre,
        COUNT(*) AS stream_count,
        COUNT(DISTINCT t.track_key) AS unique_tracks,
        COUNT(DISTINCT a.artist_key) AS unique_artists,
        ROUND(SUM(f.duration_played_ms) / 60000.0, 1) AS minutes_listened,
        ROW_NUMBER() OVER (
            PARTITION BY l.listener_key
            ORDER BY SUM(f.duration_played_ms) DESC
        ) AS genre_rank
    FROM fact_streams f
    JOIN dim_listener l ON f.listener_key = l.listener_key
    JOIN dim_track t ON f.track_key = t.track_key
    JOIN dim_artist a ON t.artist_key = a.artist_key
    GROUP BY l.listener_key, t.genre
)
SELECT
    listener_id,
    listener_name,
    genre AS top_genre,
    stream_count,
    unique_tracks,
    unique_artists,
    minutes_listened,
    -- Calculate genre dominance (% of total listening)
    ROUND(minutes_listened * 100.0 / SUM(minutes_listened) OVER (PARTITION BY listener_id), 1) AS genre_share_pct
FROM genre_stats
WHERE genre_rank = 1;

-- ============================================================================
-- QUERY 4: Listening Personality
-- ============================================================================
-- "You're a [Explorer/Genre Purist/Shuffler/etc.]"

CREATE VIEW v_listening_personality AS
SELECT
    l.listener_id,
    l.full_name AS listener_name,

    -- Classify based on behavior patterns
    CASE
        WHEN COUNT(DISTINCT a.artist_key) >= 80 THEN 'Explorer'
        WHEN COUNT(DISTINCT t.genre) <= 3 THEN 'Genre Loyalist'
        WHEN SUM(f.shuffle_mode) * 1.0 / COUNT(*) > 0.7 THEN 'The Shuffler'
        WHEN SUM(f.is_full_play) * 1.0 / COUNT(*) > 0.85 THEN 'Deep Listener'
        WHEN SUM(f.offline_mode) * 1.0 / COUNT(*) > 0.5 THEN 'Offline Adventurer'
        WHEN COUNT(*) > 2500 THEN 'Power User'
        ELSE 'Casual Listener'
    END AS listening_personality,

    -- Supporting metrics
    COUNT(*) AS total_streams,
    COUNT(DISTINCT a.artist_key) AS unique_artists,
    COUNT(DISTINCT t.track_key) AS unique_tracks,
    COUNT(DISTINCT t.genre) AS unique_genres,
    ROUND(SUM(f.shuffle_mode) * 100.0 / COUNT(*), 1) AS shuffle_pct,
    ROUND(SUM(f.is_full_play) * 100.0 / COUNT(*), 1) AS full_play_pct,
    ROUND(SUM(f.offline_mode) * 100.0 / COUNT(*), 1) AS offline_pct

FROM fact_streams f
JOIN dim_listener l ON f.listener_key = l.listener_key
JOIN dim_track t ON f.track_key = t.track_key
JOIN dim_artist a ON t.artist_key = a.artist_key
GROUP BY l.listener_key;

-- ============================================================================
-- QUERY 5: Monthly Listening Trends
-- ============================================================================
-- "Your listening journey through 2025"

CREATE VIEW v_monthly_trends_by_listener AS
SELECT
    l.listener_id,
    l.full_name AS listener_name,
    d.month,
    d.month_name,
    COUNT(*) AS streams,
    COUNT(DISTINCT t.track_key) AS unique_tracks,
    COUNT(DISTINCT a.artist_key) AS unique_artists,
    ROUND(SUM(f.duration_played_ms) / 60000.0, 1) AS minutes_listened,
    ROUND(SUM(f.duration_played_ms) / 3600000.0, 1) AS hours_listened
FROM fact_streams f
JOIN dim_listener l ON f.listener_key = l.listener_key
JOIN dim_track t ON f.track_key = t.track_key
JOIN dim_artist a ON t.artist_key = a.artist_key
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY l.listener_key, d.month
ORDER BY l.listener_id, d.month;

-- ============================================================================
-- QUERY 6: Peak Listening Times
-- ============================================================================
-- "You're a night owl" / "Early bird listener"

CREATE VIEW v_peak_listening_times AS
WITH time_breakdown AS (
    SELECT
        l.listener_id,
        l.full_name AS listener_name,
        CASE
            WHEN CAST(STRFTIME('%H', f.streamed_at) AS INTEGER) BETWEEN 5 AND 8 THEN 'Early Morning'
            WHEN CAST(STRFTIME('%H', f.streamed_at) AS INTEGER) BETWEEN 9 AND 11 THEN 'Morning'
            WHEN CAST(STRFTIME('%H', f.streamed_at) AS INTEGER) BETWEEN 12 AND 14 THEN 'Midday'
            WHEN CAST(STRFTIME('%H', f.streamed_at) AS INTEGER) BETWEEN 15 AND 17 THEN 'Afternoon'
            WHEN CAST(STRFTIME('%H', f.streamed_at) AS INTEGER) BETWEEN 18 AND 20 THEN 'Evening'
            WHEN CAST(STRFTIME('%H', f.streamed_at) AS INTEGER) BETWEEN 21 AND 23 THEN 'Night'
            ELSE 'Late Night'
        END AS time_of_day,
        COUNT(*) AS stream_count
    FROM fact_streams f
    JOIN dim_listener l ON f.listener_key = l.listener_key
    GROUP BY l.listener_key, time_of_day
),
ranked_times AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY listener_id ORDER BY stream_count DESC) AS time_rank,
        ROUND(stream_count * 100.0 / SUM(stream_count) OVER (PARTITION BY listener_id), 1) AS pct_of_listening
    FROM time_breakdown
)
SELECT *
FROM ranked_times
WHERE time_rank <= 3
ORDER BY listener_id, time_rank;

-- ============================================================================
-- QUERY 7: Weekend vs Weekday Listening
-- ============================================================================
-- "You're a weekday warrior" / "Weekend streamer"

CREATE VIEW v_weekday_vs_weekend AS
SELECT
    l.listener_id,
    l.full_name AS listener_name,
    SUM(CASE WHEN d.is_weekend = 0 THEN 1 ELSE 0 END) AS weekday_streams,
    SUM(CASE WHEN d.is_weekend = 1 THEN 1 ELSE 0 END) AS weekend_streams,
    ROUND(SUM(CASE WHEN d.is_weekend = 0 THEN f.duration_played_ms ELSE 0 END) / 60000.0, 1) AS weekday_minutes,
    ROUND(SUM(CASE WHEN d.is_weekend = 1 THEN f.duration_played_ms ELSE 0 END) / 60000.0, 1) AS weekend_minutes,
    -- Average per day type (5 weekdays, 2 weekend days)
    ROUND(SUM(CASE WHEN d.is_weekend = 0 THEN 1 ELSE 0 END) * 1.0 / (52 * 5), 1) AS avg_weekday_streams,
    ROUND(SUM(CASE WHEN d.is_weekend = 1 THEN 1 ELSE 0 END) * 1.0 / (52 * 2), 1) AS avg_weekend_streams,
    CASE
        WHEN SUM(CASE WHEN d.is_weekend = 1 THEN 1 ELSE 0 END) * 2.5 >
             SUM(CASE WHEN d.is_weekend = 0 THEN 1 ELSE 0 END) THEN 'Weekend Warrior'
        ELSE 'Weekday Listener'
    END AS listener_type
FROM fact_streams f
JOIN dim_listener l ON f.listener_key = l.listener_key
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY l.listener_key;

-- ============================================================================
-- QUERY 8: Discovery Stats
-- ============================================================================
-- "You discovered X new artists this year"

CREATE VIEW v_discovery_stats AS
WITH first_listens AS (
    SELECT
        f.listener_key,
        a.artist_key,
        t.track_key,
        MIN(f.streamed_at) AS first_listen_date
    FROM fact_streams f
    JOIN dim_track t ON f.track_key = t.track_key
    JOIN dim_artist a ON t.artist_key = a.artist_key
    GROUP BY f.listener_key, a.artist_key, t.track_key
)
SELECT
    l.listener_id,
    l.full_name AS listener_name,
    COUNT(DISTINCT fl.artist_key) AS total_artists_played,
    COUNT(DISTINCT fl.track_key) AS total_tracks_played,
    -- Artists discovered by quarter
    COUNT(DISTINCT CASE WHEN STRFTIME('%m', fl.first_listen_date) IN ('01','02','03') THEN fl.artist_key END) AS q1_new_artists,
    COUNT(DISTINCT CASE WHEN STRFTIME('%m', fl.first_listen_date) IN ('04','05','06') THEN fl.artist_key END) AS q2_new_artists,
    COUNT(DISTINCT CASE WHEN STRFTIME('%m', fl.first_listen_date) IN ('07','08','09') THEN fl.artist_key END) AS q3_new_artists,
    COUNT(DISTINCT CASE WHEN STRFTIME('%m', fl.first_listen_date) IN ('10','11','12') THEN fl.artist_key END) AS q4_new_artists
FROM first_listens fl
JOIN dim_listener l ON fl.listener_key = l.listener_key
GROUP BY fl.listener_key;

-- ============================================================================
-- QUERY 9: Complete Year in Review Summary
-- ============================================================================
-- Combines all metrics into one comprehensive view per listener

CREATE VIEW v_year_in_review_summary AS
SELECT
    l.listener_id,
    l.full_name AS listener_name,
    l.subscription_type,
    l.country,

    -- Total Activity
    COUNT(*) AS total_streams,
    ROUND(SUM(f.duration_played_ms) / 60000.0, 0) AS total_minutes,
    ROUND(SUM(f.duration_played_ms) / 3600000.0, 1) AS total_hours,
    COUNT(DISTINCT d.full_date) AS days_active,

    -- Diversity
    COUNT(DISTINCT t.track_key) AS unique_tracks,
    COUNT(DISTINCT a.artist_key) AS unique_artists,
    COUNT(DISTINCT t.genre) AS unique_genres,

    -- Engagement
    ROUND(AVG(f.duration_played_pct), 1) AS avg_completion_pct,
    SUM(f.is_full_play) AS full_plays,
    ROUND(SUM(f.is_full_play) * 100.0 / COUNT(*), 1) AS full_play_rate,

    -- Behavior
    ROUND(SUM(f.shuffle_mode) * 100.0 / COUNT(*), 1) AS shuffle_pct,
    ROUND(SUM(f.offline_mode) * 100.0 / COUNT(*), 1) AS offline_pct,

    -- Percentile ranking (how you compare to others)
    ROUND(PERCENT_RANK() OVER (ORDER BY SUM(f.duration_played_ms)) * 100, 0) AS listening_percentile

FROM fact_streams f
JOIN dim_listener l ON f.listener_key = l.listener_key
JOIN dim_track t ON f.track_key = t.track_key
JOIN dim_artist a ON t.artist_key = a.artist_key
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY l.listener_key;
