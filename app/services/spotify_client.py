"""
Spotify Web API client (client-credentials flow — good enough for reading
public catalog data; no user login needed).
Create an app at: https://developer.spotify.com/dashboard
Docs: https://developer.spotify.com/documentation/web-api

Note: as of Spotify's Feb/March 2026 API changes, GET /playlists/{id}/items
(formerly /tracks) is only available for playlists the authenticated user
owns or collaborates on — which client-credentials access can never satisfy,
since there's no logged-in user at all. So we fetch tracks via search
instead, which has no such restriction.
"""

import json
import requests

from app.services.settings_store import get_setting

TOKEN_URL = "https://accounts.spotify.com/api/token"
BASE_URL = "https://api.spotify.com/v1"


def _get_access_token():
    client_id = get_setting("SPOTIFY_CLIENT_ID")
    client_secret = get_setting("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "No Spotify credentials set. Add them on the Settings page or set "
            "SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET."
        )

    resp = requests.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(client_id, client_secret),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_tracks_by_search(query, limit=10):
    """Search for tracks (by artist, song, or genre keyword). Returns a list
    of dicts ready to insert into `items` (type='song').
    Spotify caps search `limit` at 10 as of their 2026 API changes."""
    token = _get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.get(
        f"{BASE_URL}/search",
        headers=headers,
        params={"q": query, "type": "track", "limit": min(limit, 10)},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    items = []
    for track in data.get("tracks", {}).get("items", []):
        artists = ", ".join(a["name"] for a in track.get("artists", []))
        album = track.get("album", {})
        images = album.get("images", [])
        # Spotify returns images largest-first; a mid-size one is plenty for a card.
        album_image = images[1]["url"] if len(images) > 1 else (images[0]["url"] if images else None)
        items.append(
            {
                "type": "song",
                "external_id": track["id"],
                "title": f'{track["name"]} — {artists}',
                "genre_tags": "",  # Spotify doesn't give per-track genres directly
                "metadata": json.dumps(
                    {
                        "artists": artists,
                        "album": album.get("name"),
                        "album_image": album_image,
                        "preview_url": track.get("preview_url"),
                    }
                ),
            }
        )
    return items
