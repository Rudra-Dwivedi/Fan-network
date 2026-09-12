"""
Resolves a displayable image URL for an item, based on what's stored in its
`metadata` JSON column (populated by the TMDB/Spotify/sports clients).
Returns None if there's nothing to show — the template falls back to a
domain-colored placeholder icon in that case.
"""

import json

TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"


def resolve_image_url(item):
    try:
        meta = json.loads(item["metadata"]) if item["metadata"] else {}
    except (TypeError, ValueError):
        meta = {}

    # Check for direct image_url (e.g. custom admin-created items)
    if meta.get("image_url"):
        return meta["image_url"]

    if item["type"] == "movie":
        poster = meta.get("poster_path")
        return f"{TMDB_IMAGE_BASE}{poster}" if poster else None

    if item["type"] == "song":
        return meta.get("album_image") or None

    if item["type"] == "team":
        return meta.get("badge") or None

    return None


def with_image_urls(items):
    """Take a list of sqlite3.Row items and return plain dicts with an
    added 'image_url' key, ready to pass straight into a template."""
    return [dict(item, image_url=resolve_image_url(item)) for item in items]
