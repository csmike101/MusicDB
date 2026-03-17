# Data Modeling Walkthrough

## Your Mission

You've just joined **StreamFlow**, a music streaming startup. The company has been collecting listening data for a year, but it's a mess—duplicates, inconsistent formats, missing values. Your CEO wants a "Year in Review" feature (like Spotify Wrapped), but the data isn't ready for analytics.

Your job: **Transform raw event data into analytics-ready insights.**

This walkthrough guides you through building a complete data pipeline using **medallion architecture**—a proven pattern used by companies like Databricks, Netflix, and Spotify.

---

## The Problem

Open `01_raw/data/streams.csv` and look at the data. You'll notice:

```
stream_id,listener_id,track_id,streamed_at,duration_played_ms,device_type,shuffle_mode,offline_mode
str_000001,abc123...,trk_0042,2025-01-15T14:32:00,234000,mobile,True,False
str_000001,abc123...,trk_0042,2025-01-15T14:32:00,234000,mobile,True,False  <- duplicate!
str_000847,def456...,trk_1099,2025-03-22T09:15:00,180000,desktop,False,True  <- trk_1099 doesn't exist!
```

**Real-world data is messy.** Source systems have bugs. Networks drop packets. Users do unexpected things. Your pipeline must handle all of it gracefully.

---

## The Solution: Medallion Architecture

Instead of trying to clean everything at once, we use **progressive refinement**:

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│   Raw   │ -> │ Bronze  │ -> │ Silver  │ -> │  Gold   │ -> │ Serving │
│  Files  │    │ Staging │    │ Cleaned │    │  Star   │    │  Views  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
   JSON/CSV      All TEXT       3NF with       Dimensional    Analytics
   as-is         + audit       constraints     model          queries
```

Each layer has a single responsibility:

| Layer | Responsibility | Key Question |
|-------|---------------|--------------|
| **Raw** | Generate/receive source data | "What did the source system send us?" |
| **Bronze** | Preserve exactly as received | "Can we replay from source if needed?" |
| **Silver** | Clean and validate | "Is this data trustworthy?" |
| **Gold** | Optimize for analytics | "How do we answer business questions fast?" |
| **Serving** | Present to end users | "What insights can we deliver?" |

---

## Phase 0: Foundation

Before writing any code, we establish project structure and conventions.

**Why it matters:** Consistent naming, clear organization, and documented standards prevent chaos as the project grows. A team of 10 engineers needs to understand where things go.

**What we created:**
- `CLAUDE.md` - Coding conventions (SQL style, naming prefixes)
- `README.md` - Project overview for new team members
- Directory structure mirroring the medallion layers

**Key decision:** We chose SQLite for simplicity (no server required), but the patterns apply to any database—Postgres, Snowflake, Databricks, etc.

---

## Phase 1: Raw Layer

> **Folder:** `01_raw/`
> **Goal:** Generate realistic source data with intentional quality issues

### The Story

StreamFlow's backend systems export data in different formats:
- **User profiles** → JSON (from the authentication service)
- **Artist/track catalog** → JSON (from the content management system)
- **Listening events** → CSV (from the event streaming pipeline)

Each system has its own quirks. The event pipeline occasionally sends duplicates when retrying failed writes. The content system has inconsistent genre casing ("Rock" vs "rock" vs "ROCK"). Some users never filled in their city.

### What You'll Learn

1. **Data formats matter** - JSON preserves types (numbers, booleans, nulls); CSV treats everything as strings
2. **Quality issues are inevitable** - Plan for them, don't be surprised by them
3. **Scale affects design** - 100K events is small; imagine 100 billion

### Explore It Yourself

```bash
cd 01_raw
python generate_data.py

