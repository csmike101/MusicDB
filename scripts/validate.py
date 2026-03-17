#!/usr/bin/env python3
"""
Cross-layer validation for the medallion architecture.

Verifies data integrity across all pipeline layers:
- Row count reconciliation between layers
- Foreign key integrity in gold layer
- Aggregate table consistency
- No duplicates in silver layer

Usage:
    python scripts/validate.py           # Run all validations
    python scripts/validate.py --verbose # Show detailed output
"""

import argparse
import sys
import os

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import (
    logger, BRONZE_DB, SILVER_DB, GOLD_DB,
    get_connection, get_row_count, check_database_exists,
    print_banner, SERVING_VIEWS
)


class ValidationResult:
    """Track validation results."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.details = []

    def add_pass(self, message: str):
        self.passed += 1
        self.details.append(("PASS", message))
        logger.info(f"  PASS: {message}")

    def add_fail(self, message: str):
        self.failed += 1
        self.details.append(("FAIL", message))
        logger.error(f"  FAIL: {message}")

    def add_warning(self, message: str):
        self.warnings += 1
        self.details.append(("WARN", message))
        logger.warning(f"  WARN: {message}")

    @property
    def all_passed(self) -> bool:
        return self.failed == 0


def validate_databases_exist(result: ValidationResult) -> bool:
    """Check that all required databases exist."""
    logger.info("\nChecking database files...")

    all_exist = True

    for name, db_path in [("Bronze", BRONZE_DB), ("Silver", SILVER_DB), ("Gold", GOLD_DB)]:
        if check_database_exists(db_path):
            size_mb = db_path.stat().st_size / (1024 * 1024)
            result.add_pass(f"{name} database exists ({size_mb:.2f} MB)")
        else:
            result.add_fail(f"{name} database not found: {db_path}")
            all_exist = False

    return all_exist


def validate_bronze_to_silver(result: ValidationResult) -> None:
    """Validate bronze to silver transformation."""
    logger.info("\nValidating Bronze -> Silver transformation...")

    if not check_database_exists(BRONZE_DB) or not check_database_exists(SILVER_DB):
        result.add_fail("Required databases not found")
        return

    # Get row counts
    bronze_streams = get_row_count(BRONZE_DB, "bronze_streams")
    silver_streams = get_row_count(SILVER_DB, "streams")
    silver_rejected = get_row_count(SILVER_DB, "silver_rejected_records")

    logger.info(f"  Bronze streams: {bronze_streams:,}")
    logger.info(f"  Silver streams: {silver_streams:,}")
    logger.info(f"  Rejected records: {silver_rejected:,}")

    # Calculate expected difference (duplicates + rejected)
    difference = bronze_streams - silver_streams
    logger.info(f"  Difference: {difference:,} (duplicates removed + invalid FK rejected)")

    # Check for duplicates in silver (should be 0)
    conn = get_connection(SILVER_DB)
    dup_count = conn.execute("""
        SELECT COUNT(*) - COUNT(DISTINCT stream_id) FROM streams
    """).fetchone()[0]
    conn.close()

    if dup_count > 0:
        result.add_fail(f"{dup_count} duplicates found in silver.streams")
    else:
        result.add_pass("No duplicates in silver.streams")

    # Verify all rejections are logged
    if silver_rejected > 0:
        result.add_pass(f"Rejected records logged ({silver_rejected:,} records)")
    else:
        result.add_warning("No rejected records - verify data quality issues exist in raw data")


def validate_silver_to_gold(result: ValidationResult) -> None:
    """Validate silver to gold transformation."""
    logger.info("\nValidating Silver -> Gold transformation...")

    if not check_database_exists(SILVER_DB) or not check_database_exists(GOLD_DB):
        result.add_fail("Required databases not found")
        return

    # Row counts should match
    silver_streams = get_row_count(SILVER_DB, "streams")
    gold_streams = get_row_count(GOLD_DB, "fact_streams")

    if silver_streams == gold_streams:
        result.add_pass(f"Stream counts match ({gold_streams:,})")
    else:
        result.add_fail(f"Stream count mismatch: Silver={silver_streams:,}, Gold={gold_streams:,}")

    # Check FK integrity in gold
    conn = get_connection(GOLD_DB)

    # Check listener FK
    orphan_listeners = conn.execute("""
        SELECT COUNT(*) FROM fact_streams f
        WHERE NOT EXISTS (SELECT 1 FROM dim_listener l WHERE l.listener_key = f.listener_key)
    """).fetchone()[0]

    if orphan_listeners == 0:
        result.add_pass("No orphan listener references in fact_streams")
    else:
        result.add_fail(f"{orphan_listeners} orphan listener references")

    # Check track FK
    orphan_tracks = conn.execute("""
        SELECT COUNT(*) FROM fact_streams f
        WHERE NOT EXISTS (SELECT 1 FROM dim_track t WHERE t.track_key = f.track_key)
    """).fetchone()[0]

    if orphan_tracks == 0:
        result.add_pass("No orphan track references in fact_streams")
    else:
        result.add_fail(f"{orphan_tracks} orphan track references")

    # Check device FK
    orphan_devices = conn.execute("""
        SELECT COUNT(*) FROM fact_streams f
        WHERE NOT EXISTS (SELECT 1 FROM dim_device d WHERE d.device_key = f.device_key)
    """).fetchone()[0]

    if orphan_devices == 0:
        result.add_pass("No orphan device references in fact_streams")
    else:
        result.add_fail(f"{orphan_devices} orphan device references")

    # Check date FK
    orphan_dates = conn.execute("""
        SELECT COUNT(*) FROM fact_streams f
        WHERE NOT EXISTS (SELECT 1 FROM dim_date d WHERE d.date_key = f.date_key)
    """).fetchone()[0]

    if orphan_dates == 0:
        result.add_pass("No orphan date references in fact_streams")
    else:
        result.add_fail(f"{orphan_dates} orphan date references")

    conn.close()


def validate_aggregates(result: ValidationResult) -> None:
    """Validate aggregate tables reconcile with facts."""
    logger.info("\nValidating Aggregate tables...")

    if not check_database_exists(GOLD_DB):
        result.add_fail("Gold database not found")
        return

    conn = get_connection(GOLD_DB)

    fact_count = conn.execute("SELECT COUNT(*) FROM fact_streams").fetchone()[0]

    # Daily listener aggregate
    agg_listener_sum = conn.execute(
        "SELECT SUM(stream_count) FROM agg_daily_listener_streams"
    ).fetchone()[0] or 0

    if fact_count == agg_listener_sum:
        result.add_pass(f"agg_daily_listener_streams reconciles ({agg_listener_sum:,})")
    else:
        result.add_fail(f"agg_daily_listener_streams mismatch: {agg_listener_sum:,} vs {fact_count:,}")

    # Daily track aggregate
    agg_track_sum = conn.execute(
        "SELECT SUM(stream_count) FROM agg_daily_track_streams"
    ).fetchone()[0] or 0

    if fact_count == agg_track_sum:
        result.add_pass(f"agg_daily_track_streams reconciles ({agg_track_sum:,})")
    else:
        result.add_fail(f"agg_daily_track_streams mismatch: {agg_track_sum:,} vs {fact_count:,}")

    # Monthly genre aggregate
    agg_genre_sum = conn.execute(
        "SELECT SUM(stream_count) FROM agg_monthly_genre_streams"
    ).fetchone()[0] or 0

    if fact_count == agg_genre_sum:
        result.add_pass(f"agg_monthly_genre_streams reconciles ({agg_genre_sum:,})")
    else:
        result.add_fail(f"agg_monthly_genre_streams mismatch: {agg_genre_sum:,} vs {fact_count:,}")

    conn.close()


def validate_serving_views(result: ValidationResult) -> None:
    """Validate serving layer views exist and have data."""
    logger.info("\nValidating Serving layer views...")

    if not check_database_exists(GOLD_DB):
        result.add_fail("Gold database not found")
        return

    conn = get_connection(GOLD_DB)

    views_found = 0
    views_with_data = 0

    for view in SERVING_VIEWS:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {view}").fetchone()[0]
            views_found += 1
            if count > 0:
                views_with_data += 1
        except Exception:
            pass

    conn.close()

    if views_found == len(SERVING_VIEWS):
        result.add_pass(f"All {views_found} serving views exist")
    else:
        result.add_fail(f"Only {views_found}/{len(SERVING_VIEWS)} serving views found")

    if views_with_data == views_found:
        result.add_pass(f"All {views_with_data} views contain data")
    else:
        result.add_warning(f"Only {views_with_data}/{views_found} views have data")


def validate_date_dimension(result: ValidationResult) -> None:
    """Validate date dimension coverage."""
    logger.info("\nValidating Date dimension...")

    if not check_database_exists(GOLD_DB):
        result.add_fail("Gold database not found")
        return

    conn = get_connection(GOLD_DB)

    date_stats = conn.execute("""
        SELECT MIN(full_date), MAX(full_date), COUNT(*)
        FROM dim_date
    """).fetchone()

    min_date, max_date, count = date_stats

    if count == 365:
        result.add_pass(f"Date dimension has 365 days ({min_date} to {max_date})")
    else:
        result.add_fail(f"Date dimension has {count} days, expected 365")

    # Check all fact dates have dimension entries
    orphan_dates = conn.execute("""
        SELECT COUNT(DISTINCT date_key) FROM fact_streams
        WHERE date_key NOT IN (SELECT date_key FROM dim_date)
    """).fetchone()[0]

    if orphan_dates == 0:
        result.add_pass("All fact dates have dimension entries")
    else:
        result.add_fail(f"{orphan_dates} distinct dates missing from dimension")

    conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Validate cross-layer data integrity"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show detailed output"
    )

    args = parser.parse_args()

    print_banner("CROSS-LAYER VALIDATION", "=", 60)

    result = ValidationResult()

    # Run all validations
    if not validate_databases_exist(result):
        logger.error("\nCannot continue: Required databases not found")
        logger.error("Run 'python scripts/run_all.py' first")
        sys.exit(1)

    validate_bronze_to_silver(result)
    validate_silver_to_gold(result)
    validate_aggregates(result)
    validate_date_dimension(result)
    validate_serving_views(result)

    # Summary
    print_banner("VALIDATION SUMMARY", "=", 60)
    logger.info(f"  Passed:   {result.passed}")
    logger.info(f"  Failed:   {result.failed}")
    logger.info(f"  Warnings: {result.warnings}")

    if result.all_passed:
        logger.info("\nALL VALIDATIONS PASSED")
        sys.exit(0)
    else:
        logger.error("\nSOME VALIDATIONS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
