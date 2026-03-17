# Phase 6: Integration

**Status:** Pending

---

## Goal

Create end-to-end pipeline scripts and utilities that orchestrate the entire medallion architecture flow. Enable single-command execution of the full pipeline with validation.

---

## Files to Create

| File | Purpose |
|------|---------|
| `scripts/utils.py` | Shared utility functions |
| `scripts/run_all.py` | Full pipeline orchestration |
| `scripts/validate.py` | Cross-layer validation |
| `scripts/reset.py` | Clean slate reset script |

---

## Utility Functions

### scripts/utils.py
```python
"""Shared utilities for the data modeling workbook."""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "01_raw"
BRONZE_DIR = PROJECT_ROOT / "02_bronze"
SILVER_DIR = PROJECT_ROOT / "03_silver"
GOLD_DIR = PROJECT_ROOT / "04_gold"
SERVING_DIR = PROJECT_ROOT / "05_serving"

# Database paths
BRONZE_DB = BRONZE_DIR / "bronze.db"
SILVER_DB = SILVER_DIR / "silver.db"
GOLD_DB = GOLD_DIR / "gold.db"
SERVING_DB = SERVING_DIR / "serving.db"


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Get SQLite connection with row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def execute_sql_file(db_path: Path, sql_file: Path) -> None:
    """Execute a SQL file against a database."""
    logger.info(f"Executing {sql_file.name} on {db_path.name}")
    conn = get_connection(db_path)
    with open(sql_file, 'r') as f:
        sql = f.read()
    conn.executescript(sql)
    conn.commit()
    conn.close()


def get_row_count(db_path: Path, table: str) -> int:
    """Get row count for a table."""
    conn = get_connection(db_path)
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    conn.close()
    return count


def log_layer_stats(layer_name: str, db_path: Path, tables: list) -> dict:
    """Log and return statistics for a layer."""
    stats = {}
    logger.info(f"\n{'='*50}")
    logger.info(f"{layer_name} Layer Statistics")
    logger.info(f"{'='*50}")
    for table in tables:
        count = get_row_count(db_path, table)
        stats[table] = count
        logger.info(f"  {table}: {count:,} rows")
    return stats
```

---

## Pipeline Orchestration

