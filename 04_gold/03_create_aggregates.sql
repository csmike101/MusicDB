-- Gold Layer: Aggregate Table DDL
-- Pre-computed aggregations for common query patterns
-- Run after 02_create_facts.sql

-- ============================================================================
-- agg_daily_listener_streams: Listener activity by day
-- ============================================================================
-- Use case: User dashboards, engagement metrics, churn analysis
-- Grain: One row per listener per day

CREATE TABLE agg_daily_listener_streams (
    date_key INTEGER NOT NULL,
    listener_key INTEGER NOT NULL,

    -- Measures
    stream_count INTEGER NOT NULL,
    total_duration_ms INTEGER NOT NULL,
    unique_tracks INTEGER NOT NULL,
    unique_artists INTEGER NOT NULL,
    shuffle_streams INTEGER NOT NULL,
    offline_streams INTEGER NOT NULL,
    full_plays INTEGER NOT NULL,

    PRIMARY KEY (date_key, listener_key)
);

-- Index for listener-centric queries
CREATE INDEX idx_agg_listener_daily ON agg_daily_listener_streams(listener_key, date_key);

-- ============================================================================
-- agg_daily_track_streams: Track performance by day
-- ============================================================================
-- Use case: Track popularity trends, playlist curation, royalty reporting
-- Grain: One row per track per day

CREATE TABLE agg_daily_track_streams (
    date_key INTEGER NOT NULL,
    track_key INTEGER NOT NULL,

    -- Measures
    stream_count INTEGER NOT NULL,
    unique_listeners INTEGER NOT NULL,
    total_duration_ms INTEGER NOT NULL,
    full_plays INTEGER NOT NULL,

    PRIMARY KEY (date_key, track_key)
);

-- Index for track-centric queries
CREATE INDEX idx_agg_track_daily ON agg_daily_track_streams(track_key, date_key);

-- ============================================================================
-- agg_monthly_genre_streams: Genre trends by month
-- ============================================================================
-- Use case: Genre trend analysis, content strategy, seasonal patterns
-- Grain: One row per genre per month

CREATE TABLE agg_monthly_genre_streams (
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    genre TEXT NOT NULL,

    -- Measures
    stream_count INTEGER NOT NULL,
    unique_listeners INTEGER NOT NULL,
    unique_tracks INTEGER NOT NULL,
    total_duration_ms INTEGER NOT NULL,

    PRIMARY KEY (year, month, genre)
);

-- Index for genre analysis
CREATE INDEX idx_agg_genre_monthly ON agg_monthly_genre_streams(genre, year, month);
