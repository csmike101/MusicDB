"""
Raw Data Generator for Music Streaming Workbook

Generates synthetic data with intentional quality issues for teaching
data cleaning and transformation concepts.

Usage:
    python generate_data.py

Output:
    data/listeners.json  (~50 records)
    data/artists.json    (~100 records)
    data/tracks.json     (~1000 records)
    data/streams.csv     (~100k records)
"""

import csv
import json
import os
import random
import uuid
from datetime import datetime, timedelta
from typing import Any

from faker import Faker

# Initialize Faker with seed for reproducibility
fake = Faker()
Faker.seed(42)
random.seed(42)

# Constants
NUM_LISTENERS = 50
NUM_ARTISTS = 100
NUM_TRACKS = 1000
NUM_STREAMS = 100000
YEAR = 2025

# Genre list with intentional casing variations for some entries
GENRES_CLEAN = [
    "Rock", "Pop", "Hip Hop", "Electronic", "Jazz", "Classical",
    "R&B", "Country", "Metal", "Folk", "Indie", "Blues", "Reggae",
    "Latin", "Soul", "Punk", "Alternative", "Dance"
]

# For creating casing issues (~10%)
GENRES_DIRTY = GENRES_CLEAN + [
    "rock", "ROCK", "pop", "POP", "hip hop", "HIP HOP",
    "electronic", "ELECTRONIC", "jazz", "JAZZ"
]

DEVICE_TYPES = ["mobile", "desktop", "tablet", "smart_speaker", "web"]

COUNTRIES = [
    "United States", "United Kingdom", "Canada", "Germany", "France",
    "Australia", "Japan", "Brazil", "Mexico", "Spain", "Italy",
    "Netherlands", "Sweden", "South Korea", "India"
]

# Album name templates
ALBUM_TEMPLATES = [
    "{adj} {noun}", "The {noun}", "{noun} {noun2}", "{adj} {noun} {noun2}",
    "{noun}", "Songs of {noun}", "{adj} Days", "Return to {noun}"
]
ALBUM_ADJS = ["Midnight", "Golden", "Lost", "Electric", "Velvet", "Neon", "Silent", "Wild", "Dark", "Bright"]
ALBUM_NOUNS = ["Dreams", "Roads", "Hearts", "Skies", "Waves", "Mountains", "City", "Rain", "Fire", "Stars"]


def generate_album_name() -> str:
    """Generate a random album name."""
    template = random.choice(ALBUM_TEMPLATES)
    return template.format(
        adj=random.choice(ALBUM_ADJS),
        noun=random.choice(ALBUM_NOUNS),
        noun2=random.choice(ALBUM_NOUNS)
    )


def generate_listeners() -> list[dict[str, Any]]:
    """Generate listener profiles with some quality issues."""
    listeners = []

    for i in range(NUM_LISTENERS):
        listener_id = str(uuid.uuid4())

        # Most listeners have complete data, some have nulls
        has_city = random.random() > 0.15  # ~15% missing city

        # Birth dates for ages 13-70 (relative to 2025)
        min_birth = datetime(1955, 1, 1)  # 70 years old in 2025
        max_birth = datetime(2012, 1, 1)  # 13 years old in 2025
        birth_date = fake.date_between(start_date=min_birth, end_date=max_birth)

        # Account creation dates spread over 2 years before the streaming year
        created_at = fake.date_time_between(
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2024, 12, 31)
        )

        first_name = fake.first_name()
        last_name = fake.last_name()

        listener = {
            "listener_id": listener_id,
            "email": fake.email(),
            "username": fake.user_name(),
            "first_name": first_name,
            "last_name": last_name,
            "birth_date": birth_date.isoformat(),
            "city": fake.city() if has_city else None,
            "country": random.choice(COUNTRIES),
            "subscription_type": random.choices(
                ["free", "premium"],
                weights=[0.6, 0.4]  # 60% free, 40% premium
            )[0],
            "created_at": created_at.isoformat()
        }

        # Add whitespace issues to some usernames (~2%)
        if random.random() < 0.02:
            listener["username"] = f"  {listener['username']}  "

        # Add whitespace issues to some names (~2%)
        if random.random() < 0.02:
            listener["first_name"] = f" {listener['first_name']} "

        listeners.append(listener)

    return listeners


