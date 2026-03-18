# Phase 2: Bronze Page

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
| `02_bronze/bronze.db` | `bronze_listeners` | All columns including `_source_file`, `_loaded_at`, `_row_hash` |
| | `bronze_artists` | All columns including audit columns |
| | `bronze_tracks` | All columns including audit columns |
| | `bronze_streams` | All columns including audit columns |

**Verification before starting:**
```sql
-- Verify audit columns exist
SELECT _source_file, _loaded_at, _row_hash FROM bronze_streams LIMIT 1;
```

### Page Dependencies
| Dependency | Reason |
|------------|--------|
| Phase 1 (Setup + Home) | Requires `components/database.py`, app navigation, and config |

---

## Objectives

1. Add Bronze page to the app
2. Visualize raw ingestion stats and audit metadata
3. Implement duplicate detection visualization
4. Create interactive data explorer

---

## Prerequisites

- Phase 1 complete (app launches, database utilities working)
- `02_bronze/bronze.db` exists with data

---

## Tasks

### 2.1 Create Bronze Page

Add `pages/2_Bronze.py` to the app.

### 2.2 Update Navigation

Update `app.py` to include Bronze page:
```python
pg = st.navigation([
    st.Page("pages/1_Home.py", title="Home", icon="🏠"),
    st.Page("pages/2_Bronze.py", title="Bronze", icon="🥉"),
])
```

---

## Page Design

**Purpose**: Understand what raw data was ingested and track audit metadata.

**Narrative Connection**: "Bronze = Your Email Inbox" analogy—preserve everything, add timestamps.

**Database**: `02_bronze/bronze.db`

**Layout**:
```
┌─────────────────────────────────────────────────────────────────┐
│  Bronze Layer: Raw Staging                                      │
│  "Preserve exactly as received"                                 │
├─────────────────────────────────────────────────────────────────┤
│  [100,999]        [4]              [1]               [~1%]      │
│  Total Streams    Tables           Load Batch        Duplicates │
├─────────────────────────────────────────────────────────────────┤
│  Records by Source File             │  Duplicate Detection      │
│  [Stacked bar: listeners, artists,  │  [Pie chart: unique vs    │
│   tracks, streams]                  │   duplicate row hashes]   │
├─────────────────────────────────────┴───────────────────────────┤
│  Audit Timeline                                                 │
│  [Line chart: _loaded_at timestamps showing ingestion pattern]  │
├─────────────────────────────────────────────────────────────────┤
│  Raw Data Explorer                                              │
│  [Table selector: bronze_listeners | bronze_artists | ...]      │
│  [Row limit slider: 10-500]                                     │
│  [Filterable dataframe with all columns including audit cols]   │
│  [CSV Download button]                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

| Component | Type | Source | Business Question |
|-----------|------|--------|-------------------|
| Total streams | st.metric | COUNT(*) bronze_streams | How much data was ingested? |
| Table count | st.metric | Static (4) | How many source tables? |
| Load batches | st.metric | COUNT(DISTINCT _loaded_at) | How many load runs? |
| Duplicate rate | st.metric | Calculated % | How dirty is the source? |
| Records by source | Plotly stacked bar | GROUP BY _source_file | Which files were loaded? |
| Duplicate pie | Plotly pie | Unique vs duplicate hashes | Visual duplicate breakdown |
| Audit timeline | Plotly line | GROUP BY DATE(_loaded_at) | When was data loaded? |
| Table selector | st.selectbox | bronze_* tables | Choose table to explore |
| Row limit | st.slider | 10-500 | Control result size |
| Data explorer | st.dataframe | Selected table | Inspect raw records |
| Download button | st.download_button | DataFrame to CSV | Export data |

---

## Key Queries

### Record Counts
```sql
SELECT 'bronze_listeners' as table_name, COUNT(*) as rows FROM bronze_listeners
UNION ALL SELECT 'bronze_artists', COUNT(*) FROM bronze_artists
UNION ALL SELECT 'bronze_tracks', COUNT(*) FROM bronze_tracks
UNION ALL SELECT 'bronze_streams', COUNT(*) FROM bronze_streams;
```

### Duplicate Detection
```sql
SELECT
    COUNT(*) as total_rows,
    COUNT(DISTINCT _row_hash) as unique_rows,
    COUNT(*) - COUNT(DISTINCT _row_hash) as duplicates
FROM bronze_streams;
```

### Records by Source File
```sql
SELECT _source_file, COUNT(*) as records
FROM bronze_streams
GROUP BY _source_file;
```

### Load Batches
```sql
SELECT DISTINCT DATE(_loaded_at) as load_date, COUNT(*) as records
FROM bronze_streams
GROUP BY DATE(_loaded_at)
ORDER BY load_date;
```

### Data Explorer
```sql
SELECT * FROM {selected_table} LIMIT {row_limit};
```

---

## Verification Checklist

After implementation:

- [ ] Bronze page accessible from sidebar
- [ ] All 4 metrics display correct values
- [ ] Duplicate rate shows ~1% (approximately 999 duplicates)
- [ ] Records by source bar chart renders
- [ ] Duplicate pie chart shows unique vs duplicate
- [ ] Audit timeline shows load dates
- [ ] Table selector switches between 4 bronze tables
- [ ] Row limit slider works (10-500 range)
- [ ] Data explorer shows all columns including audit columns
- [ ] CSV download works for current table view
- [ ] Sidebar shows narrative callout about Bronze layer

---

## Sidebar Narrative

Add to sidebar:
```python
with st.sidebar:
    st.info(
        "**Bronze Layer**\n\n"
        "Like your email inbox—preserve everything exactly as received. "
        "All columns are TEXT, no constraints, no cleaning. "
        "Audit columns track where data came from and when."
    )
```

---

## Notes

- All bronze columns stored as TEXT (show this in data explorer)
- Highlight audit columns (`_source_file`, `_loaded_at`, `_row_hash`)
- Duplicate detection uses `_row_hash` for efficiency
