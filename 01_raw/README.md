# Layer 1: Raw Data

## Overview

The **Raw Layer** represents data as it arrives from source systems—unprocessed, unvalidated, and in its original format. In production systems, this might be event streams, API responses, file uploads, or database exports.

For this workbook, we **generate** synthetic data that simulates realistic source data, including intentional quality issues.

## Why Start with Raw Data?

Understanding raw data is critical because:

1. **Real data is messy** - Production data contains nulls, duplicates, inconsistencies
2. **Formats vary** - Different sources use different formats (JSON, CSV, XML)
3. **Schema drift** - Source schemas change over time
4. **Quality issues compound** - Problems not caught early propagate downstream

## Files in This Layer

| File | Format | Description |
|------|--------|-------------|
| `generate_data.py` | Python | Script to create synthetic data |
| `data/listeners.json` | JSON | User profile data |
| `data/artists.json` | JSON | Artist information |
| `data/tracks.json` | JSON | Track metadata |
| `data/streams.csv` | CSV | Listening event logs |

## Data Entities

### Listeners (JSON)
User profiles with demographics and subscription info.

```json
{
    "listener_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "musicfan42",
    "first_name": "Alex",
    "last_name": "Johnson",
    "birth_date": "1996-03-15",
    "city": "Austin",
    "country": "United States",
    "subscription_type": "premium",
    "created_at": "2024-03-15T10:30:00"
}
```

### Artists (JSON)
Musicians and bands with genre, origin, and popularity metrics.

```json
{
    "artist_id": "art_001",
    "name": "The Resonators",
    "genre": "Rock",
    "country": "United States",
    "formed_year": 2015,
    "monthly_listeners": 125000
}
```

### Tracks (JSON)
Songs with metadata including duration, album, and content flags.

```json
{
    "track_id": "trk_0001",
    "title": "Midnight Drive",
    "artist_id": "art_001",
    "album": "Night Moves",
    "duration_ms": 234000,
    "genre": "Rock",
    "release_date": "2023-05-12",
    "explicit": false
}
```

### Streams (CSV)
Event log of every time a user plays a track.

```csv
stream_id,listener_id,track_id,streamed_at,duration_played_ms,device_type,shuffle_mode,offline_mode
str_000001,550e8400...,trk_0001,2025-01-15T14:32:00,234000,mobile,False,False
str_000002,550e8400...,trk_0002,2025-01-15T14:36:00,120000,mobile,True,False
```

## Intentional Data Quality Issues

The generator creates realistic "dirty" data to practice cleaning:

| Issue | Example | Frequency |
|-------|---------|-----------|
| **Duplicate records** | Same stream_id appears twice | ~1% of streams |
| **Null values** | Missing city, album, formed_year | ~15-20% |
| **Inconsistent casing** | "Rock", "rock", "ROCK" | ~10% of genres |
| **Invalid foreign keys** | Stream references non-existent track | ~0.5% |
| **Whitespace issues** | "  Rock  " (leading/trailing spaces) | ~2% |
| **Date format variations** | "2025-01-15", "01/15/2025" | ~2% |

## Running the Generator

```bash
# Ensure venv is activated first
cd 01_raw
python generate_data.py
```

This creates all files in the `data/` subdirectory.

## Data Volume

| Entity | Count | Notes |
|--------|-------|-------|
| Listeners | 50 | UUID identifiers |
| Artists | 100 | Sequential IDs (art_001, art_002, ...) |
| Tracks | 1,000 | Sequential IDs (trk_0001, trk_0002, ...) |
| Streams | ~101,000 | Includes ~1% duplicates |

The stream data covers a full year (2025) with realistic listening patterns:
- More streams on weekends
- Peak hours: morning commute, lunch, evenings
- Premium users stream more frequently

## Key Concepts

### Why JSON for Entities?
JSON demonstrates handling semi-structured data with nested fields and proper types (booleans, integers, nulls). It's common for data from web APIs and document databases.

### Why CSV for Events?
CSV is ubiquitous for high-volume log data and bulk exports. It's simple but lacks schema enforcement—everything is a string.

### Why Include Bad Data?
Real data pipelines must handle imperfect data. Learning to identify and address quality issues is essential for building robust pipelines.

### Duration in Milliseconds?
Streaming APIs typically report duration in milliseconds for precision. This creates a learning opportunity for unit conversion in later layers.

## Real-World Context

In production environments, raw data comes from many sources:

| Source Type | Example | Typical Format | Challenges |
|-------------|---------|----------------|------------|
| **Event streams** | Kafka, Kinesis | JSON, Avro | High volume, ordering, duplicates |
| **API exports** | REST APIs | JSON | Rate limits, pagination, schema changes |
| **Database dumps** | MySQL, Postgres | CSV, Parquet | Large files, encoding issues |
| **File uploads** | User submissions | CSV, Excel | Unpredictable quality |
| **Third-party feeds** | Partner data | Various | No control over format |

Our synthetic generator simulates the challenges you'd face with real sources, just at a smaller scale.

## Common Pitfalls

**1. Assuming data is clean**
> "The API documentation says this field is required."

Reality: Documentation lies. Always validate.

**2. Ignoring edge cases**
> "Who would have an empty string for their name?"

Reality: Someone will. Handle it.

**3. Hardcoding formats**
> "Dates are always YYYY-MM-DD."

Reality: Until they're not. The generator includes date format variations to teach this lesson.

**4. Not tracking data lineage**
> "Where did this weird value come from?"

Reality: Without audit columns (added in Bronze), you can't trace issues back to their source.

## Exploration Exercises

Try these queries after generating data:

```bash
# Count records in each file
wc -l data/streams.csv
cat data/listeners.json | python -c "import json,sys; print(len(json.load(sys.stdin)))"

# Find duplicate stream IDs
cut -d',' -f1 data/streams.csv | sort | uniq -d | head -5

# Check genre casing variations
cat data/artists.json | python -c "
import json, sys
data = json.load(sys.stdin)
genres = set(a['genre'] for a in data)
print(sorted(genres))
"
```

## Next Steps

After generating raw data, proceed to **02_bronze/** to load it into staging tables.
