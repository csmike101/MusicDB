# Phase 5: Serving Page

## Dependencies

### Infrastructure Dependencies
| Component | Location | Built In |
|-----------|----------|----------|
| Database utilities | `components/database.py` | Phase 1 |
| App navigation | `app.py` | Phase 1 |
| Streamlit config | `.streamlit/config.toml` | Phase 1 |
| Session state pattern | N/A (Streamlit built-in) | N/A |

### Data Dependencies
| Database | Views | Required Columns |
|----------|-------|------------------|
| `04_gold/gold.db` | `v_stream_details` | All columns |
| | `v_listener_summary` | All columns |
| | `v_track_popularity` | `rank`, `track_title`, `artist_name`, `genre`, `total_streams`, `unique_listeners` |
| | `v_artist_popularity` | `rank`, `artist_name`, `genre`, `total_streams`, `unique_listeners` |
| | `v_genre_trends` | `month`, `month_name`, `genre`, `stream_count`, `month_share_pct` |
| | `v_daily_platform_stats` | `full_date`, `total_streams`, `unique_listeners`, `total_hours` |
| | `v_top_artists_by_listener` | `listener_id`, `rank`, `artist_name`, `total_minutes` |
| | `v_top_tracks_by_listener` | `listener_id`, `rank`, `track_title`, `artist_name`, `play_count` |
| | `v_top_genre_by_listener` | `listener_id`, `genre`, `stream_count` |
| | `v_listening_personality` | `listener_id`, `listening_personality`, `unique_artists`, `unique_genres` |
| | `v_monthly_trends_by_listener` | `listener_id`, `month`, `month_name`, `total_hours` |
| | `v_peak_listening_times` | `listener_id`, `day_of_week`, `hour_of_day`, `stream_count` |
| | `v_weekday_vs_weekend` | `listener_id`, `weekday_streams`, `weekend_streams`, `weekend_pct` |
| | `v_discovery_stats` | `listener_id`, `q1_new_artists`, `q2_new_artists`, `q3_new_artists`, `q4_new_artists` |
| | `v_year_in_review_summary` | `listener_id`, `listener_name`, `total_hours`, `unique_artists`, `listening_percentile` |

**Verification before starting:**
```sql
-- Verify all 15 serving views exist
SELECT name FROM sqlite_master
WHERE type='view' AND name LIKE 'v_%'
ORDER BY name;

-- Expected: 15 views
-- v_artist_popularity, v_daily_platform_stats, v_discovery_stats,
-- v_genre_trends, v_listener_summary, v_listening_personality,
-- v_monthly_trends_by_listener, v_peak_listening_times, v_stream_details,
-- v_top_artists_by_listener, v_top_genre_by_listener, v_top_tracks_by_listener,
-- v_track_popularity, v_weekday_vs_weekend, v_year_in_review_summary

-- Verify Year-in-Review summary has data
SELECT COUNT(*) FROM v_year_in_review_summary;  -- Expected: 50

-- Verify listening personalities are assigned
SELECT DISTINCT listening_personality FROM v_listening_personality;
```

### Page Dependencies
| Dependency | Reason |
|------------|--------|
| Phase 1 (Setup + Home) | Requires shared infrastructure |
| Phase 4 (Gold) | Not strictly required, but Gold page pattern informs aggregate display |

---

## Objectives

1. Add Serving page to the app
2. Implement Year-in-Review analytics with listener selector
3. Use session state for listener persistence
4. Visualize all 15 serving views
5. Add platform analytics tabs

---

## Prerequisites

- Phase 4 complete (Gold page working)
- `04_gold/gold.db` exists with serving views created
- Session state pattern established

---

## Tasks

### 5.1 Create Serving Page

Add `pages/5_Serving.py` to the app.

### 5.2 Update Navigation

Update `app.py` to include Serving page:
```python
pg = st.navigation([
    st.Page("pages/1_Home.py", title="Home", icon="🏠"),
    st.Page("pages/2_Bronze.py", title="Bronze", icon="🥉"),
    st.Page("pages/3_Silver.py", title="Silver", icon="🥈"),
    st.Page("pages/4_Gold.py", title="Gold", icon="🥇"),
    st.Page("pages/5_Serving.py", title="Serving", icon="📊"),
])
```

### 5.3 Session State for Listener

```python
# Initialize session state
if "selected_listener" not in st.session_state:
    st.session_state.selected_listener = None
```

---

## Page Design

**Purpose**: Interactive Year-in-Review experience and analytics exploration.

**Narrative Connection**: "Year-in-Review = Annual Report Card" + listening personalities

**Database**: `04_gold/gold.db` (views)

