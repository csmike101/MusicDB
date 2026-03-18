# Phase 1: Raw Layer

**Status:** Complete

---

## Goal

Generate realistic music streaming data with intentional data quality issues for teaching data cleansing concepts.

---

## Files to Create

| File | Format | Purpose |
|------|--------|---------|
| `01_raw/generate_data.py` | Python | Main data generation script |
| `01_raw/data/listeners.json` | JSON | ~50 listener profiles |
| `01_raw/data/artists.json` | JSON | ~100 artist records |
| `01_raw/data/tracks.json` | JSON | ~1000 track records |
| `01_raw/data/streams.csv` | CSV | ~100k stream events |

---

## Entity Schemas

### Listeners (JSON)
```json
{
  "listener_id": "uuid",
  "email": "string",
  "username": "string",
  "first_name": "string",
  "last_name": "string",
  "birth_date": "YYYY-MM-DD",
  "city": "string (nullable)",
  "country": "string",
  "subscription_type": "free|premium",
  "created_at": "ISO8601 timestamp"
}
```

### Artists (JSON)
```json
{
  "artist_id": "uuid",
  "name": "string",
  "genre": "string (inconsistent casing)",
  "country": "string",
  "formed_year": "integer (nullable)",
  "monthly_listeners": "integer"
}
```

### Tracks (JSON)
```json
{
  "track_id": "uuid",
  "title": "string",
  "artist_id": "uuid (some invalid)",
  "album": "string (nullable)",
  "duration_ms": "integer",
  "genre": "string",
  "release_date": "various formats",
  "explicit": "boolean"
}
```

### Streams (CSV)
```
stream_id,listener_id,track_id,streamed_at,duration_played_ms,device_type,shuffle_mode,offline_mode
```

---

## Data Quality Issues (Intentional)

| Issue | Rate | Fields Affected |
|-------|------|-----------------|
| Duplicate records | ~1% | streams |
| Null values | ~15-20% | city, album, formed_year |
| Inconsistent casing | ~10% | genre |
| Invalid foreign keys | ~0.5% | track_id in streams |
| Whitespace issues | ~2% | name fields |
| Date format variations | ~2% | release_date |

---

## Generator Design

```python
# 01_raw/generate_data.py

import json
import csv
import random
import uuid
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

# Configuration
NUM_LISTENERS = 50
NUM_ARTISTS = 100
NUM_TRACKS = 1000
NUM_STREAMS = 100000
YEAR = 2025

# Quality issue rates
DUPLICATE_RATE = 0.01
NULL_RATE = 0.15
CASE_VARIATION_RATE = 0.10
INVALID_FK_RATE = 0.005
WHITESPACE_RATE = 0.02
DATE_FORMAT_VARIATION_RATE = 0.02

GENRES = ["Rock", "Pop", "Hip Hop", "Jazz", "Classical", "Electronic",
          "R&B", "Country", "Metal", "Folk", "Blues", "Reggae"]

SUBSCRIPTION_TYPES = ["free", "premium"]
DEVICE_TYPES = ["mobile", "desktop", "tablet", "smart_speaker", "web"]
```

---

## Tasks

- [x] Update `generate_data.py` script with revised schema
- [x] Implement listener generation with birth_date, first_name, last_name
- [x] Implement artist generation as JSON with monthly_listeners
- [x] Implement track generation as JSON with duration_ms, explicit
- [x] Implement stream generation with device_type, shuffle_mode, offline_mode
- [x] Add all intentional data quality issues
- [x] Generate all data files
- [x] Verify data volumes and quality issues

---

## Expected Row Counts

| File | Expected | Tolerance | Notes |
|------|----------|-----------|-------|
| `listeners.json` | 50 | exact | `NUM_LISTENERS` config |
| `artists.json` | 100 | exact | `NUM_ARTISTS` config |
| `tracks.json` | 1,000 | exact | `NUM_TRACKS` config |
| `streams.csv` | ~101,000 | ±1% | `NUM_STREAMS` + ~1% duplicates |

### Data Quality Issues (Expected Rates)

| Issue | Expected Rate | Actual |
|-------|---------------|--------|
| Duplicate streams | ~1% (~1,000) | 999 |
| Null cities | ~15-20% | 22% |
| Null formed_year | ~15% | 14% |
| Null albums | ~15-20% | 19.6% |
| Invalid track_ids | ~0.5% (~500) | 508 |
| Genre casing variations | ~10% | Present (20 unique) |

### Verification Commands

```bash
# Count records in each file
wc -l 01_raw/data/streams.csv
python -c "import json; print(len(json.load(open('01_raw/data/listeners.json'))))"
python -c "import json; print(len(json.load(open('01_raw/data/artists.json'))))"
python -c "import json; print(len(json.load(open('01_raw/data/tracks.json'))))"
```

---

## Verification

- [x] `listeners.json` contains 50 records with birth_date field
- [x] `artists.json` contains 100 records with monthly_listeners
- [x] `tracks.json` contains 1000 records with duration_ms and explicit
- [x] `streams.csv` contains 100,999 records with shuffle_mode, offline_mode
- [x] Duplicate streams: 999 (0.99%)
- [x] Null values: 22% null cities, 14% null formed_year, 19.6% null albums
- [x] Genre casing inconsistencies present (20 unique case-sensitive genres)
- [x] Invalid track_ids: 508 (0.50%)
