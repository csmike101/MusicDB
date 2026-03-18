# Phase 4: Gold Page

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
| `04_gold/gold.db` | `dim_date` | `date_key`, `full_date`, `year`, `month`, `day_name`, `is_weekend` |
| | `dim_listener` | `listener_key`, `listener_id`, `full_name`, `age_group`, `tenure_months` |
| | `dim_artist` | `artist_key`, `artist_id`, `name`, `genre`, `popularity_tier`, `years_active` |
| | `dim_track` | `track_key`, `track_id`, `title`, `artist_key`, `duration_bucket`, `release_year` |
| | `dim_device` | `device_key`, `device_type`, `device_category` |
| | `fact_streams` | All columns |
| | `agg_daily_listener_streams` | All columns |
| | `agg_daily_track_streams` | All columns |
| | `agg_monthly_genre_streams` | All columns |

**Verification before starting:**
```sql
-- Verify all dimension tables exist
SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'dim_%';

-- Verify derived columns exist
SELECT DISTINCT age_group FROM dim_listener;
SELECT DISTINCT popularity_tier FROM dim_artist;
SELECT DISTINCT duration_bucket FROM dim_track;

-- Verify aggregate tables exist and have data
SELECT COUNT(*) FROM agg_daily_listener_streams;
```

### Page Dependencies
| Dependency | Reason |
|------------|--------|
| Phase 1 (Setup + Home) | Requires shared infrastructure |

---

## Objectives

1. Add Gold page to the app
2. Visualize star schema structure
3. Show dimension distributions (derived attributes)
4. Create aggregate table explorer

---

## Prerequisites

- Phase 3 complete (Silver page working)
- `04_gold/gold.db` exists with data

---

## Tasks

### 4.1 Create Gold Page

Add `pages/4_Gold.py` to the app.

### 4.2 Update Navigation

Update `app.py` to include Gold page:
```python
pg = st.navigation([
    st.Page("pages/1_Home.py", title="Home", icon="🏠"),
    st.Page("pages/2_Bronze.py", title="Bronze", icon="🥉"),
    st.Page("pages/3_Silver.py", title="Silver", icon="🥈"),
    st.Page("pages/4_Gold.py", title="Gold", icon="🥇"),
])
```

---

## Page Design

**Purpose**: Explore the star schema structure and pre-aggregated summaries.

**Narrative Connection**: "Star Schema = A Well-Organized Report" + "Pre-aggregation = Pre-cooked Meals"

**Database**: `04_gold/gold.db`

**Layout**:
```
┌─────────────────────────────────────────────────────────────────┐
│  Gold Layer: Dimensional Model                                  │
│  "Optimized for analytics"                                      │
├─────────────────────────────────────────────────────────────────┤
│  [99,493]         [5]              [3]               [1,520]    │
│  Fact Rows        Dimensions       Aggregates        Dim Rows   │
├─────────────────────────────────────────────────────────────────┤
│  Star Schema Diagram                │  Dimension Sizes          │
│  [Visual showing fact_streams       │  [Horizontal bar:         │
│   connected to 5 dimensions]        │   dim_* row counts]       │
├─────────────────────────────────────┴───────────────────────────┤
│  Derived Attributes                                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Age Groups   │ │ Pop. Tiers   │ │ Duration     │            │
│  │ [Pie chart]  │ │ [Pie chart]  │ │ [Pie chart]  │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
├─────────────────────────────────────────────────────────────────┤
│  Aggregate Tables                                               │
│  [Tabs: Daily Listener | Daily Track | Monthly Genre]           │
│  [Summary stats for selected aggregate]                         │
│  [Sample data table + CSV download]                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

| Component | Type | Source | Business Question |
|-----------|------|--------|-------------------|
| Fact rows | st.metric | COUNT(*) fact_streams | How many events? |
| Dimension count | st.metric | Static (5) | How many dimensions? |
| Aggregate count | st.metric | Static (3) | What's pre-computed? |
| Total dim rows | st.metric | SUM of dim counts | Model size? |
| Star schema diagram | Custom/Plotly | Static visualization | How are tables related? |
| Dimension sizes | Plotly horizontal bar | COUNT(*) per dim_* | Dimension cardinality? |
| Age group pie | Plotly pie | dim_listener.age_group | Listener demographics? |
| Popularity tier pie | Plotly pie | dim_artist.popularity_tier | Artist distribution? |
| Duration bucket pie | Plotly pie | dim_track.duration_bucket | Track lengths? |
| Aggregate tabs | st.tabs | 3 tabs | Switch between aggregates |
| Aggregate stats | st.metric | COUNT, date range | Aggregate summary |
| Aggregate sample | st.dataframe | LIMIT 100 | Preview data |
| Download button | st.download_button | Full aggregate CSV | Export |

---

## Key Queries

### Dimension Row Counts
```sql
SELECT 'dim_date' as dimension, COUNT(*) as rows FROM dim_date
UNION ALL SELECT 'dim_listener', COUNT(*) FROM dim_listener
UNION ALL SELECT 'dim_artist', COUNT(*) FROM dim_artist
UNION ALL SELECT 'dim_track', COUNT(*) FROM dim_track
UNION ALL SELECT 'dim_device', COUNT(*) FROM dim_device;
```

### Fact Table Count
```sql
SELECT COUNT(*) as rows FROM fact_streams;
```

### Age Group Distribution
```sql
SELECT age_group, COUNT(*) as count
FROM dim_listener
GROUP BY age_group
ORDER BY count DESC;
```

### Popularity Tier Distribution
```sql
SELECT popularity_tier, COUNT(*) as count
FROM dim_artist
GROUP BY popularity_tier
ORDER BY count DESC;
```

### Duration Bucket Distribution
```sql
SELECT duration_bucket, COUNT(*) as count
FROM dim_track
GROUP BY duration_bucket
ORDER BY count DESC;
```

### Aggregate Table Samples
```sql
-- Daily Listener Streams
SELECT * FROM agg_daily_listener_streams LIMIT 100;