# Look at the data
head -5 data/streams.csv
cat data/listeners.json | python -m json.tool | head -30
```

**Question to ponder:** If you found a bug in the generator, how would you know which downstream data is affected?

> **Deep dive:** See `01_raw/README.md` for entity schemas and quality issue details.

---

## Phase 2: Bronze Layer

> **Folder:** `02_bronze/`
> **Database:** `bronze.db`
> **Goal:** Load raw data exactly as-is, adding only audit metadata

### The Story

Your first instinct might be to clean the data immediately. Resist it.

Imagine this scenario: Three months from now, a data scientist notices strange patterns in the analytics. They ask, "What did the raw data actually look like?" If you cleaned it on ingestion, that information is lost forever.

The bronze layer is your **safety net**—a faithful copy of source data with metadata that tells you where it came from and when.

### What You'll Learn

1. **Schema-on-read** - Store everything as TEXT; interpret types later
2. **Audit columns** - Track lineage with `_source_file`, `_loaded_at`, `_row_hash`
3. **No constraints** - Accept everything, even garbage; reject nothing
4. **Idempotent loads** - Running the load twice shouldn't create duplicates (truncate-and-load pattern)

### The Audit Column Pattern

Every bronze table has three extra columns:

```sql
_source_file TEXT,   -- "streams.csv" - which file did this come from?
_loaded_at TEXT,     -- "2025-01-15T10:30:00Z" - when did we load it?
_row_hash TEXT       -- "a1b2c3d4..." - MD5 hash for deduplication tracking
```

**Why `_row_hash`?** It lets us detect duplicates without comparing every column. Two rows with the same hash are identical. This becomes critical when you have billions of rows.

### Explore It Yourself

```bash
cd 02_bronze
python 02_load_data.py

# Query the bronze data
sqlite3 bronze.db "SELECT COUNT(*) FROM bronze_streams;"
sqlite3 bronze.db "SELECT * FROM bronze_streams LIMIT 3;"

# Find duplicates using row hash
sqlite3 bronze.db "
  SELECT _row_hash, COUNT(*) as occurrences
  FROM bronze_streams
  GROUP BY _row_hash
  HAVING COUNT(*) > 1
  LIMIT 5;
"
```

**Question to ponder:** Why do we store `duration_ms` as TEXT when it's clearly a number?

> **Deep dive:** See `02_bronze/README.md` for schema details and the full loading process.

---

## Phase 3: Silver Layer

> **Folder:** `03_silver/`
> **Database:** `silver.db`
> **Goal:** Clean, validate, and normalize data into trustworthy tables

### The Story

Now we clean. The silver layer is where data becomes **trustworthy**. After this layer, downstream consumers can rely on:
- No duplicate records
- Valid foreign key relationships
- Consistent data types
- Standardized formats (dates, casing, whitespace)

This is also where we **reject** bad data—but we don't delete it. We log it to `silver_rejected_records` so we can investigate later.

### What You'll Learn

1. **Type coercion** - TEXT → INTEGER, DATE, DATETIME
2. **Deduplication** - Using `ROW_NUMBER()` to keep first occurrence
3. **Referential integrity** - Rejecting streams that reference non-existent tracks
4. **Data standardization** - Genre casing, email lowercase, whitespace trimming
5. **Third Normal Form (3NF)** - Each table represents one entity

### The Transformation Pipeline

```
Bronze                          Silver
─────────────────────────────────────────────────
bronze_listeners (50 rows)  ->  listeners (50 rows)
  - Trim whitespace             - birth_date as DATE
  - Lowercase email             - Proper constraints

bronze_artists (100 rows)   ->  artists (100 rows)
  - Normalize genre casing      - "rock" -> "Rock"
  - Cast formed_year            - TEXT -> INTEGER

bronze_tracks (1000 rows)   ->  tracks (1000 rows)
  - Parse release_date          - Multiple formats -> ISO
  - Validate artist FK          - Reject orphans

bronze_streams (100,999)    ->  streams (99,493)
  - Remove duplicates           - 999 duplicates removed
  - Validate track FK           - 507 invalid refs rejected
  - Cast boolean strings        - "True" -> 1
