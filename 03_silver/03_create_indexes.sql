-- Silver Layer: Performance Indexes
-- Run after 02_transform_data.sql

-- ============================================================================
-- LISTENER INDEXES
-- ============================================================================
-- Email lookups (login, account management)
CREATE INDEX IF NOT EXISTS idx_listeners_email ON listeners(email);

-- Country-based analytics
CREATE INDEX IF NOT EXISTS idx_listeners_country ON listeners(country);

-- Subscription type filtering
CREATE INDEX IF NOT EXISTS idx_listeners_subscription ON listeners(subscription_type);

-- ============================================================================
-- ARTIST INDEXES
-- ============================================================================
-- Genre-based discovery and analytics
CREATE INDEX IF NOT EXISTS idx_artists_genre ON artists(genre);

-- Country-based filtering
CREATE INDEX IF NOT EXISTS idx_artists_country ON artists(country);

-- Popularity sorting
CREATE INDEX IF NOT EXISTS idx_artists_monthly_listeners ON artists(monthly_listeners);

-- ============================================================================
-- TRACK INDEXES
-- ============================================================================
-- Artist lookup (get all tracks by artist)
CREATE INDEX IF NOT EXISTS idx_tracks_artist_id ON tracks(artist_id);

-- Genre filtering
CREATE INDEX IF NOT EXISTS idx_tracks_genre ON tracks(genre);

-- Release date for "new releases" queries
CREATE INDEX IF NOT EXISTS idx_tracks_release_date ON tracks(release_date);

-- Explicit content filtering
CREATE INDEX IF NOT EXISTS idx_tracks_explicit ON tracks(explicit);

-- ============================================================================
-- STREAM INDEXES (Critical for analytics performance)
-- ============================================================================
-- Listener activity (user's listening history)
CREATE INDEX IF NOT EXISTS idx_streams_listener_id ON streams(listener_id);

-- Track popularity (play counts per track)
CREATE INDEX IF NOT EXISTS idx_streams_track_id ON streams(track_id);

-- Time-based analytics (daily/weekly/monthly trends)
CREATE INDEX IF NOT EXISTS idx_streams_streamed_at ON streams(streamed_at);

-- Device analytics
CREATE INDEX IF NOT EXISTS idx_streams_device_type ON streams(device_type);

-- Composite index for common query pattern: listener + time range
CREATE INDEX IF NOT EXISTS idx_streams_listener_time ON streams(listener_id, streamed_at);

-- Composite index for track popularity over time
CREATE INDEX IF NOT EXISTS idx_streams_track_time ON streams(track_id, streamed_at);
