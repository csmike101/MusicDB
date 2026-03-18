# MusicDB v1.1 - Streamlit App Implementation Plan

> This is the master plan for MusicDB v1.1. It adds a Streamlit visualization layer on top of the existing medallion architecture.

## Overview

A multi-page Streamlit app that visualizes the MusicDB pipeline, with one page per medallion layer plus a home/overview page. Each page connects directly to the relevant `.db` file.

**New in v1.1:** Interactive dashboards for pipeline observability, data quality metrics, and Year-in-Review analytics.

---

## Status: 🚧 In Progress

| Phase | Name | Status | Details |
|-------|------|--------|---------|
| 1 | Setup + Home Page | ⬜ Pending | [01_setup_and_home.md](./01_setup_and_home.md) |
| 2 | Bronze Page | ⬜ Pending | [02_bronze_page.md](./02_bronze_page.md) |
| 3 | Silver Page | ⬜ Pending | [03_silver_page.md](./03_silver_page.md) |
| 4 | Gold Page | ⬜ Pending | [04_gold_page.md](./04_gold_page.md) |
| 5 | Serving Page | ⬜ Pending | [05_serving_page.md](./05_serving_page.md) |

---

## Design Decisions (Resolved)

| Decision | Choice | Notes |
|----------|--------|-------|
| **Styling** | Light customization | Custom accent color, styled headers |
| **Listener persistence** | Session state | Selection survives page navigation |
| **Data refresh** | Always fresh | No caching, queries hit DB directly |
| **Export** | CSV download | Download buttons on dataframes |
| **Error handling** | Warning + instructions | Friendly message if DBs missing |
| **Mobile support** | Desktop only | Optimized for desktop |

---

## Project Structure (after v1.1)

```
MusicDB/
├── ... (existing v1.0 structure)
│
├── 06_streamlit/                    # NEW: Visualization layer
│   ├── README.md
│   ├── app.py
│   ├── pages/
│   │   ├── 1_Home.py
│   │   ├── 2_Bronze.py
│   │   ├── 3_Silver.py
│   │   ├── 4_Gold.py
│   │   └── 5_Serving.py
│   ├── components/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── metrics.py
│   │   └── charts.py
│   ├── assets/
│   │   └── style.css
│   └── .streamlit/
│       └── config.toml
│
└── docs/plans/v1.1/                 # This plan
    ├── PLAN.md
    ├── 01_setup_and_home.md
    ├── 02_bronze_page.md
    ├── 03_silver_page.md
    ├── 04_gold_page.md
    └── 05_serving_page.md
```

---

## Dependencies (New)

```
streamlit>=1.36.0
plotly>=5.18.0
pandas>=2.0.0
```

---

## Process

Each phase is implemented and verified independently:

1. **Phase 1** produces a working app with Home page only
2. **Phases 2-5** add one page each, verified before proceeding
3. Each phase includes its own verification checklist

---

## Phase Summaries

### Phase 1: Setup + Home Page
Project setup (`06_streamlit/` directory), dependencies, database utilities, error handling, and the Home page with pipeline health dashboard.

**Deliverable:** Functional app that launches and shows pipeline status.

### Phase 2: Bronze Page
Raw ingestion stats, audit metadata visualization, duplicate detection, data explorer.

**Deliverable:** Bronze page shows record counts, duplicates, audit timeline.

### Phase 3: Silver Page
Data quality metrics, rejection summaries, before/after comparisons, quality gauges.

**Deliverable:** Silver page shows cleaning stats, rejected records, quality scores.

### Phase 4: Gold Page
Star schema explorer, dimension distributions, aggregate table browser.

**Deliverable:** Gold page shows schema diagram, dimension stats, aggregates.

### Phase 5: Serving Page
Year-in-Review analytics, listener selector with session state, all serving views visualized.

**Deliverable:** Full Year-in-Review experience with listener selection.

---

## Documentation Updates

After all phases complete:
- [ ] Add Phase 7 section to `docs/WALKTHROUGH.md`
- [ ] Create `06_streamlit/README.md`
- [ ] Update `CLAUDE.md` with new layer