```

### The Rejected Records Pattern

```sql
CREATE TABLE silver_rejected_records (
    source_table TEXT,      -- "streams"
    source_id TEXT,         -- "str_000847"
    rejection_reason TEXT,  -- "Invalid track_id: trk_1099"
    rejected_at DATETIME
);
```

**Why log rejections?** Because "the data disappeared" is never an acceptable answer. When someone asks why a stream isn't in the analytics, you can trace exactly what happened.

### Explore It Yourself

```bash
cd 03_silver

# See the transformation in action
sqlite3 silver.db "
  SELECT 'bronze' as layer, COUNT(*) as streams FROM bronze.bronze_streams
  UNION ALL
  SELECT 'silver', COUNT(*) FROM streams;
" --cmd "ATTACH '../02_bronze/bronze.db' AS bronze"

# Check genre normalization
sqlite3 silver.db "SELECT DISTINCT genre FROM artists ORDER BY genre;"

# Review rejected records
sqlite3 silver.db "
  SELECT source_table, COUNT(*) as rejected
  FROM silver_rejected_records
  GROUP BY source_table;
"
```

**Question to ponder:** A product manager asks, "Why did we lose 1,506 streams?" How do you explain the difference between bronze (100,999) and silver (99,493)?

> **Deep dive:** See `03_silver/README.md` for transformation logic and verification queries.

---

## Phase 4: Gold Layer

> **Folder:** `04_gold/`
> **Database:** `gold.db`
> **Goal:** Build a dimensional model (star schema) optimized for analytics

### The Story

Silver data is clean and trustworthy, but it's normalized—optimized for storage, not queries. Answering "What were the top 5 artists for each listener?" requires joining multiple tables and is slow at scale.

The gold layer **denormalizes** data into a star schema with:
- **Dimension tables** (`dim_listener`, `dim_artist`, `dim_track`, `dim_date`, `dim_device`)
- **Fact table** (`fact_streams`)
- **Aggregate tables** (pre-computed daily/monthly summaries)

### What You'll Learn

1. **Star schema design** - Facts in the center, dimensions around
2. **Surrogate keys** - Using integers instead of UUIDs for joins
3. **Derived attributes** - `age_group`, `popularity_tier`, `duration_bucket`
4. **Date dimensions** - Every analytics system needs one
5. **Pre-aggregation** - Trading storage for query speed

### The Star Schema

```
                    ┌─────────────┐
                    │  dim_date   │
                    │  (365 rows) │
                    └──────┬──────┘
                           │
┌─────────────┐     ┌──────┴──────┐     ┌─────────────┐
│ dim_listener│─────│ fact_streams│─────│  dim_track  │
│  (50 rows)  │     │ (99,493)    │     │ (1000 rows) │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                           │                   │
                    ┌──────┴──────┐     ┌──────┴──────┐
                    │ dim_device  │     │ dim_artist  │
                    │  (5 rows)   │     │ (100 rows)  │
                    └─────────────┘     └─────────────┘
```

### Derived Attributes

Instead of calculating age every query, we pre-compute `age_group`:

```sql
CASE
    WHEN age < 18 THEN 'Under 18'
    WHEN age BETWEEN 18 AND 24 THEN '18-24'
    WHEN age BETWEEN 25 AND 34 THEN '25-34'
    -- ...
END AS age_group
```

Similarly for `popularity_tier` (emerging → superstar) and `duration_bucket` (short/medium/long).

### Pre-aggregation: The Performance Secret

The `agg_daily_listener_streams` table pre-computes what would otherwise require scanning 99,493 fact rows:

```sql
-- Without pre-aggregation: scan all fact rows
SELECT listener_key, DATE(streamed_at), COUNT(*), SUM(duration_played_ms)
FROM fact_streams GROUP BY 1, 2;

-- With pre-aggregation: instant lookup
SELECT * FROM agg_daily_listener_streams WHERE listener_key = 42;
```

### Explore It Yourself

```bash
cd 04_gold

