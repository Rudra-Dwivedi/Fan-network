import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    DATABASE_PATH = os.environ.get(
        "DATABASE_PATH", os.path.join(BASE_DIR, "fan_network.db")
    )

    # Fill these in when you're ready to pull real data.
    # Get a free TMDB key at https://www.themoviedb.org/settings/api
    TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")

    # Create a Spotify app at https://developer.spotify.com/dashboard
    SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "")

    # Any sports-data API of your choice (e.g. API-Football, TheSportsDB)
    SPORTS_API_KEY = os.environ.get("SPORTS_API_KEY", "")
