#!/usr/bin/env python3
"""
Run the complete medallion architecture pipeline.

Usage:
    python scripts/run_all.py              # Run entire pipeline
    python scripts/run_all.py --from silver  # Start from silver layer
    python scripts/run_all.py --to gold      # Stop after gold layer
    python scripts/run_all.py --from bronze --to silver  # Run just bronze to silver
"""

import argparse
import subprocess
import sys
import os

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import (
    logger, PROJECT_ROOT, RAW_DIR, BRONZE_DIR, SILVER_DIR, GOLD_DIR, SERVING_DIR,
    BRONZE_DB, SILVER_DB, GOLD_DB,
    BRONZE_TABLES, SILVER_TABLES, GOLD_TABLES, SERVING_VIEWS,
    execute_sql_file, log_layer_stats, print_banner
)


def run_raw_layer() -> bool:
    """
    Generate raw data files.

    Returns:
        True if successful, False otherwise
    """
    print_banner("PHASE 1: Generating Raw Data")

    generate_script = RAW_DIR / "generate_data.py"
    if not generate_script.exists():
        logger.error(f"Generate script not found: {generate_script}")
        return False

    result = subprocess.run(
        [sys.executable, str(generate_script)],
        cwd=str(RAW_DIR),
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        logger.error(f"Raw generation failed: {result.stderr}")
        return False

    # Check output
    data_dir = RAW_DIR / "data"
    if not data_dir.exists():
        logger.error("Raw data directory not created")
        return False

    files = list(data_dir.glob("*"))
    logger.info(f"Generated {len(files)} raw data files")
    for f in files:
        size_kb = f.stat().st_size / 1024
        logger.info(f"  {f.name}: {size_kb:.1f} KB")

    return True


def run_bronze_layer() -> bool:
    """
    Load data into bronze layer.

    Returns:
        True if successful, False otherwise
    """
    print_banner("PHASE 2: Loading Bronze Layer")

    # Create tables
    create_sql = BRONZE_DIR / "01_create_tables.sql"
    if create_sql.exists():
        execute_sql_file(BRONZE_DB, create_sql)

    # Load data
    load_script = BRONZE_DIR / "02_load_data.py"
    if not load_script.exists():
        logger.error(f"Load script not found: {load_script}")
        return False

    result = subprocess.run(
        [sys.executable, str(load_script)],
        cwd=str(BRONZE_DIR),
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        logger.error(f"Bronze load failed: {result.stderr}")
        if result.stdout:
            logger.error(f"Stdout: {result.stdout}")
        return False

    log_layer_stats("Bronze", BRONZE_DB, BRONZE_TABLES)
    return True


def run_silver_layer() -> bool:
    """
    Transform data into silver layer.

    Returns:
        True if successful, False otherwise
    """
    print_banner("PHASE 3: Transforming Silver Layer")

    sql_files = [
        "01_create_tables.sql",
        "02_transform_data.sql",
        "03_create_indexes.sql"
    ]

    for sql_file in sql_files:
        sql_path = SILVER_DIR / sql_file
        if sql_path.exists():
            execute_sql_file(SILVER_DB, sql_path)
        else:
            logger.warning(f"SQL file not found: {sql_path}")

    log_layer_stats("Silver", SILVER_DB, SILVER_TABLES)
    return True


def run_gold_layer() -> bool:
    """
    Build dimensional model in gold layer.

    Returns:
        True if successful, False otherwise
    """
    print_banner("PHASE 4: Building Gold Layer")

    sql_files = [
        "01_create_dimensions.sql",
        "02_create_facts.sql",
        "03_create_aggregates.sql",
        "04_load_dimensions.sql",
        "05_load_facts.sql",
        "06_load_aggregates.sql"
    ]

    for sql_file in sql_files:
        sql_path = GOLD_DIR / sql_file
        if sql_path.exists():
            execute_sql_file(GOLD_DB, sql_path)
        else:
            logger.warning(f"SQL file not found: {sql_path}")

    log_layer_stats("Gold", GOLD_DB, GOLD_TABLES)
    return True


def run_serving_layer() -> bool:
    """
    Create analytics views and export reports.

    Returns:
        True if successful, False otherwise
    """
    print_banner("PHASE 5: Creating Serving Layer")

    # Create views in gold.db (SQLite views can't reference attached DBs)
    sql_files = [
        "01_create_views.sql",
        "02_year_in_review.sql"
    ]

    for sql_file in sql_files:
        sql_path = SERVING_DIR / sql_file
        if sql_path.exists():
            execute_sql_file(GOLD_DB, sql_path)
        else:
            logger.warning(f"SQL file not found: {sql_path}")

    # Log view stats
    log_layer_stats("Serving", GOLD_DB, SERVING_VIEWS)

    # Generate Year-in-Review reports
    export_script = SERVING_DIR / "03_export_reports.py"
    if export_script.exists():
        logger.info("\nGenerating Year-in-Review reports...")
        result = subprocess.run(
            [sys.executable, str(export_script), "--limit", "10", "--csv"],
            cwd=str(SERVING_DIR),
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            logger.warning(f"Report export had issues: {result.stderr}")
        else:
            logger.info("Year-in-Review reports generated")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Run the medallion architecture pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_all.py                    # Run entire pipeline
  python scripts/run_all.py --from silver      # Start from silver
  python scripts/run_all.py --to gold          # Stop after gold
  python scripts/run_all.py --from bronze --to silver  # Bronze to silver only
        """
    )
    parser.add_argument(
        "--from", dest="start_from", default="raw",
        choices=["raw", "bronze", "silver", "gold", "serving"],
        help="Start from a specific layer (default: raw)"
    )
    parser.add_argument(
        "--to", dest="end_at", default="serving",
        choices=["raw", "bronze", "silver", "gold", "serving"],
        help="End at a specific layer (default: serving)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    layers = ["raw", "bronze", "silver", "gold", "serving"]
    start_idx = layers.index(args.start_from)
    end_idx = layers.index(args.end_at)

    if start_idx > end_idx:
        logger.error(f"Invalid range: --from {args.start_from} is after --to {args.end_at}")
        sys.exit(1)

    print_banner("MEDALLION ARCHITECTURE PIPELINE", "=", 60)
    logger.info(f"Running layers: {' -> '.join(layers[start_idx:end_idx+1])}")

    # Track results
    results = {}

    # Run each layer in sequence
    layer_functions = {
        "raw": run_raw_layer,
        "bronze": run_bronze_layer,
        "silver": run_silver_layer,
        "gold": run_gold_layer,
        "serving": run_serving_layer
    }

    for i, layer in enumerate(layers):
        if start_idx <= i <= end_idx:
            success = layer_functions[layer]()
            results[layer] = success
            if not success:
                logger.error(f"Pipeline failed at {layer} layer")
                sys.exit(1)

    # Summary
    print_banner("PIPELINE COMPLETE", "=", 60)
    for layer, success in results.items():
        status = "OK" if success else "FAILED"
        logger.info(f"  {layer.upper()}: {status}")

    logger.info("\nRun 'python scripts/validate.py' to verify data integrity")


if __name__ == "__main__":
    main()