# See the star schema in action
sqlite3 gold.db "
  SELECT 'dim_date', COUNT(*) FROM dim_date
  UNION ALL SELECT 'dim_listener', COUNT(*) FROM dim_listener
  UNION ALL SELECT 'dim_artist', COUNT(*) FROM dim_artist
  UNION ALL SELECT 'dim_track', COUNT(*) FROM dim_track
  UNION ALL SELECT 'dim_device', COUNT(*) FROM dim_device
  UNION ALL SELECT 'fact_streams', COUNT(*) FROM fact_streams;
"

# Check derived attributes
sqlite3 gold.db "SELECT age_group, COUNT(*) FROM dim_listener GROUP BY age_group;"
sqlite3 gold.db "SELECT popularity_tier, COUNT(*) FROM dim_artist GROUP BY popularity_tier;"

# Query with star schema joins
sqlite3 gold.db "
  SELECT dl.full_name, da.name as artist, COUNT(*) as plays
  FROM fact_streams f
  JOIN dim_listener dl ON f.listener_key = dl.listener_key
  JOIN dim_track dt ON f.track_key = dt.track_key
  JOIN dim_artist da ON dt.artist_key = da.artist_key
  GROUP BY dl.listener_key, da.artist_key
  ORDER BY plays DESC
  LIMIT 10;
"
```

**Question to ponder:** Why do we use integer surrogate keys (`listener_key`) instead of the original UUIDs (`listener_id`)?

> **Deep dive:** See `04_gold/README.md` for complete schema details and verification queries.

---

## Phase 5: Serving Layer (Coming Later)

> **Folder:** `05_serving/`
> **Database:** `serving.db`
> **Goal:** Create analytics-ready views and Year-in-Review queries

### The Story

The gold layer is powerful but complex. Business users shouldn't need to know about surrogate keys or fact tables. The serving layer provides **semantic views** that hide complexity:

- `v_stream_details` - One row per stream with all context denormalized
- `v_listener_summary` - Aggregated stats per listener
- `v_top_artists_by_listener` - Pre-ranked for Year-in-Review

### What You'll Learn

1. **Semantic layers** - Business-friendly names and calculations
2. **Window functions** - `ROW_NUMBER()`, `RANK()` for top-N queries
3. **Year-in-Review patterns** - Top artists, genres, listening streaks

*Implementation coming in Phase 5...*

---

## Phase 6: Integration (Coming Later)

> **Folder:** `scripts/`
> **Goal:** Orchestrate the full pipeline with validation

### The Story

Running SQL files manually doesn't scale. The integration layer provides:
- `run_all.py` - Execute the entire pipeline with one command
- `validate.py` - Cross-layer integrity checks
- `reset.py` - Clean slate for re-running

### What You'll Learn

1. **Pipeline orchestration** - Dependency ordering
2. **Cross-layer validation** - Row count reconciliation
3. **Idempotent execution** - Safe to re-run anytime

*Implementation coming in Phase 6...*

---

## Key Takeaways

### 1. Progressive Refinement Works
Each layer does one thing well. Bronze preserves, Silver cleans, Gold optimizes. This separation makes debugging easier and changes safer.

### 2. Never Lose Data
Audit columns in Bronze and rejected records in Silver ensure you can always answer "what happened to this record?"

### 3. Schema Design Is Context-Dependent
- **Silver (3NF)**: Optimized for storage and consistency
- **Gold (Star)**: Optimized for query performance
- Neither is "better"—they serve different purposes

### 4. Data Quality Is Everyone's Problem
The generator intentionally creates messy data. In production, you'd have monitoring and alerts. But the cleaning patterns remain the same.

### 5. Start Simple, Scale Later
SQLite works for learning. The patterns transfer directly to Postgres, Snowflake, Databricks, or any modern data platform.

---

## What's Next?

1. **Explore the data** - Run the queries suggested in each section
2. **Break things** - Modify the generator, see what breaks downstream
3. **Add features** - Can you add a "listening streak" calculation?
4. **Scale up** - Try with 1M streams instead of 100K

Happy modeling!