**Layout**:
```
┌─────────────────────────────────────────────────────────────────┐
│  Serving Layer: Year in Review 2025                             │
│  "What insights can we deliver?"                                │
├─────────────────────────────────────────────────────────────────┤
│  [Tabs: Year in Review | Platform Analytics | Leaderboards]     │
├─────────────────────────────────────────────────────────────────┤
│  TAB 1: YEAR IN REVIEW                                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Select Listener: [Dropdown ▼]                              ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  "Explorer"              165 hours        Top 92%           ││
│  │  Listening Personality   Total Listening  Percentile        ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────┐ ┌─────────────────────────────────┐│
│  │  Top 5 Artists          │ │  Top 5 Tracks                   ││
│  │  [Horizontal bar]       │ │  [Horizontal bar]               ││
│  └─────────────────────────┘ └─────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Monthly Listening Trends                                   ││
│  │  [Area chart: hours by month]                               ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────┐ ┌─────────────────────────────────┐│
│  │  Peak Hours             │ │  Weekday vs Weekend             ││
│  │  [Heatmap: hour × day]  │ │  [Donut chart]                  ││
│  └─────────────────────────┘ └─────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Discovery Stats                                            ││
│  │  [Quarterly new artist discovery]                           ││
│  └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│  TAB 2: PLATFORM ANALYTICS                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Daily Platform Stats                                       ││
│  │  [Line chart: daily streams, unique listeners]              ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Genre Trends Over Time                                     ││
│  │  [Multi-line: top 5 genres by month]                        ││
│  └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│  TAB 3: LEADERBOARDS                                            │
│  ┌─────────────────────────┐ ┌─────────────────────────────────┐│
│  │  Top Tracks             │ │  Top Artists                    ││
│  │  [Search filter]        │ │  [Genre filter]                 ││
│  │  [Sortable table]       │ │  [Sortable table]               ││
│  │  [CSV Download]         │ │  [CSV Download]                 ││
│  └─────────────────────────┘ └─────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## Components by Tab

### Tab 1: Year in Review

| Component | Type | Source View | Business Question |
|-----------|------|-------------|-------------------|
| Listener dropdown | st.selectbox | v_year_in_review_summary | Who to analyze? |
| Personality badge | st.metric | v_listening_personality | What type of listener? |
| Total hours | st.metric | v_year_in_review_summary | How much listening? |
| Percentile | st.metric | v_year_in_review_summary | vs other listeners? |
| Top 5 artists | Plotly horizontal bar | v_top_artists_by_listener | Favorite artists? |
| Top 5 tracks | Plotly horizontal bar | v_top_tracks_by_listener | Favorite tracks? |
| Monthly trends | Plotly area | v_monthly_trends_by_listener | Seasonal patterns? |
| Peak hours heatmap | Plotly heatmap | v_peak_listening_times | When do they listen? |
| Weekday/weekend | Plotly donut | v_weekday_vs_weekend | Weekend listener? |
| Discovery stats | Plotly line/bar | v_discovery_stats | How adventurous? |

### Tab 2: Platform Analytics

| Component | Type | Source View | Business Question |
|-----------|------|-------------|-------------------|
| Daily stats line | Plotly line | v_daily_platform_stats | Platform activity? |
| Genre trends | Plotly multi-line | v_genre_trends | Genre popularity? |

### Tab 3: Leaderboards

| Component | Type | Source View | Business Question |
|-----------|------|-------------|-------------------|
| Track search | st.text_input | Filter | Find specific track? |
| Track table | st.dataframe | v_track_popularity | Top tracks overall? |
| Genre filter | st.multiselect | Filter | Filter by genre? |
| Artist table | st.dataframe | v_artist_popularity | Top artists overall? |
| Download buttons | st.download_button | CSVs | Export leaderboards? |

---

## Key Queries

### Listener List for Dropdown
```sql
SELECT listener_id, listener_name
FROM v_year_in_review_summary
ORDER BY listener_name;
```

### Year in Review Summary (selected listener)
```sql
SELECT *
FROM v_year_in_review_summary
WHERE listener_id = ?;
```

### Listening Personality
```sql
SELECT listening_personality, unique_artists, unique_genres
FROM v_listening_personality
WHERE listener_id = ?;
```

### Top 5 Artists
```sql
SELECT rank, artist_name, total_minutes
FROM v_top_artists_by_listener
WHERE listener_id = ?
ORDER BY rank;
```

### Top 5 Tracks
```sql
SELECT rank, track_title, artist_name, play_count
FROM v_top_tracks_by_listener
WHERE listener_id = ?
ORDER BY rank;
```

### Monthly Trends
```sql
SELECT month, month_name, total_hours
FROM v_monthly_trends_by_listener
WHERE listener_id = ?
ORDER BY month;
```

### Peak Listening Times
```sql
SELECT day_of_week, hour_of_day, stream_count
FROM v_peak_listening_times
WHERE listener_id = ?;
```

### Weekday vs Weekend
```sql
SELECT weekday_streams, weekend_streams, weekend_pct
FROM v_weekday_vs_weekend
WHERE listener_id = ?;
```

### Discovery Stats
```sql
SELECT q1_new_artists, q2_new_artists, q3_new_artists, q4_new_artists
FROM v_discovery_stats
WHERE listener_id = ?;
```

### Daily Platform Stats
```sql
SELECT full_date, total_streams, unique_listeners, total_hours
FROM v_daily_platform_stats
ORDER BY full_date;
```

### Genre Trends
```sql
SELECT month_name, genre, stream_count
FROM v_genre_trends
WHERE genre IN (SELECT genre FROM v_genre_trends GROUP BY genre ORDER BY SUM(stream_count) DESC LIMIT 5)
ORDER BY month, stream_count DESC;
```

### Track Popularity
```sql
SELECT rank, track_title, artist_name, genre, total_streams, unique_listeners
FROM v_track_popularity
ORDER BY rank;
```

### Artist Popularity
```sql
SELECT rank, artist_name, genre, total_streams, unique_listeners
FROM v_artist_popularity
ORDER BY rank;
```

---

## Session State Implementation

```python
import streamlit as st
from components.database import query_df

