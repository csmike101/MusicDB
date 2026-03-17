# Phase 2: Raw Layer

**Status:** Complete

---

## Goal

Generate realistic music streaming data with intentional data quality issues for teaching data cleansing concepts.

---

## Files to Create

| File | Purpose |
|------|---------|
| `00_raw/generate_data.py` | Main data generation script |
| `00_raw/data/listeners.json` | ~50 listener profiles |
| `00_raw/data/artists.json` | ~100 artist records |
| `00_raw/data/tracks.json` | ~1000 track records |
| `00_raw/data/streams.csv` | ~100k stream events |

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
# 00_raw/generate_data.py

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

- [x] Create `generate_data.py` script
- [x] Implement listener generation with nullable city
- [x] Implement artist generation with genre casing issues
- [x] Implement track generation with FK issues and date variations
- [x] Implement stream generation with duplicates
- [x] Add whitespace issues to name fields
- [x] Generate all data files
- [x] Verify data volumes match targets

---

## Verification

- [x] `listeners.json` contains ~50 records
- [x] `artists.json` contains ~100 records
- [x] `tracks.json` contains ~1000 records
- [x] `streams.csv` contains ~100k records
- [x] Duplicate streams exist (~1%)
- [x] Null values present in optional fields
- [x] Genre casing inconsistencies present
- [x] Some invalid track_ids in streams