### scripts/run_all.py
```python
"""Run the complete medallion architecture pipeline."""

import argparse
import sys
from pathlib import Path

from utils import (
    logger, PROJECT_ROOT, RAW_DIR, BRONZE_DIR, SILVER_DIR, GOLD_DIR, SERVING_DIR,
    BRONZE_DB, SILVER_DB, GOLD_DB, SERVING_DB,
    execute_sql_file, log_layer_stats
)

def run_raw_layer():
    """Generate raw data."""
    logger.info("\n" + "="*60)
    logger.info("PHASE 1: Generating Raw Data")
    logger.info("="*60)

    import subprocess
    result = subprocess.run(
        [sys.executable, str(RAW_DIR / "generate_data.py")],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        logger.error(f"Raw generation failed: {result.stderr}")
        sys.exit(1)
    logger.info("Raw data generation complete")


def run_bronze_layer():
    """Load data into bronze layer."""
    logger.info("\n" + "="*60)
    logger.info("PHASE 2: Loading Bronze Layer")
    logger.info("="*60)

    # Create tables
    execute_sql_file(BRONZE_DB, BRONZE_DIR / "01_create_tables.sql")

    # Load data
    import subprocess
    result = subprocess.run(
        [sys.executable, str(BRONZE_DIR / "02_load_data.py")],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        logger.error(f"Bronze load failed: {result.stderr}")
        sys.exit(1)

    log_layer_stats("Bronze", BRONZE_DB, [
        "bronze_listeners", "bronze_artists", "bronze_tracks", "bronze_streams"
    ])


def run_silver_layer():
    """Transform data into silver layer."""
    logger.info("\n" + "="*60)
    logger.info("PHASE 3: Transforming Silver Layer")
    logger.info("="*60)

    execute_sql_file(SILVER_DB, SILVER_DIR / "01_create_tables.sql")
    execute_sql_file(SILVER_DB, SILVER_DIR / "02_transform_data.sql")
    execute_sql_file(SILVER_DB, SILVER_DIR / "03_create_indexes.sql")

    log_layer_stats("Silver", SILVER_DB, [
        "listeners", "artists", "tracks", "streams"
    ])


def run_gold_layer():
    """Build dimensional model in gold layer."""
    logger.info("\n" + "="*60)
    logger.info("PHASE 4: Building Gold Layer")
    logger.info("="*60)

    execute_sql_file(GOLD_DB, GOLD_DIR / "01_create_dimensions.sql")
    execute_sql_file(GOLD_DB, GOLD_DIR / "02_create_facts.sql")
    execute_sql_file(GOLD_DB, GOLD_DIR / "03_create_aggregates.sql")
    execute_sql_file(GOLD_DB, GOLD_DIR / "04_load_dimensions.sql")
    execute_sql_file(GOLD_DB, GOLD_DIR / "05_load_facts.sql")
    execute_sql_file(GOLD_DB, GOLD_DIR / "06_load_aggregates.sql")

    log_layer_stats("Gold", GOLD_DB, [
        "dim_date", "dim_listener", "dim_artist", "dim_track", "dim_device",
        "fact_streams",
        "agg_daily_listener_streams", "agg_daily_track_streams", "agg_monthly_genre_streams"
    ])


def run_serving_layer():
    """Create analytics views and exports."""
    logger.info("\n" + "="*60)
    logger.info("PHASE 5: Creating Serving Layer")
    logger.info("="*60)

    execute_sql_file(SERVING_DB, SERVING_DIR / "01_create_views.sql")

    # Generate Year-in-Review reports
    import subprocess
    result = subprocess.run(
        [sys.executable, str(SERVING_DIR / "03_export_reports.py")],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        logger.warning(f"Report export had issues: {result.stderr}")

    logger.info("Serving layer complete")


def main():
    parser = argparse.ArgumentParser(description="Run medallion architecture pipeline")
    parser.add_argument("--from", dest="start_from", default="raw",
                        choices=["raw", "bronze", "silver", "gold", "serving"],
                        help="Start from a specific layer")
    parser.add_argument("--to", dest="end_at", default="serving",
                        choices=["raw", "bronze", "silver", "gold", "serving"],
                        help="End at a specific layer")
    args = parser.parse_args()

    layers = ["raw", "bronze", "silver", "gold", "serving"]
    start_idx = layers.index(args.start_from)
    end_idx = layers.index(args.end_at)

    logger.info("Starting Medallion Architecture Pipeline")
    logger.info(f"Running layers: {layers[start_idx:end_idx+1]}")

    if start_idx <= 0 <= end_idx:
        run_raw_layer()
    if start_idx <= 1 <= end_idx:
        run_bronze_layer()
    if start_idx <= 2 <= end_idx:
        run_silver_layer()
    if start_idx <= 3 <= end_idx:
        run_gold_layer()
    if start_idx <= 4 <= end_idx:
        run_serving_layer()

    logger.info("\n" + "="*60)
    logger.info("PIPELINE COMPLETE")
    logger.info("="*60)


if __name__ == "__main__":
    main()
```

---

## Validation Script

