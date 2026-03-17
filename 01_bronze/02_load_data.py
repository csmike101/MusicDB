"""
Bronze Layer Data Loader

Loads raw data files into bronze staging tables with audit columns.
All data is stored as TEXT to preserve original values exactly.

Usage:
    python 02_load_data.py

Prerequisites:
    - Run 01_create_tables.sql first to create the tables
    - Raw data must exist in ../00_raw/data/
"""

import csv
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def compute_row_hash(row: dict) -> str:
    """Compute MD5 hash of row contents for deduplication tracking."""
    # Sort keys for consistent hashing
    content = json.dumps(row, sort_keys=True, default=str)
    return hashlib.md5(content.encode()).hexdigest()


def get_column_names(table: str) -> list[str]:
    """Get column names for a bronze table (excluding audit columns)."""
    columns = {
        "bronze_listeners": [
            "listener_id", "email", "username", "first_name", "last_name",
            "birth_date", "city", "country", "subscription_type", "created_at"
        ],
        "bronze_artists": [
            "artist_id", "name", "genre", "country", "formed_year", "monthly_listeners"
        ],
        "bronze_tracks": [
            "track_id", "title", "artist_id", "album", "duration_ms",
            "genre", "release_date", "explicit"
        ],
        "bronze_streams": [
            "stream_id", "listener_id", "track_id", "streamed_at",
            "duration_played_ms", "device_type", "shuffle_mode", "offline_mode"
        ]
    }
    return columns[table]


def load_json_to_bronze(
    conn: sqlite3.Connection,
    table: str,
    json_path: str,
    loaded_at: str
) -> int:
    """Load JSON file into bronze table."""
    cursor = conn.cursor()
    source_file = Path(json_path).name
    columns = get_column_names(table)

    with open(json_path, 'r', encoding='utf-8') as f:
        records = json.load(f)

    # Build INSERT statement
    all_columns = columns + ["_source_file", "_loaded_at", "_row_hash"]
    placeholders = ", ".join(["?"] * len(all_columns))
    column_list = ", ".join(all_columns)
    sql = f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})"

    rows_inserted = 0
    for record in records:
        row_hash = compute_row_hash(record)

        # Convert all values to strings (bronze = all TEXT)
        values = [str(record.get(col)) if record.get(col) is not None else None for col in columns]
        values.extend([source_file, loaded_at, row_hash])

        cursor.execute(sql, values)
        rows_inserted += 1

    return rows_inserted


def load_csv_to_bronze(
    conn: sqlite3.Connection,
    table: str,
    csv_path: str,
    loaded_at: str
) -> int:
    """Load CSV file into bronze table."""
    cursor = conn.cursor()
    source_file = Path(csv_path).name
    columns = get_column_names(table)

    # Build INSERT statement
    all_columns = columns + ["_source_file", "_loaded_at", "_row_hash"]
    placeholders = ", ".join(["?"] * len(all_columns))
    column_list = ", ".join(all_columns)
    sql = f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})"

    rows_inserted = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for record in reader:
            row_hash = compute_row_hash(record)

            # CSV values are already strings, but handle empty as None
            values = [record.get(col) if record.get(col) != "" else None for col in columns]
            values.extend([source_file, loaded_at, row_hash])

            cursor.execute(sql, values)
            rows_inserted += 1

    return rows_inserted


def run_sql_file(conn: sqlite3.Connection, sql_path: str) -> None:
    """Execute a SQL file."""
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    conn.executescript(sql)


def main():
    """Load all raw data into bronze tables."""
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    db_path = script_dir / "bronze.db"
    raw_path = project_root / "00_raw" / "data"
    ddl_path = script_dir / "01_create_tables.sql"

    print("Loading data into Bronze layer...")
    print("-" * 40)

    # Connect to database (creates if not exists)
    conn = sqlite3.connect(db_path)

    # Create tables
    print("Creating tables...")
    run_sql_file(conn, str(ddl_path))
    conn.commit()

    # Load timestamp for all records in this batch
    loaded_at = datetime.now(timezone.utc).isoformat()

    # Load JSON files
    print("Loading listeners.json...")
    listeners_count = load_json_to_bronze(
        conn, "bronze_listeners", str(raw_path / "listeners.json"), loaded_at
    )
    print(f"  Loaded {listeners_count} listeners")

    print("Loading artists.json...")
    artists_count = load_json_to_bronze(
        conn, "bronze_artists", str(raw_path / "artists.json"), loaded_at
    )
    print(f"  Loaded {artists_count} artists")

    print("Loading tracks.json...")
    tracks_count = load_json_to_bronze(
        conn, "bronze_tracks", str(raw_path / "tracks.json"), loaded_at
    )
    print(f"  Loaded {tracks_count} tracks")

    # Load CSV file
    print("Loading streams.csv (this may take a moment)...")
    streams_count = load_csv_to_bronze(
        conn, "bronze_streams", str(raw_path / "streams.csv"), loaded_at
    )
    print(f"  Loaded {streams_count} streams")

    conn.commit()
    conn.close()

    print("-" * 40)
    print("Bronze layer load complete!")
    print(f"Database: {db_path}")
    print()
    print("Summary:")
    print(f"  bronze_listeners: {listeners_count:,} rows")
    print(f"  bronze_artists:   {artists_count:,} rows")
    print(f"  bronze_tracks:    {tracks_count:,} rows")
    print(f"  bronze_streams:   {streams_count:,} rows")


if __name__ == "__main__":
    main()
