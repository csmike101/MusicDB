-- Silver Layer: Data Transformations
-- Transforms bronze data into clean, normalized silver tables
-- Run after 01_create_tables.sql

-- Attach the bronze database
ATTACH DATABASE '../02_bronze/bronze.db' AS bronze;

-- ============================================================================
-- LISTENERS: Clean and load
-- ============================================================================
-- Listeners have no major quality issues, just trim whitespace
INSERT INTO listeners (
    listener_id,
    email,
    username,
    first_name,
    last_name,
    birth_date,
    city,
    country,
    subscription_type,
    created_at
)
SELECT
    TRIM(listener_id),
    TRIM(LOWER(email)),  -- normalize email to lowercase
    TRIM(username),
    TRIM(first_name),
    TRIM(last_name),
    CASE
        WHEN birth_date IS NOT NULL AND birth_date != 'None'
        THEN DATE(birth_date)
        ELSE NULL
    END,
    CASE
        WHEN city IS NOT NULL AND city != 'None' AND TRIM(city) != ''
        THEN TRIM(city)
        ELSE NULL
    END,
    TRIM(country),
    LOWER(TRIM(subscription_type)),
    DATETIME(created_at)
FROM bronze.bronze_listeners;

-- ============================================================================
-- ARTISTS: Normalize genre casing, trim whitespace
-- ============================================================================
INSERT INTO artists (
    artist_id,
    name,
    genre,
    country,
    formed_year,
    monthly_listeners
)
SELECT
    TRIM(artist_id),
    TRIM(name),
    -- Normalize genre to Title Case (first letter upper, rest lower)
    UPPER(SUBSTR(LOWER(TRIM(genre)), 1, 1)) || LOWER(SUBSTR(TRIM(genre), 2)),
    TRIM(country),
    CASE
        WHEN formed_year IS NOT NULL AND formed_year != 'None'
        THEN CAST(formed_year AS INTEGER)
        ELSE NULL
    END,
    CAST(monthly_listeners AS INTEGER)
FROM bronze.bronze_artists;

-- ============================================================================
-- TRACKS: Parse dates, validate artist FK, handle explicit flag
-- ============================================================================

-- First, log tracks with invalid artist references
INSERT INTO silver_rejected_records (source_table, source_id, rejection_reason)
SELECT
    'tracks',
    bt.track_id,
    'Invalid artist_id: ' || bt.artist_id
FROM bronze.bronze_tracks bt
WHERE NOT EXISTS (
    SELECT 1 FROM artists a WHERE a.artist_id = TRIM(bt.artist_id)
);

-- Insert valid tracks
INSERT INTO tracks (
    track_id,
    title,
    artist_id,
    album,
    duration_ms,
    genre,
    release_date,
    explicit
)
SELECT
    TRIM(track_id),
    TRIM(title),
    TRIM(artist_id),
    CASE
        WHEN album IS NOT NULL AND album != 'None' AND TRIM(album) != ''
        THEN TRIM(album)
        ELSE NULL
    END,
    CAST(duration_ms AS INTEGER),
    -- Normalize genre to Title Case
    UPPER(SUBSTR(LOWER(TRIM(genre)), 1, 1)) || LOWER(SUBSTR(TRIM(genre), 2)),
    -- Parse release_date handling multiple formats
    CASE
        -- Standard ISO format: YYYY-MM-DD
        WHEN release_date LIKE '____-__-__' THEN DATE(release_date)
        -- US format: MM/DD/YYYY
        WHEN release_date LIKE '__/__/____' THEN
            DATE(SUBSTR(release_date, 7, 4) || '-' ||
                 SUBSTR(release_date, 1, 2) || '-' ||
                 SUBSTR(release_date, 4, 2))
        -- Fallback: try SQLite's date parsing
        ELSE DATE(release_date)
    END,
    -- Convert explicit to integer (handle string 'True'/'False' and boolean)
    CASE
        WHEN LOWER(TRIM(explicit)) IN ('true', '1') THEN 1
        ELSE 0
    END
FROM bronze.bronze_tracks bt
WHERE EXISTS (
    SELECT 1 FROM artists a WHERE a.artist_id = TRIM(bt.artist_id)
);

-- ============================================================================
-- STREAMS: Deduplicate, validate FKs, convert types
-- ============================================================================

-- Log streams with invalid track references (before dedup to capture all)
INSERT INTO silver_rejected_records (source_table, source_id, rejection_reason)
SELECT DISTINCT
    'streams',
    bs.stream_id,
    'Invalid track_id: ' || bs.track_id
FROM bronze.bronze_streams bs
WHERE NOT EXISTS (
    SELECT 1 FROM tracks t WHERE t.track_id = TRIM(bs.track_id)
);

-- Log streams with invalid listener references
INSERT INTO silver_rejected_records (source_table, source_id, rejection_reason)
SELECT DISTINCT
    'streams',
    bs.stream_id,
    'Invalid listener_id: ' || bs.listener_id
FROM bronze.bronze_streams bs
WHERE NOT EXISTS (
    SELECT 1 FROM listeners l WHERE l.listener_id = TRIM(bs.listener_id)
)
AND EXISTS (
    SELECT 1 FROM tracks t WHERE t.track_id = TRIM(bs.track_id)
);

-- Insert deduplicated streams with valid FKs
-- Use ROW_NUMBER to keep only first occurrence of duplicates (by _row_hash)
INSERT INTO streams (
    stream_id,
    listener_id,
    track_id,
    streamed_at,
    duration_played_ms,
    device_type,
    shuffle_mode,
    offline_mode
)
SELECT
    TRIM(stream_id),
    TRIM(listener_id),
    TRIM(track_id),
    DATETIME(streamed_at),
    CAST(duration_played_ms AS INTEGER),
    TRIM(device_type),
    CASE WHEN LOWER(TRIM(shuffle_mode)) IN ('true', '1') THEN 1 ELSE 0 END,
    CASE WHEN LOWER(TRIM(offline_mode)) IN ('true', '1') THEN 1 ELSE 0 END
FROM (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY _row_hash ORDER BY _loaded_at, ROWID) AS rn
    FROM bronze.bronze_streams
) deduped
WHERE rn = 1  -- Keep first occurrence of each unique row
  AND EXISTS (
      SELECT 1 FROM tracks t WHERE t.track_id = TRIM(deduped.track_id)
  )
  AND EXISTS (
      SELECT 1 FROM listeners l WHERE l.listener_id = TRIM(deduped.listener_id)
  );

-- Detach bronze database
DETACH DATABASE bronze;
