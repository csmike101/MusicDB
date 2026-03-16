# Layer 0: Raw Data

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

| File | Description |
|------|-------------|
| `generate_data.py` | Python script to create synthetic data |
| `data/listeners.json` | User profile data (JSON format) |
| `data/artists.csv` | Artist information (CSV format) |
| `data/tracks.csv` | Track metadata (CSV format) |
| `data/streams.csv` | Listening event logs (CSV format) |

## Data Entities

### Listeners (JSON)
User profiles with demographics and subscription info.

```json
{
    "listener_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "musicfan42",
    "age": 28,
    "country": "United States",
    "city": "Austin",
    "signup_date": "2024-03-15",
    "subscription_tier": "premium"
}
```

### Artists (CSV)
Musicians and bands with genre and origin.

```csv
artist_id,name,genre,country,formed_year
art_001,The Resonators,Rock,United States,2015
art_002,Luna Eclipse,Electronic,Sweden,2018
```

### Tracks (CSV)
Songs with metadata including duration and album.

```csv
track_id,title,artist_id,album,duration_seconds,release_date,genre
trk_0001,Midnight Drive,art_001,Night Moves,234,2023-05-12,Rock
trk_0002,Neon Dreams,art_002,,187,2024-01-20,Electronic
```

### Streams (CSV)
Event log of every time a user plays a track.

```csv
stream_id,listener_id,track_id,streamed_at,duration_listened,platform
str_00001,550e8400...,trk_0001,2025-01-15T14:32:00,234,mobile_ios
str_00002,550e8400...,trk_0002,2025-01-15T14:36:00,120,mobile_ios
```

## Intentional Data Quality Issues

The generator creates realistic "dirty" data to practice cleaning:

| Issue | Example | Frequency |
|-------|---------|-----------|
| **Duplicate records** | Same stream_id appears twice | ~1% of streams |
| **Null values** | Missing city, album | ~10-20% |
| **Inconsistent casing** | "Rock", "rock", "ROCK" | ~5% of genres |
| **Invalid foreign keys** | stream references non-existent track | ~0.5% |
| **Whitespace issues** | "  Rock  " (leading/trailing spaces) | ~2% |
| **Date format variations** | "2025-01-15", "01/15/2025" | ~2% |

## Running the Generator

```bash
cd 00_raw
python generate_data.py
```

This creates all files in the `data/` subdirectory.

## Data Volume

| Entity | Approximate Count |
|--------|------------------|
| Listeners | 50 |
| Artists | 100 |
| Tracks | 1,000 |
| Streams | 100,000 |

The stream data covers a full year (2025) with realistic listening patterns:
- More streams on weekends
- Peak hours in evenings
- Premium users stream more

## Key Concepts

### Why JSON for Listeners?
JSON demonstrates handling semi-structured data. It's common for user profile data from web APIs.

### Why CSV for Events?
CSV is ubiquitous for log data and bulk exports. It's simple but lacks schema enforcement.

### Why Include Bad Data?
Real data pipelines must handle imperfect data. Learning to identify and address quality issues is essential.

## Next Steps

After generating raw data, proceed to **01_bronze/** to load it into staging tables.
