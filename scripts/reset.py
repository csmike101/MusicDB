#!/usr/bin/env python3
"""
Reset the project to a clean slate.

Removes all generated files:
- All database files (bronze.db, silver.db, gold.db)
- Raw data files (01_raw/data/)
- Serving reports (05_serving/reports/)

Usage:
    python scripts/reset.py           # Reset everything (with confirmation)
    python scripts/reset.py --force   # Reset without confirmation
    python scripts/reset.py --dry-run # Show what would be deleted
"""

import argparse
import shutil
import sys
import os

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import (
    logger, RAW_DIR, BRONZE_DB, SILVER_DB, GOLD_DB, SERVING_DIR,
    print_banner, check_database_exists
)


def get_files_to_delete() -> list:
    """
    Get list of files and directories that would be deleted.

    Returns:
        List of (path, type) tuples
    """
    items = []

    # Database files
    for name, db_path in [("Bronze", BRONZE_DB), ("Silver", SILVER_DB), ("Gold", GOLD_DB)]:
        if db_path.exists():
            size_mb = db_path.stat().st_size / (1024 * 1024)
            items.append((db_path, f"{name} database ({size_mb:.2f} MB)"))

    # Raw data directory
    raw_data_dir = RAW_DIR / "data"
    if raw_data_dir.exists():
        file_count = len(list(raw_data_dir.glob("*")))
        items.append((raw_data_dir, f"Raw data directory ({file_count} files)"))

    # Serving reports
    reports_dir = SERVING_DIR / "reports"
    if reports_dir.exists():
        file_count = len(list(reports_dir.glob("*")))
        items.append((reports_dir, f"Serving reports ({file_count} files)"))

    return items


def reset_all(dry_run: bool = False) -> int:
    """
    Remove all generated files and databases.

    Args:
        dry_run: If True, only show what would be deleted

    Returns:
        Number of items deleted
    """
    items = get_files_to_delete()

    if not items:
        logger.info("Nothing to reset - project is already clean")
        return 0

    action = "Would delete" if dry_run else "Deleting"
    deleted = 0

    for path, description in items:
        logger.info(f"  {action}: {description}")

        if not dry_run:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            deleted += 1

    return deleted


def main():
    parser = argparse.ArgumentParser(
        description="Reset project to clean slate"
    )
    parser.add_argument(
        "--force", "-f", action="store_true",
        help="Skip confirmation prompt"
    )
    parser.add_argument(
        "--dry-run", "-n", action="store_true",
        help="Show what would be deleted without deleting"
    )

    args = parser.parse_args()

    print_banner("PROJECT RESET", "=", 60)

    items = get_files_to_delete()

    if not items:
        logger.info("Nothing to reset - project is already clean")
        return

    logger.info(f"Found {len(items)} item(s) to delete:\n")
    for path, description in items:
        logger.info(f"  - {description}")

    if args.dry_run:
        logger.info("\n[Dry run - no files deleted]")
        return

    if not args.force:
        logger.info("")
        response = input("Are you sure you want to delete these files? [y/N] ")
        if response.lower() != 'y':
            logger.info("Reset cancelled")
            return

    logger.info("\nResetting project...")
    deleted = reset_all(dry_run=False)

    print_banner("RESET COMPLETE", "=", 60)
    logger.info(f"Deleted {deleted} item(s)")
    logger.info("\nRun 'python scripts/run_all.py' to regenerate everything")


if __name__ == "__main__":
    main()