# Initialize session state
if "selected_listener_id" not in st.session_state:
    st.session_state.selected_listener_id = None

# Get listener list
listeners = query_df("gold", """
    SELECT listener_id, listener_name
    FROM v_year_in_review_summary
    ORDER BY listener_name
""")

# Create dropdown with session state
selected = st.selectbox(
    "Select Listener",
    options=listeners["listener_id"].tolist(),
    format_func=lambda x: listeners[listeners["listener_id"] == x]["listener_name"].iloc[0],
    index=listeners["listener_id"].tolist().index(st.session_state.selected_listener_id)
        if st.session_state.selected_listener_id in listeners["listener_id"].tolist()
        else 0,
    key="listener_selector"
)

# Update session state
st.session_state.selected_listener_id = selected
```

---

## Heatmap for Peak Hours

```python
import plotly.express as px

# Query peak listening times
df = query_df("gold", f"""
    SELECT day_of_week, hour_of_day, stream_count
    FROM v_peak_listening_times
    WHERE listener_id = '{selected_listener}'
""")

# Pivot for heatmap
pivot = df.pivot(index="day_of_week", columns="hour_of_day", values="stream_count")

fig = px.imshow(
    pivot,
    labels=dict(x="Hour of Day", y="Day of Week", color="Streams"),
    aspect="auto",
    color_continuous_scale="Blues"
)
st.plotly_chart(fig, use_container_width=True)
```

---

## Verification Checklist

After implementation:

- [ ] Serving page accessible from sidebar
- [ ] Three tabs visible: Year in Review, Platform Analytics, Leaderboards

**Tab 1: Year in Review**
- [ ] Listener dropdown shows all 50 listeners
- [ ] Selecting listener updates all charts
- [ ] Session state persists across page navigation
- [ ] Personality badge displays correctly
- [ ] Total hours and percentile metrics show
- [ ] Top 5 artists bar chart renders
- [ ] Top 5 tracks bar chart renders
- [ ] Monthly trends area chart renders
- [ ] Peak hours heatmap renders (7×24 grid)
- [ ] Weekday/weekend donut chart renders
- [ ] Discovery stats shows quarterly breakdown

**Tab 2: Platform Analytics**
- [ ] Daily platform stats line chart renders
- [ ] Genre trends multi-line chart shows top 5 genres

**Tab 3: Leaderboards**
- [ ] Track search filter works
- [ ] Track table is sortable
- [ ] Genre multiselect filter works
- [ ] Artist table is sortable
- [ ] CSV download works for both tables

**General**
- [ ] Sidebar narrative displays
- [ ] No errors when switching listeners rapidly

---

## Sidebar Narrative

```python
with st.sidebar:
    st.info(
        "**Serving Layer**\n\n"
        "Business-friendly analytics:\n"
        "- **15 views** hiding complex SQL\n"
        "- **Year in Review** like Spotify Wrapped\n"
        "- **Listening Personalities** based on behavior\n\n"
        "End users query views, not fact tables."
    )
```

---

## Listening Personalities Reference

| Personality | Criteria |
|-------------|----------|
| Explorer | 80+ unique artists |
| Genre Loyalist | 3 or fewer genres |
| The Shuffler | >70% shuffle mode |
| Deep Listener | >85% full play rate |
| Offline Adventurer | >50% offline |
| Power User | >2,500 streams |
| Casual Listener | Default |

---

## Notes

- This is the most complex page with 3 tabs and ~20 components
- Session state ensures listener selection persists if user navigates away
- Heatmap requires pivoting the data (day × hour matrix)
- Consider caching listener list to avoid re-querying on every interaction
- Genre trends should limit to top 5 genres to avoid cluttered chart
