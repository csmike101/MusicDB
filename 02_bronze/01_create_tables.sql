-- Bronze Layer: Staging Tables
-- All columns are TEXT to preserve raw data exactly as-is
-- No constraints - accept all data, clean in Silver layer

-- Drop tables if they exist (for idempotent runs)
DROP TABLE IF EXISTS bronze_listeners;
DROP TABLE IF EXISTS bronze_artists;
DROP TABLE IF EXISTS bronze_tracks;
DROP TABLE IF EXISTS bronze_streams;

-- Listeners staging table
CREATE TABLE bronze_listeners (
    listener_id TEXT,
    email TEXT,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    birth_date TEXT,
    city TEXT,
    country TEXT,
    subscription_type TEXT,
    created_at TEXT,
    -- Audit columns
    _source_file TEXT,
    _loaded_at TEXT,
    _row_hash TEXT
);

-- Artists staging table
CREATE TABLE bronze_artists (
    artist_id TEXT,
    name TEXT,
    genre TEXT,
    country TEXT,
    formed_year TEXT,
    monthly_listeners TEXT,
    -- Audit columns
    _source_file TEXT,
    _loaded_at TEXT,
    _row_hash TEXT
);

-- Tracks staging table
CREATE TABLE bronze_tracks (
    track_id TEXT,
    title TEXT,
    artist_id TEXT,
    album TEXT,
    duration_ms TEXT,
    genre TEXT,
    release_date TEXT,
    explicit TEXT,
    -- Audit columns
    _source_file TEXT,
    _loaded_at TEXT,
    _row_hash TEXT
);

-- Streams staging table (event log)
CREATE TABLE bronze_streams (
    stream_id TEXT,
    listener_id TEXT,
    track_id TEXT,
    streamed_at TEXT,
    duration_played_ms TEXT,
    device_type TEXT,
    shuffle_mode TEXT,
    offline_mode TEXT,
    -- Audit columns
    _source_file TEXT,
    _loaded_at TEXT,
    _row_hash TEXT
);
