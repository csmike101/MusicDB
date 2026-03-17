# Music Streaming Data Modeling Workbook - Master Plan

## Overview

A tutorial-style workbook demonstrating **medallion architecture** (Raw → Bronze → Silver → Gold → Serving) using a music streaming domain in SQLite.

**Scale:** ~50 listeners, ~100 artists, ~1000 tracks, ~100k streams, 1 year of data (2025)

---

## Current Status

| Phase | Name | Status | Details |
|-------|------|--------|---------|
| 0 | Foundation | ✅ Complete | [plans/00_foundation.md](./plans/00_foundation.md) |
| 1 | Raw Layer | ✅ Complete | [plans/01_raw_layer.md](./plans/01_raw_layer.md) |
| 2 | Bronze Layer | ✅ Complete | [plans/02_bronze_layer.md](./plans/02_bronze_layer.md) |
| 3 | Silver Layer | 🔲 Next | [plans/03_silver_layer.md](./plans/03_silver_layer.md) |
| 4 | Gold Layer | 🔲 Pending | [plans/04_gold_layer.md](./plans/04_gold_layer.md) |
| 5 | Serving Layer | 🔲 Pending | [plans/05_serving_layer.md](./plans/05_serving_layer.md) |
| 6 | Integration | 🔲 Pending | [plans/06_integration.md](./plans/06_integration.md) |

---

## Project Structure

```
data_modeling/
├── CLAUDE.md                     # Project context for Claude Code
├── README.md                     # Workbook introduction
├── PLAN.md                       # This master plan
├── requirements.txt              # Python dependencies
│
├── plans/                        # Detailed phase documentation
│   ├── 00_foundation.md
│   ├── 01_raw_layer.md
│   ├── 02_bronze_layer.md
│   ├── 03_silver_layer.md
│   ├── 04_gold_layer.md
│   ├── 05_serving_layer.md
│   └── 06_integration.md
│
├── 01_raw/                       # Layer 1: Raw data generation
├── 02_bronze/                    # Layer 2: Staging
├── 03_silver/                    # Layer 3: Cleaned & normalized
├── 04_gold/                      # Layer 4: Dimensional model
├── 05_serving/                   # Layer 5: Analytics layer
└── scripts/                      # Pipeline utilities
```

---

## Phase Summaries

### Phase 0: Foundation ✅
Project setup, directory structure, CLAUDE.md, README.md, requirements.txt

### Phase 1: Raw Layer ✅
Data generator with ~50 listeners, ~100 artists, ~1000 tracks, ~100k streams. Intentional data quality issues for teaching.

### Phase 2: Bronze Layer ✅
Staging tables with TEXT columns, audit columns (_source_file, _loaded_at, _row_hash), no constraints.

### Phase 3: Silver Layer (Next)
3NF schema with proper types, constraints, deduplication, genre normalization, FK validation.

### Phase 4: Gold Layer
Star schema with dim_date, dim_listener, dim_artist, dim_track, dim_device, fact_streams, and aggregate tables.

### Phase 5: Serving Layer
Semantic views (v_stream_details, v_listener_summary, v_track_popularity) and Year-in-Review analytics queries.

### Phase 6: Integration
Pipeline orchestration (run_all.py), cross-layer validation, reset script.

---

## Data Quality Issues (Intentional)

For teaching purposes, raw data includes:
| Issue | Rate | Fields Affected |
|-------|------|-----------------|
| Duplicate records | ~1% | streams |
| Null values | ~15-20% | city, album, formed_year |
| Inconsistent casing | ~10% | genre |
| Invalid foreign keys | ~0.5% | track_id in streams |
| Whitespace issues | ~2% | name fields |
| Date format variations | ~2% | release_date |

---

## Process

Each phase is executed one at a time. After completing a phase, we pause for user review before proceeding. See individual phase files in `plans/` for detailed tasks, schemas, and verification steps.

---

## Dependencies

```
faker>=18.0.0
```

SQLite is included with Python standard library.
