-- Silver Layer: Table Creation DDL
-- Creates normalized tables with proper types and constraints
-- Run this before 02_transform_data.sql

-- Drop tables if they exist (for idempotent runs)
DROP TABLE IF EXISTS streams;
DROP TABLE IF EXISTS tracks;
DROP TABLE IF EXISTS artists;
DROP TABLE IF EXISTS listeners;
DROP TABLE IF EXISTS silver_rejected_records;

-- Listeners table
-- Cleaned user profiles with constraints
CREATE TABLE listeners (
    listener_id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    birth_date DATE,  -- nullable (some users don't provide)
    city TEXT,  -- nullable
    country TEXT NOT NULL,
    subscription_type TEXT NOT NULL CHECK (subscription_type IN ('free', 'premium')),
    created_at DATETIME NOT NULL
);

-- Artists table
-- Musicians/bands with normalized genre casing
CREATE TABLE artists (
    artist_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    genre TEXT NOT NULL,  -- normalized to Title Case
    country TEXT NOT NULL,
    formed_year INTEGER,  -- nullable
    monthly_listeners INTEGER NOT NULL
);

-- Tracks table
-- Songs with foreign key to artists
CREATE TABLE tracks (
    track_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    artist_id TEXT NOT NULL REFERENCES artists(artist_id),
    album TEXT,  -- nullable
    duration_ms INTEGER NOT NULL,
    genre TEXT NOT NULL,
    release_date DATE NOT NULL,
    explicit INTEGER NOT NULL CHECK (explicit IN (0, 1))
);

-- Streams table
-- Listening events with foreign keys to listeners and tracks
CREATE TABLE streams (
    stream_id TEXT PRIMARY KEY,
    listener_id TEXT NOT NULL REFERENCES listeners(listener_id),
    track_id TEXT NOT NULL REFERENCES tracks(track_id),
    streamed_at DATETIME NOT NULL,
    duration_played_ms INTEGER NOT NULL,
    device_type TEXT NOT NULL,
    shuffle_mode INTEGER NOT NULL CHECK (shuffle_mode IN (0, 1)),
    offline_mode INTEGER NOT NULL CHECK (offline_mode IN (0, 1))
);

-- Rejected records table
-- Tracks records that failed validation for audit purposes
CREATE TABLE silver_rejected_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_table TEXT NOT NULL,
    source_id TEXT,
    rejection_reason TEXT NOT NULL,
    rejected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
