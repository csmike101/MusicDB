-- Gold Layer: Dimension Table DDL
-- Creates dimension tables for the star schema
-- Run this first before other gold layer scripts

-- Drop tables if they exist (for idempotent runs)
-- Drop in reverse dependency order
DROP TABLE IF EXISTS fact_streams;
DROP TABLE IF EXISTS agg_daily_listener_streams;
DROP TABLE IF EXISTS agg_daily_track_streams;
DROP TABLE IF EXISTS agg_monthly_genre_streams;
DROP TABLE IF EXISTS dim_track;
DROP TABLE IF EXISTS dim_artist;
DROP TABLE IF EXISTS dim_listener;
DROP TABLE IF EXISTS dim_device;
DROP TABLE IF EXISTS dim_date;

-- ============================================================================
-- dim_date: Calendar dimension for time-based analytics
-- ============================================================================
-- Pre-populated with all dates in 2025
-- date_key uses YYYYMMDD integer format for efficient joins
CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,      -- YYYYMMDD format (e.g., 20250115)
    full_date DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,          -- 1-4
    month INTEGER NOT NULL,            -- 1-12
    month_name TEXT NOT NULL,          -- 'January', 'February', etc.
    week_of_year INTEGER NOT NULL,     -- 1-53
    day_of_month INTEGER NOT NULL,     -- 1-31
    day_of_week INTEGER NOT NULL,      -- 0=Sunday, 6=Saturday
    day_name TEXT NOT NULL,            -- 'Sunday', 'Monday', etc.
    is_weekend INTEGER NOT NULL,       -- 0 or 1
    is_holiday INTEGER NOT NULL        -- 0 or 1 (US federal holidays)
);

-- ============================================================================
-- dim_listener: User dimension with derived attributes
-- ============================================================================
CREATE TABLE dim_listener (
    listener_key INTEGER PRIMARY KEY AUTOINCREMENT,
    listener_id TEXT NOT NULL UNIQUE,  -- Natural key from source
    email TEXT NOT NULL,
    username TEXT NOT NULL,
    full_name TEXT NOT NULL,           -- Derived: first_name || ' ' || last_name
    birth_date DATE,
    age_group TEXT,                    -- Derived: 'Under 18', '18-24', '25-34', etc.
    city TEXT,
    country TEXT NOT NULL,
    subscription_type TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    tenure_months INTEGER              -- Derived: months since created_at
);

-- ============================================================================
-- dim_artist: Artist/band dimension with popularity tiers
-- ============================================================================
CREATE TABLE dim_artist (
    artist_key INTEGER PRIMARY KEY AUTOINCREMENT,
    artist_id TEXT NOT NULL UNIQUE,    -- Natural key from source
    name TEXT NOT NULL,
    genre TEXT NOT NULL,
    country TEXT NOT NULL,
    formed_year INTEGER,
    years_active INTEGER,              -- Derived: current year - formed_year
    monthly_listeners INTEGER NOT NULL,
    popularity_tier TEXT               -- Derived: 'emerging', 'established', 'star', 'superstar'
);

-- ============================================================================
-- dim_track: Track dimension with duration buckets
-- ============================================================================
CREATE TABLE dim_track (
    track_key INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id TEXT NOT NULL UNIQUE,     -- Natural key from source
    title TEXT NOT NULL,
    artist_key INTEGER NOT NULL REFERENCES dim_artist(artist_key),
    album TEXT,
    duration_ms INTEGER NOT NULL,
    duration_bucket TEXT,              -- Derived: 'short', 'medium', 'long'
    genre TEXT NOT NULL,
    release_date DATE NOT NULL,
    release_year INTEGER NOT NULL,     -- Derived from release_date
    explicit INTEGER NOT NULL
);

-- ============================================================================
-- dim_device: Device type dimension (small/static)
-- ============================================================================
CREATE TABLE dim_device (
    device_key INTEGER PRIMARY KEY AUTOINCREMENT,
    device_type TEXT NOT NULL UNIQUE,
    device_category TEXT NOT NULL      -- 'mobile', 'desktop', 'other'
);

-- Create indexes on natural keys for fast lookups during fact loading
CREATE INDEX idx_dim_listener_id ON dim_listener(listener_id);
CREATE INDEX idx_dim_artist_id ON dim_artist(artist_id);
CREATE INDEX idx_dim_track_id ON dim_track(track_id);
CREATE INDEX idx_dim_date_full ON dim_date(full_date);
