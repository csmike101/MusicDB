"""
Bronze Layer: Data Loading Script

Loads raw data from JSON/CSV files into SQLite bronze tables.
All data is stored as TEXT with audit columns for lineage tracking.

Usage:
    python 02_load_bronze_data.py

Output:
    bronze.db - SQLite database with loaded data
"""

import csv
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path


def get_paths() -> dict[str, Path]:
    """Get all relevant file paths."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    return {
        "script_dir": script_dir,
        "raw_data_dir": project_root / "00_raw" / "data",
        "ddl_file": script_dir / "01_create_bronze_tables.sql",
        "database": script_dir / "bronze.db",
    }


def create_database(conn: sqlite3.Connection, ddl_path: Path) -> None:
    """Execute DDL to create bronze tables."""
    print(f"Executing DDL from {ddl_path.name}...")

    with open(ddl_path, "r", encoding="utf-8") as f:
        ddl_script = f.read()

    conn.executescript(ddl_script)
    conn.commit()
    print("  Tables created successfully")


def load_json_file(
    conn: sqlite3.Connection,
    file_path: Path,
    table_name: str,
    columns: list[str],
) -> int:
    """Load a JSON array file into a bronze table."""
    print(f"Loading {file_path.name} into {table_name}...")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Build INSERT statement
    placeholders = ", ".join(["?"] * (len(columns) + 2))  # +2 for audit columns
    insert_sql = f"""
        INSERT INTO {table_name}
        ({', '.join(columns)}, _source_file, _row_number)
        VALUES ({placeholders})
    """

    cursor = conn.cursor()
    source_file = file_path.name

    for row_num, record in enumerate(data, start=1):
        # Convert all values to strings (preserving None as None)
        values = [
            str(record.get(col)) if record.get(col) is not None else None
            for col in columns
        ]
        values.extend([source_file, row_num])
        cursor.execute(insert_sql, values)

    conn.commit()
    print(f"  Loaded {len(data)} records")
    return len(data)


def load_csv_file(
    conn: sqlite3.Connection,
    file_path: Path,
    table_name: str,
    columns: list[str],
) -> int:
    """Load a CSV file into a bronze table."""
    print(f"Loading {file_path.name} into {table_name}...")

    # Build INSERT statement
    placeholders = ", ".join(["?"] * (len(columns) + 2))  # +2 for audit columns
    insert_sql = f"""
        INSERT INTO {table_name}
        ({', '.join(columns)}, _source_file, _row_number)
        VALUES ({placeholders})
    """

    cursor = conn.cursor()
    source_file = file_path.name
    row_count = 0

    with open(file_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        for row_num, record in enumerate(reader, start=1):
            # Convert empty strings to None, keep everything else as string
            values = [
                record.get(col) if record.get(col) != "" else None
                for col in columns
            ]
            values.extend([source_file, row_num])
            cursor.execute(insert_sql, values)
            row_count += 1

            # Commit in batches for large files
            if row_count % 10000 == 0:
                conn.commit()
                print(f"    ...{row_count:,} records loaded")

    conn.commit()
    print(f"  Loaded {row_count:,} records")
    return row_count


def verify_load(conn: sqlite3.Connection) -> None:
    """Print verification summary."""
    print("\n" + "=" * 50)
    print("VERIFICATION SUMMARY")
    print("=" * 50)

    tables = ["bronze_listeners", "bronze_artists", "bronze_tracks", "bronze_streams"]

    for table in tables:
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count:,} rows")

    # Check for duplicates in streams (expected ~1%)
    cursor = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT stream_id FROM bronze_streams
            GROUP BY stream_id
            HAVING COUNT(*) > 1
        )
    """)
    dup_count = cursor.fetchone()[0]
    print(f"\n  Duplicate stream_ids found: {dup_count:,} (expected ~1%)")

    # Sample audit columns
    cursor = conn.execute("""
        SELECT _source_file, MIN(_loaded_at), MAX(_row_number)
        FROM bronze_streams
        GROUP BY _source_file
    """)
    row = cursor.fetchone()
    if row:
        print(f"\n  Audit sample (streams):")
        print(f"    Source file: {row[0]}")
        print(f"    Loaded at: {row[1]}")
        print(f"    Max row number: {row[2]:,}")


def main():
    """Main execution."""
    paths = get_paths()

    # Remove existing database
    if paths["database"].exists():
        os.remove(paths["database"])
        print(f"Removed existing {paths['database'].name}")

    print(f"\nCreating bronze database: {paths['database']}")
    print("-" * 50)

    # Connect to database
    conn = sqlite3.connect(paths["database"])

    try:
        # Create tables
        create_database(conn, paths["ddl_file"])

        print("-" * 50)

        # Load listeners (JSON)
        load_json_file(
            conn,
            paths["raw_data_dir"] / "listeners.json",
            "bronze_listeners",
            ["listener_id", "email", "username", "age", "country", "city",
             "signup_date", "subscription_tier"],
        )

        # Load artists (CSV)
        load_csv_file(
            conn,
            paths["raw_data_dir"] / "artists.csv",
            "bronze_artists",
            ["artist_id", "name", "genre", "country", "formed_year"],
        )

        # Load tracks (CSV)
        load_csv_file(
            conn,
            paths["raw_data_dir"] / "tracks.csv",
            "bronze_tracks",
            ["track_id", "title", "artist_id", "album", "duration_seconds",
             "release_date", "genre"],
        )

        # Load streams (CSV)
        load_csv_file(
            conn,
            paths["raw_data_dir"] / "streams.csv",
            "bronze_streams",
            ["stream_id", "listener_id", "track_id", "streamed_at",
             "duration_listened", "platform"],
        )

        # Verify
        verify_load(conn)

        print("\n" + "=" * 50)
        print("Bronze layer load complete!")
        print("=" * 50)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