-- Daily Track Streams
SELECT * FROM agg_daily_track_streams LIMIT 100;

-- Monthly Genre Streams
SELECT * FROM agg_monthly_genre_streams LIMIT 100;
```

### Aggregate Stats
```sql
-- Daily Listener Streams stats
SELECT
    COUNT(*) as total_rows,
    COUNT(DISTINCT listener_key) as unique_listeners,
    COUNT(DISTINCT date_key) as unique_dates,
    SUM(stream_count) as total_streams
FROM agg_daily_listener_streams;
```

---

## Star Schema Visualization

Create a simple visual representation:

```python
st.markdown("""
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
""")
```

Or use Plotly network graph for an interactive version.

---

## Derived Attributes Reference

### Age Groups (dim_listener.age_group)
| Group | Criteria |
|-------|----------|
| Under 18 | age < 18 |
| 18-24 | 18 <= age <= 24 |
| 25-34 | 25 <= age <= 34 |
| 35-44 | 35 <= age <= 44 |
| 45-54 | 45 <= age <= 54 |
| 55+ | age >= 55 |

### Popularity Tiers (dim_artist.popularity_tier)
| Tier | Criteria (monthly_listeners) |
|------|------------------------------|
| emerging | < 10,000 |
| established | 10,000 - 99,999 |
| star | 100,000 - 999,999 |
| superstar | >= 1,000,000 |

### Duration Buckets (dim_track.duration_bucket)
| Bucket | Criteria |
|--------|----------|
| short | < 3 minutes |
| medium | 3-5 minutes |
| long | > 5 minutes |

---

## Verification Checklist

After implementation:

- [ ] Gold page accessible from sidebar
- [ ] Fact rows metric shows ~99,493
- [ ] Dimension count shows 5
- [ ] Aggregate count shows 3
- [ ] Total dimension rows shows sum (~1,520)
- [ ] Star schema diagram renders (ASCII or Plotly)
- [ ] Dimension sizes bar chart shows all 5 dims
- [ ] Age group pie chart renders correctly
- [ ] Popularity tier pie chart renders correctly
- [ ] Duration bucket pie chart renders correctly
- [ ] Aggregate tabs switch between 3 aggregates
- [ ] Each aggregate shows summary stats
- [ ] Sample data table displays for each aggregate
- [ ] CSV download works for aggregates
- [ ] Sidebar shows narrative callout about Gold layer

---

## Sidebar Narrative

```python
with st.sidebar:
    st.info(
        "**Gold Layer**\n\n"
        "Star schema optimized for analytics:\n"
        "- **Fact table**: Events (streams)\n"
        "- **Dimensions**: Context (who, what, when)\n"
        "- **Aggregates**: Pre-computed summaries\n\n"
        "Surrogate keys (integers) for fast joins."
    )
```

---

## Notes

- Star schema diagram can be ASCII art in st.code() or Plotly network
- Pie charts should use consistent color schemes
- Aggregate tabs use st.tabs() for clean switching
- Consider adding a "Query Builder" for advanced users (v1.2)