### scripts/validate.py
```python
"""Cross-layer validation for the medallion architecture."""

from utils import (
    logger, BRONZE_DB, SILVER_DB, GOLD_DB,
    get_connection, get_row_count
)


def validate_bronze_to_silver():
    """Validate bronze to silver transformation."""
    logger.info("\nValidating Bronze -> Silver")

    bronze_streams = get_row_count(BRONZE_DB, "bronze_streams")
    silver_streams = get_row_count(SILVER_DB, "streams")
    silver_rejected = get_row_count(SILVER_DB, "silver_rejected_records")

    # Rows should reconcile
    expected_silver = bronze_streams - silver_rejected
    # Note: duplicates also reduce count

    logger.info(f"  Bronze streams: {bronze_streams:,}")
    logger.info(f"  Silver streams: {silver_streams:,}")
    logger.info(f"  Rejected records: {silver_rejected:,}")

    # Check for duplicates in silver
    conn = get_connection(SILVER_DB)
    dup_count = conn.execute("""
        SELECT COUNT(*) - COUNT(DISTINCT stream_id) FROM streams
    """).fetchone()[0]
    conn.close()

    if dup_count > 0:
        logger.error(f"  FAIL: {dup_count} duplicates in silver.streams")
        return False
    logger.info("  PASS: No duplicates in silver")
    return True


def validate_silver_to_gold():
    """Validate silver to gold transformation."""
    logger.info("\nValidating Silver -> Gold")

    silver_streams = get_row_count(SILVER_DB, "streams")
    gold_streams = get_row_count(GOLD_DB, "fact_streams")

    if silver_streams != gold_streams:
        logger.error(f"  FAIL: Row count mismatch ({silver_streams} vs {gold_streams})")
        return False
    logger.info(f"  PASS: Stream counts match ({gold_streams:,})")

    # Check FK integrity in gold
    conn = get_connection(GOLD_DB)
    orphans = conn.execute("""
        SELECT COUNT(*) FROM fact_streams f
        WHERE NOT EXISTS (SELECT 1 FROM dim_listener l WHERE l.listener_key = f.listener_key)
           OR NOT EXISTS (SELECT 1 FROM dim_track t WHERE t.track_key = f.track_key)
    """).fetchone()[0]
    conn.close()

    if orphans > 0:
        logger.error(f"  FAIL: {orphans} orphaned fact records")
        return False
    logger.info("  PASS: No FK violations in gold")
    return True


def validate_aggregates():
    """Validate aggregate tables reconcile with facts."""
    logger.info("\nValidating Aggregates")

    conn = get_connection(GOLD_DB)

    fact_count = conn.execute("SELECT COUNT(*) FROM fact_streams").fetchone()[0]
    agg_sum = conn.execute("SELECT SUM(stream_count) FROM agg_daily_listener_streams").fetchone()[0]

    conn.close()

    if fact_count != agg_sum:
        logger.error(f"  FAIL: Aggregate mismatch ({fact_count} vs {agg_sum})")
        return False
    logger.info(f"  PASS: Aggregates reconcile ({agg_sum:,} streams)")
    return True


def main():
    logger.info("="*60)
    logger.info("Running Cross-Layer Validation")
    logger.info("="*60)

    results = []
    results.append(validate_bronze_to_silver())
    results.append(validate_silver_to_gold())
    results.append(validate_aggregates())

    logger.info("\n" + "="*60)
    if all(results):
        logger.info("ALL VALIDATIONS PASSED")
    else:
        logger.error("SOME VALIDATIONS FAILED")
        exit(1)


if __name__ == "__main__":
    main()
```

---

## Reset Script

### scripts/reset.py
```python
"""Reset the project to a clean slate."""

import shutil
from pathlib import Path

from utils import (
    logger, PROJECT_ROOT, RAW_DIR, BRONZE_DIR, SILVER_DIR, GOLD_DIR, SERVING_DIR,
    BRONZE_DB, SILVER_DB, GOLD_DB, SERVING_DB
)


def reset_all():
    """Remove all generated files and databases."""
    logger.info("Resetting project to clean slate...")

    # Remove databases
    for db in [BRONZE_DB, SILVER_DB, GOLD_DB, SERVING_DB]:
        if db.exists():
            db.unlink()
            logger.info(f"  Removed {db.name}")

    # Remove raw data
    raw_data_dir = RAW_DIR / "data"
    if raw_data_dir.exists():
        shutil.rmtree(raw_data_dir)
        logger.info("  Removed raw data directory")

    # Remove serving reports
    reports_dir = SERVING_DIR / "reports"
    if reports_dir.exists():
        shutil.rmtree(reports_dir)
        logger.info("  Removed serving reports")

    logger.info("Reset complete")


if __name__ == "__main__":
    reset_all()
```

---

## Tasks

- [ ] Create `scripts/utils.py`
- [ ] Create `scripts/run_all.py`
- [ ] Create `scripts/validate.py`
- [ ] Create `scripts/reset.py`
- [ ] Test full pipeline execution
- [ ] Test validation checks
- [ ] Test reset and re-run
- [ ] Document usage in README

---

## Usage

```bash
# Run full pipeline
python scripts/run_all.py

# Run from specific layer
python scripts/run_all.py --from silver

# Run to specific layer
python scripts/run_all.py --to gold

# Validate cross-layer integrity
python scripts/validate.py

# Reset everything
python scripts/reset.py
```

---

## Verification

```bash
# Full pipeline should complete without errors
python scripts/run_all.py

# Validation should pass
python scripts/validate.py

# Reset and re-run should produce identical results
python scripts/reset.py
python scripts/run_all.py
python scripts/validate.py
```

---

## Final Deliverables Checklist

- [ ] All layer directories populated with SQL and Python files
- [ ] All databases generated (bronze.db, silver.db, gold.db, serving.db)
- [ ] Year-in-Review JSON exports for all listeners
- [ ] Pipeline runs end-to-end without errors
- [ ] Cross-layer validation passes
- [ ] README documents full usage
