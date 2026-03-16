-- Bronze Layer: Table Creation
--
-- These staging tables preserve raw data exactly as received.
-- All business fields are TEXT to avoid type coercion failures.
-- Audit columns track data lineage.
--
-- No constraints are applied - validation happens in the Silver layer.

-- Drop existing tables if re-running
DROP TABLE IF EXISTS bronze_listeners;
DROP TABLE IF EXISTS bronze_artists;
DROP TABLE IF EXISTS bronze_tracks;
DROP TABLE IF EXISTS bronze_streams;

-- Listeners table (source: listeners.json)
CREATE TABLE bronze_listeners (
    -- Source fields (all TEXT to preserve raw data)
    listener_id TEXT,
    email TEXT,
    username TEXT,
    age TEXT,
    country TEXT,
    city TEXT,
    signup_date TEXT,
    subscription_tier TEXT,
    -- Audit columns
    _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    _source_file TEXT,
    _row_number INTEGER
);

-- Artists table (source: artists.csv)
CREATE TABLE bronze_artists (
    artist_id TEXT,
    name TEXT,
    genre TEXT,
    country TEXT,
    formed_year TEXT,
    -- Audit columns
    _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    _source_file TEXT,
    _row_number INTEGER
);

-- Tracks table (source: tracks.csv)
CREATE TABLE bronze_tracks (
    track_id TEXT,
    title TEXT,
    artist_id TEXT,
    album TEXT,
    duration_seconds TEXT,
    release_date TEXT,
    genre TEXT,
    -- Audit columns
    _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    _source_file TEXT,
    _row_number INTEGER
);

-- Streams table (source: streams.csv)
CREATE TABLE bronze_streams (
    stream_id TEXT,
    listener_id TEXT,
    track_id TEXT,
    streamed_at TEXT,
    duration_listened TEXT,
    platform TEXT,
    -- Audit columns
    _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    _source_file TEXT,
    _row_number INTEGER
);
