# Phase 3: Silver Page

## Dependencies

### Infrastructure Dependencies
| Component | Location | Built In |
|-----------|----------|----------|
| Database utilities | `components/database.py` | Phase 1 |
| App navigation | `app.py` | Phase 1 |
| Streamlit config | `.streamlit/config.toml` | Phase 1 |

### Data Dependencies
| Database | Tables | Required Columns |
|----------|--------|------------------|
| `03_silver/silver.db` | `listeners` | All columns |
| | `artists` | `artist_id`, `genre` |
| | `tracks` | All columns |
| | `streams` | All columns |
| | `silver_rejected_records` | `source_table`, `source_id`, `rejection_reason`, `rejected_at` |
| `02_bronze/bronze.db` | `bronze_streams` | `COUNT(*)` for comparison |
| | `bronze_artists` | `genre` for before/after comparison |

**Verification before starting:**
```sql
-- Verify rejected records table exists and has data
SELECT COUNT(*) FROM silver_rejected_records;

-- Verify genre normalization happened
SELECT DISTINCT genre FROM artists ORDER BY genre;
```

### Page Dependencies
| Dependency | Reason |
|------------|--------|
| Phase 1 (Setup + Home) | Requires shared infrastructure |
| Phase 2 (Bronze) | Not strictly required, but establishes page pattern |

---

## Objectives

1. Add Silver page to the app
2. Visualize data quality improvements (before/after)
3. Show rejection summaries and reasons
4. Display data quality gauges

---

## Prerequisites

- Phase 2 complete (Bronze page working)
- `03_silver/silver.db` exists with data
- `02_bronze/bronze.db` accessible for comparison

---

## Tasks

### 3.1 Create Silver Page

Add `pages/3_Silver.py` to the app.

### 3.2 Update Navigation

Update `app.py` to include Silver page:
```python
pg = st.navigation([
    st.Page("pages/1_Home.py", title="Home", icon="🏠"),
    st.Page("pages/2_Bronze.py", title="Bronze", icon="🥉"),
    st.Page("pages/3_Silver.py", title="Silver", icon="🥈"),
])
```

---

## Page Design

**Purpose**: Show data quality improvements and rejection summaries.

**Narrative Connection**: "Silver = Quality Control on a Production Line"—inspect, validate, reject defects.

**Database**: `03_silver/silver.db` (+ `02_bronze/bronze.db` for comparison)

**Layout**:
```
┌─────────────────────────────────────────────────────────────────┐
│  Silver Layer: Cleaned & Normalized                             │
│  "Is this data trustworthy?"                                    │
├─────────────────────────────────────────────────────────────────┤
│  [99,493]         [1,506]          [0]               [12]       │
│  Clean Streams    Rejected         Duplicates Left   Genres     │
├─────────────────────────────────────────────────────────────────┤
│  Bronze → Silver Comparison         │  Rejection Breakdown      │
│  [Grouped bar: before/after counts  │  [Horizontal bar: reasons │
│   per table]                        │   with counts]            │
├─────────────────────────────────────┴───────────────────────────┤
│  Data Quality Scores                                            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Dedup Rate   │ │ FK Valid     │ │ Overall      │            │
│  │ [Gauge 99%]  │ │ [Gauge 99%]  │ │ [Gauge 98%]  │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
├─────────────────────────────────────────────────────────────────┤
│  Genre Normalization Example        │  Rejected Records         │
│  Before: Rock, rock, ROCK, RoCk    │  [Filterable table:       │
│  After:  Rock (all unified)         │   source, id, reason]     │
│                                     │  [CSV Download]           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

| Component | Type | Source | Business Question |
|-----------|------|--------|-------------------|
| Clean streams | st.metric | COUNT(*) streams | How much survived? |
| Rejected count | st.metric | COUNT(*) silver_rejected_records | How much rejected? |
| Duplicates remaining | st.metric | Should be 0 | Is dedup complete? |
| Distinct genres | st.metric | COUNT(DISTINCT genre) | Is casing normalized? |
| Before/after bar | Plotly grouped bar | Bronze vs Silver counts | What changed? |
| Rejection reasons | Plotly horizontal bar | GROUP BY rejection_reason | Why rejected? |
| Dedup gauge | Plotly gauge | (1 - dups/total) * 100 | Deduplication rate |
| FK validity gauge | Plotly gauge | (valid/total) * 100 | FK integrity rate |
| Overall quality gauge | Plotly gauge | Combined score | Overall quality |
| Genre comparison | st.columns + code | Before/after examples | Normalization demo |
| Rejected records | st.dataframe | silver_rejected_records | Drill into rejections |
| Download button | st.download_button | Rejected records CSV | Export rejections |

---

## Key Queries

### Clean Record Counts (Silver)
```sql
SELECT 'listeners' as table_name, COUNT(*) as rows FROM listeners
UNION ALL SELECT 'artists', COUNT(*) FROM artists
UNION ALL SELECT 'tracks', COUNT(*) FROM tracks
UNION ALL SELECT 'streams', COUNT(*) FROM streams;
```

### Rejected Record Summary
```sql
SELECT
    source_table,
    rejection_reason,
    COUNT(*) as count
