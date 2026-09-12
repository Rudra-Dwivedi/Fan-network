"""
High-definition media artwork discovery service for movies, songs, and sports teams.
Fetches pristine, high-resolution media artwork using robust public providers:
- Movies: Keyless IMDb official CDN (1000px-4000px studio theatrical posters) or TMDB w780/original, with Wikipedia fallback
- Songs: Apple iTunes Search API (1000x1000 ultra-clear album artwork)
- Sports teams: TheSportsDB public badge API (512x512 transparent PNG crests) with Wikipedia fallback
"""

import json
import logging
import re
import requests

from app.services.settings_store import get_setting

logger = logging.getLogger(__name__)

USER_AGENT = "FanNetwork/1.0 (contact@fannetwork.local)"


def fetch_movie_poster(title):
    """
    Attempt to find high-resolution movie poster:
    1. TMDB (if API key configured in settings) at w780 or original resolution.
    2. Keyless IMDb suggestion API returning 1000px-4000px official studio posters.
    3. Keyless Wikipedia Pageimages API (with 1000px / original) as fallback.
    """
    if not title:
        return None

    clean_title = title.strip()

    # 1. Try TMDB if API key is saved
    try:
        tmdb_key = get_setting("TMDB_API_KEY")
        if tmdb_key:
            resp = requests.get(
                "https://api.themoviedb.org/3/search/movie",
                params={"api_key": tmdb_key, "query": clean_title},
                timeout=6,
            )
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                if results and results[0].get("poster_path"):
                    # Use w780 for crisp, high-definition display
                    return f"https://image.tmdb.org/t/p/w780{results[0]['poster_path']}"
    except Exception as e:
        logger.debug(f"TMDB search error for '{clean_title}': {e}")

    # 2. Keyless High-Definition: IMDb Official CDN
    try:
        slug = re.sub(r"[^a-z0-9]+", "_", clean_title.lower()).strip("_")
        if slug:
            first_char = slug[0]
            url = f"https://v3.sg.media-imdb.com/suggestion/{first_char}/{slug}.json"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
            }
            resp = requests.get(url, headers=headers, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("d", []):
                    img_data = item.get("i")
                    if img_data and img_data.get("imageUrl"):
                        raw_url = img_data["imageUrl"]
                        if "._V1_" in raw_url:
                            base = raw_url.split("._V1_")[0]
                            # Request 1000px wide high-definition studio poster
                            return f"{base}._V1_FMjpg_UX1000_.jpg"
                        return raw_url
    except Exception as e:
        logger.debug(f"IMDb poster lookup error for '{clean_title}': {e}")

    # 3. Fallback: Wikipedia Pageimages API
    try:
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "generator": "search",
                "gsrsearch": f"{clean_title} film",
                "gsrlimit": 1,
                "prop": "pageimages",
                "pilicense": "any",
                "piprop": "thumbnail|original",
                "pithumbsize": 1000,
                "format": "json",
            },
            headers=headers,
            timeout=6,
        )
        if resp.status_code == 200:
            pages = resp.json().get("query", {}).get("pages", {})
            for page in pages.values():
                orig = page.get("original", {}).get("source")
                if orig:
                    return orig
                thumb = page.get("thumbnail", {}).get("source")
                if thumb:
                    return thumb
    except Exception as e:
        logger.debug(f"Wikipedia poster search error for '{clean_title}': {e}")

    return None


def fetch_song_artwork(title):
    """
    Find song album artwork from Apple iTunes Search API in 1000x1000 HD resolution.
    """
    if not title:
        return None

    try:
        search_term = title.replace("—", " ").replace("-", " ").replace("–", " ").strip()
        resp = requests.get(
            "https://itunes.apple.com/search",
            params={"term": search_term, "media": "music", "limit": 1},
            timeout=6,
        )
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            if results and results[0].get("artworkUrl100"):
                raw_art = results[0]["artworkUrl100"]
                # Upgrade standard 100x100 thumbnail to 1000x1000 high-definition artwork
                return raw_art.replace("100x100bb", "1000x1000bb")
    except Exception as e:
        logger.debug(f"iTunes song artwork error for '{title}': {e}")

    return None


def fetch_team_badge(title):
    """
    Find sports team badge or crest from TheSportsDB (512x512 transparent PNG)
    with Wikipedia crest fallback.
    """
    if not title:
        return None

    clean_title = title.strip()
    try:
        resp = requests.get(
            "https://www.thesportsdb.com/api/v1/json/3/searchteams.php",
            params={"t": clean_title},
            timeout=6,
        )
        if resp.status_code == 200:
            teams = resp.json().get("teams") or []
            if teams:
                team = teams[0]
                badge = team.get("strBadge") or team.get("strTeamBadge") or team.get("strTeamLogo")
                if badge:
                    return badge
    except Exception as e:
        logger.debug(f"TheSportsDB badge search error for '{clean_title}': {e}")

    # Fallback: Wikipedia crest/logo
    try:
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "generator": "search",
                "gsrsearch": f"{clean_title} crest logo",
                "gsrlimit": 1,
                "prop": "pageimages",
                "pilicense": "any",
                "piprop": "thumbnail|original",
                "pithumbsize": 800,
                "format": "json",
            },
            headers=headers,
            timeout=6,
        )
        if resp.status_code == 200:
            pages = resp.json().get("query", {}).get("pages", {})
            for page in pages.values():
                orig = page.get("original", {}).get("source")
                if orig:
                    return orig
                thumb = page.get("thumbnail", {}).get("source")
                if thumb:
                    return thumb
    except Exception as e:
        logger.debug(f"Wikipedia team crest search error for '{clean_title}': {e}")

    return None


def fetch_image_for_item(item_type, title):
    """Route item to appropriate provider and return high-definition image URL string or None."""
    if not title or not item_type:
        return None

    clean_title = title.strip()
    if item_type == "movie":
        return fetch_movie_poster(clean_title)
    elif item_type == "song":
        return fetch_song_artwork(clean_title)
    elif item_type == "team":
        return fetch_team_badge(clean_title)

    return None


def enrich_item_metadata(metadata_str, image_url):
    """Inject or update image_url in existing JSON metadata string."""
    try:
        meta = json.loads(metadata_str) if metadata_str else {}
    except (TypeError, ValueError):
        meta = {}

    if image_url:
        meta["image_url"] = image_url

    return json.dumps(meta)
