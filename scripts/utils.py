"""
Shared utilities for the data modeling workbook.

Provides common functions for database connections, SQL execution,
logging, and path management across all pipeline scripts.
"""

import sqlite3
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "01_raw"
BRONZE_DIR = PROJECT_ROOT / "02_bronze"
SILVER_DIR = PROJECT_ROOT / "03_silver"
GOLD_DIR = PROJECT_ROOT / "04_gold"
SERVING_DIR = PROJECT_ROOT / "05_serving"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Database paths
BRONZE_DB = BRONZE_DIR / "bronze.db"
SILVER_DB = SILVER_DIR / "silver.db"
GOLD_DB = GOLD_DIR / "gold.db"

# Layer configurations
LAYERS = ["raw", "bronze", "silver", "gold", "serving"]

BRONZE_TABLES = ["bronze_listeners", "bronze_artists", "bronze_tracks", "bronze_streams"]
SILVER_TABLES = ["listeners", "artists", "tracks", "streams", "silver_rejected_records"]
GOLD_TABLES = [
    "dim_date", "dim_listener", "dim_artist", "dim_track", "dim_device",
    "fact_streams",
    "agg_daily_listener_streams", "agg_daily_track_streams", "agg_monthly_genre_streams"
]
SERVING_VIEWS = [
    "v_stream_details", "v_listener_summary", "v_track_popularity",
    "v_artist_popularity", "v_genre_trends", "v_daily_platform_stats",
    "v_top_artists_by_listener", "v_top_tracks_by_listener", "v_top_genre_by_listener",
    "v_listening_personality", "v_monthly_trends_by_listener", "v_peak_listening_times",
    "v_weekday_vs_weekend", "v_discovery_stats", "v_year_in_review_summary"
]


def get_connection(db_path: Path) -> sqlite3.Connection:
    """
    Get SQLite connection with row factory for dict-like access.

    Args:
        db_path: Path to the SQLite database

    Returns:
        sqlite3.Connection with Row factory configured
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def execute_sql_file(db_path: Path, sql_file: Path) -> None:
    """
    Execute a SQL file against a database.

    Args:
        db_path: Path to the SQLite database
        sql_file: Path to the SQL file to execute
    """
    logger.info(f"Executing {sql_file.name} on {db_path.name}")
    conn = sqlite3.connect(db_path)
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    try:
        conn.executescript(sql)
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"SQL execution failed: {e}")
        raise
    finally:
        conn.close()


def get_row_count(db_path: Path, table: str) -> int:
    """
    Get row count for a table or view.

    Args:
        db_path: Path to the SQLite database
        table: Name of table or view

    Returns:
        Number of rows
    """
    conn = get_connection(db_path)
    try:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        conn.close()
    return count


def table_exists(db_path: Path, table: str) -> bool:
    """
    Check if a table or view exists in the database.

    Args:
        db_path: Path to the SQLite database
        table: Name of table or view

    Returns:
        True if exists, False otherwise
    """
    conn = get_connection(db_path)
    try:
        result = conn.execute("""
            SELECT COUNT(*) FROM sqlite_master
            WHERE type IN ('table', 'view') AND name = ?
        """, (table,)).fetchone()[0]
    finally:
        conn.close()
    return result > 0


def log_layer_stats(layer_name: str, db_path: Path, tables: List[str]) -> Dict[str, int]:
    """
    Log and return statistics for a layer.

    Args:
        layer_name: Name of the layer for logging
        db_path: Path to the database
        tables: List of table/view names to check

    Returns:
        Dictionary mapping table names to row counts
    """
    stats = {}
    logger.info(f"\n{'='*50}")
    logger.info(f"{layer_name} Layer Statistics")
    logger.info(f"{'='*50}")

    for table in tables:
        if table_exists(db_path, table):
            count = get_row_count(db_path, table)
            stats[table] = count
            logger.info(f"  {table}: {count:,} rows")
        else:
            logger.warning(f"  {table}: NOT FOUND")
            stats[table] = -1

    return stats


def print_banner(text: str, char: str = "=", width: int = 60) -> None:
    """Print a formatted banner."""
    logger.info("")
    logger.info(char * width)
    logger.info(text.center(width))
    logger.info(char * width)


def check_database_exists(db_path: Path) -> bool:
    """Check if a database file exists."""
    return db_path.exists() and db_path.stat().st_size > 0


def get_pipeline_status() -> Dict[str, Dict]:
    """
    Get the current status of all pipeline layers.

    Returns:
        Dictionary with layer status information
    """
    status = {}

    # Raw layer
    raw_data_dir = RAW_DIR / "data"
    raw_files = list(raw_data_dir.glob("*.csv")) + list(raw_data_dir.glob("*.json")) if raw_data_dir.exists() else []
    status["raw"] = {
        "exists": len(raw_files) > 0,
        "files": len(raw_files),
        "path": str(raw_data_dir)
    }

    # Bronze layer
    status["bronze"] = {
        "exists": check_database_exists(BRONZE_DB),
        "path": str(BRONZE_DB),
        "tables": BRONZE_TABLES
    }

    # Silver layer
    status["silver"] = {
        "exists": check_database_exists(SILVER_DB),
        "path": str(SILVER_DB),
        "tables": SILVER_TABLES
    }

    # Gold layer
    status["gold"] = {
        "exists": check_database_exists(GOLD_DB),
        "path": str(GOLD_DB),
        "tables": GOLD_TABLES
    }

    # Serving layer (views in gold.db)
    if check_database_exists(GOLD_DB):
        views_exist = all(table_exists(GOLD_DB, v) for v in SERVING_VIEWS[:3])
        status["serving"] = {
            "exists": views_exist,
            "path": str(GOLD_DB) + " (views)",
            "views": SERVING_VIEWS
        }
    else:
        status["serving"] = {
            "exists": False,
            "path": str(GOLD_DB) + " (views)",
            "views": SERVING_VIEWS
        }

    return status


if __name__ == "__main__":
    # Quick test of utilities
    print_banner("Utility Module Test")

    status = get_pipeline_status()
    for layer, info in status.items():
        exists = "YES" if info["exists"] else "NO"
        logger.info(f"{layer.upper()}: {exists}")