def generate_artists() -> list[dict[str, Any]]:
    """Generate artist records with some quality issues."""
    artists = []

    for i in range(NUM_ARTISTS):
        artist_id = f"art_{i+1:03d}"

        # Use dirty genres sometimes for casing issues (~10%)
        genre = random.choice(GENRES_DIRTY) if random.random() < 0.1 else random.choice(GENRES_CLEAN)

        # Add whitespace to some genres (~2%)
        if random.random() < 0.02:
            genre = f"  {genre}  "

        # Monthly listeners: ranges from small indie to superstar
        # Distribution skewed toward smaller artists
        if random.random() < 0.6:
            monthly_listeners = random.randint(1000, 50000)  # Emerging
        elif random.random() < 0.8:
            monthly_listeners = random.randint(50000, 500000)  # Established
        elif random.random() < 0.95:
            monthly_listeners = random.randint(500000, 5000000)  # Star
        else:
            monthly_listeners = random.randint(5000000, 50000000)  # Superstar

        # Some artists have null formed_year (~15%)
        has_formed_year = random.random() > 0.15

        artist = {
            "artist_id": artist_id,
            "name": fake.name() if random.random() < 0.3 else f"The {fake.word().title()}s",
            "genre": genre,
            "country": random.choice(COUNTRIES),
            "formed_year": random.randint(1960, 2024) if has_formed_year else None,
            "monthly_listeners": monthly_listeners
        }

        # Add whitespace issues to some names (~2%)
        if random.random() < 0.02:
            artist["name"] = f" {artist['name']}  "

        artists.append(artist)

    return artists