FROM silver_rejected_records
GROUP BY source_table, rejection_reason
ORDER BY count DESC;
```

### Rejection Counts by Reason
```sql
SELECT rejection_reason, COUNT(*) as count
FROM silver_rejected_records
GROUP BY rejection_reason
ORDER BY count DESC;
```

### Genre Normalization Check
```sql
-- Silver (should be normalized)
SELECT DISTINCT genre FROM artists ORDER BY genre;
```

### Bronze Genre Variants (for comparison)
```sql
-- Bronze (has variants)
SELECT genre, COUNT(*) as count
FROM bronze_artists
GROUP BY genre
ORDER BY count DESC;
```

### Distinct Genre Count
```sql
SELECT COUNT(DISTINCT genre) as genres FROM artists;
```

### Rejected Records Detail
```sql
SELECT source_table, source_id, rejection_reason, rejected_at
FROM silver_rejected_records
ORDER BY rejected_at DESC
LIMIT 100;
```

---

## Quality Score Calculations

### Deduplication Rate
```python
bronze_streams = query_bronze("SELECT COUNT(*) FROM bronze_streams")
bronze_unique = query_bronze("SELECT COUNT(DISTINCT _row_hash) FROM bronze_streams")
dedup_rate = (bronze_unique / bronze_streams) * 100  # ~99%
```

### FK Validity Rate
```python
total_bronze_streams = query_bronze("SELECT COUNT(*) FROM bronze_streams")
rejected_fk = query_silver("""
    SELECT COUNT(*) FROM silver_rejected_records
    WHERE rejection_reason LIKE '%track_id%'
""")
fk_valid_rate = ((total_bronze_streams - rejected_fk) / total_bronze_streams) * 100
```

### Overall Quality Score
```python
silver_streams = query_silver("SELECT COUNT(*) FROM streams")
bronze_streams = query_bronze("SELECT COUNT(*) FROM bronze_streams")
overall = (silver_streams / bronze_streams) * 100  # ~98.5%
```

---

## Verification Checklist

After implementation:

- [ ] Silver page accessible from sidebar
- [ ] Clean streams metric shows ~99,493
- [ ] Rejected count shows ~1,506
- [ ] Duplicates remaining shows 0
- [ ] Distinct genres shows 12 (or actual count)
- [ ] Before/after bar chart shows all 4 tables
- [ ] Rejection reasons bar shows breakdown (FK invalid, duplicates)
- [ ] All 3 gauges render with correct percentages
- [ ] Genre comparison shows before/after examples
- [ ] Rejected records table is filterable
- [ ] CSV download works for rejected records
- [ ] Sidebar shows narrative callout about Silver layer

---

## Sidebar Narrative

```python
with st.sidebar:
    st.info(
        "**Silver Layer**\n\n"
        "Quality control checkpoint. Data is:\n"
        "- Deduplicated\n"
        "- Type-cast (TEXT → proper types)\n"
        "- FK-validated\n"
        "- Normalized (genre casing)\n\n"
        "Rejected records are logged, not deleted."
    )
```

---

## Notes

- Requires connecting to BOTH bronze.db and silver.db for comparisons
- Gauge charts use Plotly indicator with mode="gauge+number"
- Genre comparison can use st.code() to show before/after
