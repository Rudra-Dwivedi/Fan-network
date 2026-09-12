"""
TMDB (The Movie Database) client.
Get a free API key at: https://www.themoviedb.org/settings/api
Docs: https://developer.themoviedb.org/reference/intro/getting-started
"""

import json
import requests
from flask import current_app

from app.services.settings_store import get_setting

BASE_URL = "https://api.themoviedb.org/3"


def fetch_popular_movies(page=1):
    """Fetch a page of popular movies. Returns a list of dicts ready to insert
    into the `items` table (type='movie')."""
    api_key = get_setting("TMDB_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No TMDB API key set. Add one on the Settings page or set TMDB_API_KEY."
        )

    resp = requests.get(
        f"{BASE_URL}/movie/popular",
        params={"api_key": api_key, "page": page},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    items = []
    for movie in data.get("results", []):
        items.append(
            {
                "type": "movie",
                "external_id": str(movie["id"]),
                "title": movie["title"],
                "genre_tags": "",  # map genre_ids -> names via /genre/movie/list if needed
                "metadata": json.dumps(
                    {
                        "poster_path": movie.get("poster_path"),
                        "overview": movie.get("overview"),
                        "release_date": movie.get("release_date"),
                        "vote_average": movie.get("vote_average"),
                    }
                ),
            }
        )
    return items


def save_items(db, items):
    """Insert a list of item dicts (as produced by the fetch_* functions) into the DB."""
    for item in items:
        db.execute(
            "INSERT INTO items (type, external_id, title, genre_tags, metadata) "
            "VALUES (?, ?, ?, ?, ?)",
            (item["type"], item["external_id"], item["title"], item["genre_tags"], item["metadata"]),
        )
    db.commit()
