-- Gold Layer: Fact Table DDL
-- Creates the central fact table for the star schema
-- Run after 01_create_dimensions.sql

-- ============================================================================
-- fact_streams: Central fact table recording each stream event
-- ============================================================================
-- Grain: One row per stream event
-- Measures: duration_played_ms, duration_played_pct, shuffle_mode, offline_mode, is_full_play

CREATE TABLE fact_streams (
    stream_key INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Dimension foreign keys (surrogate keys for efficient joins)
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    listener_key INTEGER NOT NULL REFERENCES dim_listener(listener_key),
    track_key INTEGER NOT NULL REFERENCES dim_track(track_key),
    device_key INTEGER NOT NULL REFERENCES dim_device(device_key),

    -- Degenerate dimensions (kept in fact for drill-through)
    stream_id TEXT NOT NULL UNIQUE,
    streamed_at DATETIME NOT NULL,

    -- Measures
    duration_played_ms INTEGER NOT NULL,
    duration_played_pct REAL NOT NULL,     -- Derived: (played / track_duration) * 100
    shuffle_mode INTEGER NOT NULL,          -- 0 or 1
    offline_mode INTEGER NOT NULL,          -- 0 or 1
    is_full_play INTEGER NOT NULL           -- Derived: 1 if played >= 90% of track
);

-- Indexes for common query patterns
-- These are critical for analytics performance

-- Time-based analysis (daily trends, monthly reports)
CREATE INDEX idx_fact_date_key ON fact_streams(date_key);

-- User-centric queries (listening history, recommendations)
CREATE INDEX idx_fact_listener_key ON fact_streams(listener_key);

-- Track popularity analysis
CREATE INDEX idx_fact_track_key ON fact_streams(track_key);

-- Device breakdown reports
CREATE INDEX idx_fact_device_key ON fact_streams(device_key);

-- Composite indexes for common multi-dimension queries
CREATE INDEX idx_fact_listener_date ON fact_streams(listener_key, date_key);
CREATE INDEX idx_fact_track_date ON fact_streams(track_key, date_key);
