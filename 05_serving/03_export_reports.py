#!/usr/bin/env python3
"""
Serving Layer: Export Year-in-Review Reports

Generates personalized JSON reports for each listener, similar to Spotify Wrapped.
Each report contains:
- Summary statistics
- Top 5 artists
- Top 5 tracks
- Top genre
- Listening personality
- Monthly trends
- Peak listening times
"""

import sqlite3
import json
import csv
from pathlib import Path
from datetime import datetime


def dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
    """Convert SQLite rows to dictionaries."""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def get_listener_summary(conn: sqlite3.Connection, listener_id: str) -> dict:
    """Get overall summary stats for a listener."""
    result = conn.execute("""
        SELECT
            total_streams,
            total_minutes,
            total_hours,
            days_active,
            unique_tracks,
            unique_artists,
            unique_genres,
            avg_completion_pct,
            full_plays,
            full_play_rate,
            shuffle_pct,
            offline_pct,
            listening_percentile
        FROM v_year_in_review_summary
        WHERE listener_id = ?
    """, (listener_id,)).fetchone()
    return result if result else {}


def get_top_artists(conn: sqlite3.Connection, listener_id: str, limit: int = 5) -> list:
    """Get top artists for a listener."""
    results = conn.execute("""
        SELECT
            artist_rank,
            artist_name,
            artist_genre,
            stream_count,
            minutes_listened
        FROM v_top_artists_by_listener
        WHERE listener_id = ? AND artist_rank <= ?
        ORDER BY artist_rank
    """, (listener_id, limit)).fetchall()
    return results


def get_top_tracks(conn: sqlite3.Connection, listener_id: str, limit: int = 5) -> list:
    """Get top tracks for a listener."""
    results = conn.execute("""
        SELECT
            track_rank,
            track_title,
            artist_name,
            album,
            play_count,
            minutes_listened
        FROM v_top_tracks_by_listener
        WHERE listener_id = ? AND track_rank <= ?
        ORDER BY track_rank
    """, (listener_id, limit)).fetchall()
    return results


def get_top_genre(conn: sqlite3.Connection, listener_id: str) -> dict:
    """Get the top genre for a listener."""
    result = conn.execute("""
        SELECT
            top_genre,
            stream_count,
            minutes_listened,
            genre_share_pct
        FROM v_top_genre_by_listener
        WHERE listener_id = ?
    """, (listener_id,)).fetchone()
    return result if result else {}


def get_listening_personality(conn: sqlite3.Connection, listener_id: str) -> dict:
    """Get listening personality classification."""
    result = conn.execute("""
        SELECT
            listening_personality,
            total_streams,
            unique_artists,
            unique_tracks,
            unique_genres,
            shuffle_pct,
            full_play_pct
        FROM v_listening_personality
        WHERE listener_id = ?
    """, (listener_id,)).fetchone()
    return result if result else {}


def get_monthly_trends(conn: sqlite3.Connection, listener_id: str) -> list:
    """Get monthly listening trends."""
    results = conn.execute("""
        SELECT
            month,
            month_name,
            streams,
            unique_tracks,
            unique_artists,
            minutes_listened,
            hours_listened
        FROM v_monthly_trends_by_listener
        WHERE listener_id = ?
        ORDER BY month
    """, (listener_id,)).fetchall()
    return results


def get_peak_times(conn: sqlite3.Connection, listener_id: str) -> list:
    """Get peak listening times."""
    results = conn.execute("""
        SELECT
            time_of_day,
            stream_count,
            pct_of_listening,
            time_rank
        FROM v_peak_listening_times
        WHERE listener_id = ?
        ORDER BY time_rank
    """, (listener_id,)).fetchall()
    return results


def get_weekday_vs_weekend(conn: sqlite3.Connection, listener_id: str) -> dict:
    """Get weekday vs weekend breakdown."""
    result = conn.execute("""
        SELECT
            weekday_streams,
            weekend_streams,
            weekday_minutes,
            weekend_minutes,
            listener_type
        FROM v_weekday_vs_weekend
        WHERE listener_id = ?
    """, (listener_id,)).fetchone()
    return result if result else {}