def generate_tracks(artists: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Generate track records with some quality issues."""
    tracks = []
    artist_ids = [a["artist_id"] for a in artists]

    for i in range(NUM_TRACKS):
        track_id = f"trk_{i+1:04d}"
        artist_id = random.choice(artist_ids)

        # Find artist genre for consistency (sometimes)
        artist = next(a for a in artists if a["artist_id"] == artist_id)

        # 80% use artist genre, 20% different genre (collaborations, genre experiments)
        if random.random() < 0.8:
            genre = artist["genre"]
        else:
            genre = random.choice(GENRES_DIRTY) if random.random() < 0.1 else random.choice(GENRES_CLEAN)

        # Some tracks have no album (singles) (~20%)
        has_album = random.random() > 0.2

        # Duration between 90 seconds and 8 minutes (in milliseconds)
        duration_ms = random.randint(90000, 480000)

        # Release date in last 5 years
        release_date = fake.date_between(
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2025, 6, 30)
        )

        # Explicit content flag (~15% are explicit)
        explicit = random.random() < 0.15

        track = {
            "track_id": track_id,
            "title": fake.sentence(nb_words=random.randint(1, 4)).rstrip('.'),
            "artist_id": artist_id,
            "album": generate_album_name() if has_album else None,
            "duration_ms": duration_ms,
            "genre": genre,
            "release_date": release_date.isoformat(),
            "explicit": explicit
        }

        # Add whitespace issues to some titles (~2%)
        if random.random() < 0.02:
            track["title"] = f" {track['title']} "

        # Date format inconsistency (~2%)
        if random.random() < 0.02:
            d = datetime.fromisoformat(track["release_date"])
            track["release_date"] = d.strftime("%m/%d/%Y")

        tracks.append(track)

    return tracks


def generate_streams(
    listeners: list[dict[str, Any]],
    tracks: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Generate stream events with quality issues including duplicates and invalid FKs."""
    streams = []

    listener_ids = [l["listener_id"] for l in listeners]
    track_ids = [t["track_id"] for t in tracks]
    track_durations = {t["track_id"]: t["duration_ms"] for t in tracks}

    # Premium listeners stream more
    premium_listeners = {l["listener_id"] for l in listeners if l["subscription_type"] == "premium"}

    # Generate stream timestamps across the year
    year_start = datetime(YEAR, 1, 1)
    year_end = datetime(YEAR, 12, 31, 23, 59, 59)

    stream_count = 0
    duplicates_to_add = []

    while stream_count < NUM_STREAMS:
        stream_id = f"str_{stream_count+1:06d}"

        # Pick a listener (premium listeners appear more often)
        listener_id = random.choice(listener_ids)
        weight = 2.0 if listener_id in premium_listeners else 1.0
        if random.random() > weight / 2.0:
            listener_id = random.choice(listener_ids)

        # Pick a track (or invalid track ~0.5% of time)
        if random.random() < 0.005:
            track_id = f"trk_{NUM_TRACKS + random.randint(1, 100):04d}"  # Invalid FK
            track_duration_ms = 200000  # Fake duration for invalid track
        else:
            track_id = random.choice(track_ids)
            track_duration_ms = track_durations[track_id]

        # Generate timestamp with realistic patterns
        stream_date = fake.date_time_between(start_date=year_start, end_date=year_end)

        # Adjust hour distribution to be more realistic
        # Peak hours: 6-9 AM, 12-2 PM, 6-11 PM
        hour = random.choices(
            list(range(24)),
            weights=[
                1, 1, 1, 1, 1, 2,  # 0-5 AM (low)
                4, 5, 5, 4, 3, 3,  # 6-11 AM (morning commute)
                5, 5, 4, 3, 3, 4,  # 12-5 PM (afternoon)
                6, 7, 7, 6, 4, 2   # 6-11 PM (evening peak)
            ]
        )[0]
        stream_date = stream_date.replace(hour=hour, minute=random.randint(0, 59))

        # Duration played in milliseconds (most listen to full song, some skip)
        if random.random() < 0.7:
            # Full listen
            duration_played_ms = track_duration_ms
        elif random.random() < 0.5:
            # Partial listen (30-90%)
            duration_played_ms = int(track_duration_ms * random.uniform(0.3, 0.9))
        else:
            # Skip (< 30 seconds)
            duration_played_ms = random.randint(5000, 30000)

        # Shuffle and offline modes
        shuffle_mode = random.random() < 0.35  # 35% use shuffle
        offline_mode = random.random() < 0.10  # 10% offline

        stream = {
            "stream_id": stream_id,
            "listener_id": listener_id,
            "track_id": track_id,
            "streamed_at": stream_date.isoformat(),
            "duration_played_ms": duration_played_ms,
            "device_type": random.choice(DEVICE_TYPES),
            "shuffle_mode": shuffle_mode,
            "offline_mode": offline_mode
        }

        streams.append(stream)

        # Mark some for duplication (~1%)
        if random.random() < 0.01:
            duplicates_to_add.append(stream.copy())

        stream_count += 1

    # Add duplicate records (same content, appears twice)
    streams.extend(duplicates_to_add)

    # Shuffle to mix in duplicates
    random.shuffle(streams)

    return streams


def save_json(data: list[dict[str, Any]], filepath: str) -> None:
    """Save data as JSON."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"  Saved {len(data)} records to {filepath}")


def save_csv(data: list[dict[str, Any]], filepath: str) -> None:
    """Save data as CSV."""
    if not data:
        return

    fieldnames = list(data[0].keys())

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    print(f"  Saved {len(data)} records to {filepath}")


def main():
    """Generate all data files."""
    # Create data directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    print("Generating music streaming data...")
    print("-" * 40)

    # Generate data
    print("Generating listeners...")
    listeners = generate_listeners()

    print("Generating artists...")
    artists = generate_artists()

    print("Generating tracks...")
    tracks = generate_tracks(artists)

    print("Generating streams (this may take a moment)...")
    streams = generate_streams(listeners, tracks)

    print("-" * 40)
    print("Saving files...")

    # Save files (JSON for entities, CSV for events)
    save_json(listeners, os.path.join(data_dir, "listeners.json"))
    save_json(artists, os.path.join(data_dir, "artists.json"))
    save_json(tracks, os.path.join(data_dir, "tracks.json"))
    save_csv(streams, os.path.join(data_dir, "streams.csv"))

    print("-" * 40)
    print("Data generation complete!")
    print()
    print("Quality issues injected:")
    print("  - ~1% duplicate stream records")
    print("  - ~15% missing city in listeners")
    print("  - ~15% missing formed_year in artists")
    print("  - ~20% missing album in tracks (singles)")
    print("  - ~10% genre casing inconsistencies")
    print("  - ~0.5% invalid track references in streams")
    print("  - ~2% whitespace issues in text fields")
    print("  - ~2% date format variations in release_date")


if __name__ == "__main__":
    main()
