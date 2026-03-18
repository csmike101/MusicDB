#!/usr/bin/env python3
"""
Copy sample databases to layer directories.

This script provides a cross-platform way to use the pre-generated
sample databases for exploring the project without running the full pipeline.

Usage:
    python scripts/use_sample_data.py           # Copy all sample databases
    python scripts/use_sample_data.py --check   # Verify sample data exists
"""

import argparse
import shutil
import sys
import os

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import (
    logger, PROJECT_ROOT, BRONZE_DB, SILVER_DB, GOLD_DB,
    print_banner, check_database_exists
)

# Sample data paths
SAMPLE_DIR = PROJECT_ROOT / "sample_data"
SAMPLE_BRONZE = SAMPLE_DIR / "bronze.db"
SAMPLE_SILVER = SAMPLE_DIR / "silver.db"
SAMPLE_GOLD = SAMPLE_DIR / "gold.db"


def check_sample_data() -> bool:
    """
    Check if sample data exists.

    Returns:
        True if all sample databases exist
    """
    all_exist = True
    for name, path in [
        ("Bronze", SAMPLE_BRONZE),
        ("Silver", SAMPLE_SILVER),
        ("Gold", SAMPLE_GOLD)
    ]:
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            logger.info(f"  {name}: {path.name} ({size_mb:.2f} MB)")
        else:
            logger.warning(f"  {name}: NOT FOUND at {path}")
            all_exist = False
    return all_exist


def copy_sample_data() -> int:
    """
    Copy sample databases to layer directories.

    Returns:
        Number of databases copied
    """
    copies = [
        (SAMPLE_BRONZE, BRONZE_DB, "Bronze"),
        (SAMPLE_SILVER, SILVER_DB, "Silver"),
        (SAMPLE_GOLD, GOLD_DB, "Gold"),
    ]

    copied = 0
    for src, dst, name in copies:
        if not src.exists():
            logger.error(f"  {name}: Source not found at {src}")
            continue

        # Ensure destination directory exists
        dst.parent.mkdir(parents=True, exist_ok=True)

        # Copy the file
        shutil.copy2(src, dst)
        size_mb = dst.stat().st_size / (1024 * 1024)
        logger.info(f"  {name}: Copied to {dst} ({size_mb:.2f} MB)")
        copied += 1

    return copied


def main():
    parser = argparse.ArgumentParser(
        description='Copy sample databases to layer directories'
    )
    parser.add_argument(
        '--check', action='store_true',
        help='Only check if sample data exists (do not copy)'
    )

    args = parser.parse_args()

    print_banner("SAMPLE DATA SETUP")

    if args.check:
        logger.info("Checking sample data availability...\n")
        if check_sample_data():
            logger.info("\nAll sample databases are available.")
            logger.info("Run without --check to copy them to layer directories.")
        else:
            logger.error("\nSome sample databases are missing!")
            sys.exit(1)
    else:
        logger.info("Copying sample databases to layer directories...\n")
        copied = copy_sample_data()

        print_banner("SETUP COMPLETE")
        logger.info(f"Copied {copied} database(s)")
        logger.info("")
        logger.info("You can now:")
        logger.info("  1. Run 'python scripts/validate.py' to verify data integrity")
        logger.info("  2. Explore data with Python:")
        logger.info("     python -c \"import sqlite3; c=sqlite3.connect('04_gold/gold.db'); \\")
        logger.info("       print([r for r in c.execute('SELECT * FROM dim_artist LIMIT 5')])\"")
        logger.info("")


if __name__ == "__main__":
    main()