def generate_listener_report(conn: sqlite3.Connection, listener_id: str) -> dict:
    """Generate complete Year-in-Review report for a listener."""
    # Get listener name
    listener = conn.execute("""
        SELECT full_name, email, country, subscription_type
        FROM dim_listener
        WHERE listener_id = ?
    """, (listener_id,)).fetchone()

    report = {
        'listener_id': listener_id,
        'listener_name': listener['full_name'] if listener else 'Unknown',
        'email': listener['email'] if listener else None,
        'country': listener['country'] if listener else None,
        'subscription_type': listener['subscription_type'] if listener else None,
        'year': 2025,
        'generated_at': datetime.now().isoformat(),
        'summary': get_listener_summary(conn, listener_id),
        'top_artists': get_top_artists(conn, listener_id),
        'top_tracks': get_top_tracks(conn, listener_id),
        'top_genre': get_top_genre(conn, listener_id),
        'listening_personality': get_listening_personality(conn, listener_id),
        'monthly_trends': get_monthly_trends(conn, listener_id),
        'peak_listening_times': get_peak_times(conn, listener_id),
        'weekday_vs_weekend': get_weekday_vs_weekend(conn, listener_id),
    }

    return report


def export_all_reports(db_path: str, output_dir: str, limit: int = None) -> int:
    """
    Export Year-in-Review JSON reports for all (or some) listeners.

    Args:
        db_path: Path to the serving database
        output_dir: Directory to write JSON files
        limit: Optional limit on number of reports to generate

    Returns:
        Number of reports generated
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = dict_factory

    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Get all listeners
    query = "SELECT DISTINCT listener_id FROM dim_listener ORDER BY listener_id"
    if limit:
        query += f" LIMIT {limit}"
    listeners = conn.execute(query).fetchall()

    count = 0
    for listener in listeners:
        listener_id = listener['listener_id']
        report = generate_listener_report(conn, listener_id)

        # Write individual JSON file
        filename = f"{listener_id}_wrapped_2025.json"
        filepath = output_path / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        count += 1
        print(f"Generated: {filename}")

    conn.close()
    return count


def export_summary_csv(db_path: str, output_path: str) -> int:
    """
    Export a CSV summary of all listeners' Year-in-Review stats.

    Args:
        db_path: Path to the serving database
        output_path: Path to write CSV file

    Returns:
        Number of rows exported
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = dict_factory

    results = conn.execute("""
        SELECT
            s.listener_id,
            s.listener_name,
            s.subscription_type,
            s.country,
            s.total_streams,
            s.total_hours,
            s.unique_artists,
            s.unique_tracks,
            s.unique_genres,
            s.full_play_rate,
            s.listening_percentile,
            p.listening_personality,
            g.top_genre
        FROM v_year_in_review_summary s
        LEFT JOIN v_listening_personality p ON s.listener_id = p.listener_id
        LEFT JOIN v_top_genre_by_listener g ON s.listener_id = g.listener_id
        ORDER BY s.total_hours DESC
    """).fetchall()

    if not results:
        print("No data to export")
        return 0

    # Write CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    conn.close()
    return len(results)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Export Year-in-Review reports from the serving layer'
    )
    parser.add_argument(
        '--db', default='../04_gold/gold.db',
        help='Path to gold database (default: ../04_gold/gold.db)'
    )
    parser.add_argument(
        '--output', default='reports',
        help='Output directory for JSON reports (default: reports)'
    )
    parser.add_argument(
        '--limit', type=int, default=None,
        help='Limit number of reports to generate (default: all)'
    )
    parser.add_argument(
        '--csv', action='store_true',
        help='Also export a summary CSV file'
    )

    args = parser.parse_args()

    # Export JSON reports
    print(f"\nExporting Year-in-Review reports to {args.output}/")
    print("-" * 50)
    count = export_all_reports(args.db, args.output, args.limit)
    print("-" * 50)
    print(f"Generated {count} reports\n")

    # Export CSV summary if requested
    if args.csv:
        csv_path = Path(args.output) / 'year_in_review_summary.csv'
        print(f"Exporting summary CSV to {csv_path}")
        rows = export_summary_csv(args.db, str(csv_path))
        print(f"Exported {rows} rows\n")


if __name__ == "__main__":
    main()
