-- Gold Layer: Load Dimension Tables
-- Populates dimension tables from silver layer
-- Run after creating all tables (01, 02, 03 scripts)

-- Attach silver database
ATTACH DATABASE '../03_silver/silver.db' AS silver;

-- ============================================================================
-- dim_date: Generate calendar for 2025
-- ============================================================================
-- SQLite doesn't have generate_series, so we use a recursive CTE

WITH RECURSIVE dates(d) AS (
    SELECT DATE('2025-01-01')
    UNION ALL
    SELECT DATE(d, '+1 day')
    FROM dates
    WHERE d < '2025-12-31'
)
INSERT INTO dim_date (
    date_key,
    full_date,
    year,
    quarter,
    month,
    month_name,
    week_of_year,
    day_of_month,
    day_of_week,
    day_name,
    is_weekend,
    is_holiday
)
SELECT
    CAST(STRFTIME('%Y%m%d', d) AS INTEGER) AS date_key,
    d AS full_date,
    CAST(STRFTIME('%Y', d) AS INTEGER) AS year,
    CASE
        WHEN CAST(STRFTIME('%m', d) AS INTEGER) <= 3 THEN 1
        WHEN CAST(STRFTIME('%m', d) AS INTEGER) <= 6 THEN 2
        WHEN CAST(STRFTIME('%m', d) AS INTEGER) <= 9 THEN 3
        ELSE 4
    END AS quarter,
    CAST(STRFTIME('%m', d) AS INTEGER) AS month,
    CASE CAST(STRFTIME('%m', d) AS INTEGER)
        WHEN 1 THEN 'January'
        WHEN 2 THEN 'February'
        WHEN 3 THEN 'March'
        WHEN 4 THEN 'April'
        WHEN 5 THEN 'May'
        WHEN 6 THEN 'June'
        WHEN 7 THEN 'July'
        WHEN 8 THEN 'August'
        WHEN 9 THEN 'September'
        WHEN 10 THEN 'October'
        WHEN 11 THEN 'November'
        WHEN 12 THEN 'December'
    END AS month_name,
    CAST(STRFTIME('%W', d) AS INTEGER) + 1 AS week_of_year,
    CAST(STRFTIME('%d', d) AS INTEGER) AS day_of_month,
    CAST(STRFTIME('%w', d) AS INTEGER) AS day_of_week,  -- 0=Sunday
    CASE CAST(STRFTIME('%w', d) AS INTEGER)
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END AS day_name,
    CASE WHEN CAST(STRFTIME('%w', d) AS INTEGER) IN (0, 6) THEN 1 ELSE 0 END AS is_weekend,
    -- US Federal Holidays (simplified - fixed dates only)
    CASE
        WHEN STRFTIME('%m-%d', d) = '01-01' THEN 1  -- New Year's Day
        WHEN STRFTIME('%m-%d', d) = '07-04' THEN 1  -- Independence Day
        WHEN STRFTIME('%m-%d', d) = '12-25' THEN 1  -- Christmas
        WHEN STRFTIME('%m-%d', d) = '11-11' THEN 1  -- Veterans Day
        ELSE 0
    END AS is_holiday
FROM dates;

-- ============================================================================
-- dim_device: Static device dimension
-- ============================================================================
INSERT INTO dim_device (device_type, device_category)
VALUES
    ('mobile', 'mobile'),
    ('tablet', 'mobile'),
    ('desktop', 'desktop'),
    ('web', 'desktop'),
    ('smart_speaker', 'other');

-- ============================================================================
-- dim_artist: Load from silver with derived columns
-- ============================================================================
INSERT INTO dim_artist (
    artist_id,
    name,
    genre,
    country,
    formed_year,
    years_active,
    monthly_listeners,
    popularity_tier
)
SELECT
    artist_id,
    name,
    genre,
    country,
    formed_year,
    -- Years active: 2025 - formed_year (NULL if formed_year is NULL)
    CASE
        WHEN formed_year IS NOT NULL THEN 2025 - formed_year
        ELSE NULL
    END AS years_active,
    monthly_listeners,
    -- Popularity tier based on monthly listeners
    CASE
        WHEN monthly_listeners < 10000 THEN 'emerging'
        WHEN monthly_listeners < 100000 THEN 'established'
        WHEN monthly_listeners < 1000000 THEN 'star'
        ELSE 'superstar'
    END AS popularity_tier
FROM silver.artists;

-- ============================================================================
-- dim_listener: Load from silver with derived columns
-- ============================================================================
INSERT INTO dim_listener (
    listener_id,
    email,
    username,
    full_name,
    birth_date,
    age_group,
    city,
    country,
    subscription_type,
    created_at,
    tenure_months
)
SELECT
    listener_id,
    email,
    username,
    first_name || ' ' || last_name AS full_name,
    birth_date,
    -- Age group based on birth_date (age as of 2025-01-01)
    CASE
        WHEN birth_date IS NULL THEN 'Unknown'
        WHEN (JULIANDAY('2025-01-01') - JULIANDAY(birth_date)) / 365.25 < 18 THEN 'Under 18'
        WHEN (JULIANDAY('2025-01-01') - JULIANDAY(birth_date)) / 365.25 < 25 THEN '18-24'
        WHEN (JULIANDAY('2025-01-01') - JULIANDAY(birth_date)) / 365.25 < 35 THEN '25-34'
        WHEN (JULIANDAY('2025-01-01') - JULIANDAY(birth_date)) / 365.25 < 45 THEN '35-44'
        WHEN (JULIANDAY('2025-01-01') - JULIANDAY(birth_date)) / 365.25 < 55 THEN '45-54'
        ELSE '55+'
    END AS age_group,
    city,
    country,
    subscription_type,
    created_at,
    -- Tenure in months from created_at to 2025-12-31
    CAST((JULIANDAY('2025-12-31') - JULIANDAY(created_at)) / 30.44 AS INTEGER) AS tenure_months
FROM silver.listeners;

-- ============================================================================
-- dim_track: Load from silver with derived columns
-- ============================================================================
-- Note: Requires dim_artist to be loaded first for artist_key lookup
INSERT INTO dim_track (
    track_id,
    title,
    artist_key,
    album,
    duration_ms,
    duration_bucket,
    genre,
    release_date,
    release_year,
    explicit
)
SELECT
    t.track_id,
    t.title,
    da.artist_key,
    t.album,
    t.duration_ms,
    -- Duration bucket
    CASE
        WHEN t.duration_ms < 180000 THEN 'short'    -- < 3 min
        WHEN t.duration_ms <= 300000 THEN 'medium'  -- 3-5 min
        ELSE 'long'                                  -- > 5 min
    END AS duration_bucket,
    t.genre,
    t.release_date,
    CAST(STRFTIME('%Y', t.release_date) AS INTEGER) AS release_year,
    t.explicit
FROM silver.tracks t
JOIN dim_artist da ON t.artist_id = da.artist_id;

-- Detach silver (will reattach for fact loading)
DETACH DATABASE silver;
