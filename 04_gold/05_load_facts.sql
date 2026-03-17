-- Gold Layer: Load Fact Table
-- Populates fact_streams with surrogate keys from dimensions
-- Run after 04_load_dimensions.sql

-- Attach silver database
ATTACH DATABASE '../03_silver/silver.db' AS silver;

-- ============================================================================
-- fact_streams: Transform silver streams into fact table
-- ============================================================================
-- Join to all dimensions to get surrogate keys
-- Calculate derived measures (duration_played_pct, is_full_play)

INSERT INTO fact_streams (
    date_key,
    listener_key,
    track_key,
    device_key,
    stream_id,
    streamed_at,
    duration_played_ms,
    duration_played_pct,
    shuffle_mode,
    offline_mode,
    is_full_play
)
SELECT
    -- Dimension keys
    CAST(STRFTIME('%Y%m%d', DATE(s.streamed_at)) AS INTEGER) AS date_key,
    dl.listener_key,
    dt.track_key,
    dd.device_key,

    -- Degenerate dimensions
    s.stream_id,
    s.streamed_at,

    -- Measures
    s.duration_played_ms,

    -- Duration played as percentage of track length
    CASE
        WHEN dt.duration_ms > 0
        THEN ROUND((s.duration_played_ms * 100.0) / dt.duration_ms, 2)
        ELSE 0.0
    END AS duration_played_pct,

    s.shuffle_mode,
    s.offline_mode,

    -- Full play: listened to at least 90% of the track
    CASE
        WHEN dt.duration_ms > 0 AND (s.duration_played_ms * 100.0 / dt.duration_ms) >= 90.0
        THEN 1
        ELSE 0
    END AS is_full_play

FROM silver.streams s
-- Join to listener dimension
JOIN dim_listener dl ON s.listener_id = dl.listener_id
-- Join to track dimension
JOIN dim_track dt ON s.track_id = dt.track_id
-- Join to device dimension
JOIN dim_device dd ON s.device_type = dd.device_type
-- Join to date dimension (verify date exists)
JOIN dim_date ddt ON CAST(STRFTIME('%Y%m%d', DATE(s.streamed_at)) AS INTEGER) = ddt.date_key;

-- Detach silver (will reattach for aggregate loading)
DETACH DATABASE silver;
