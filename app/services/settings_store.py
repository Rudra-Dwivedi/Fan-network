"""
Lets API keys be set from the Settings page (stored in the `settings` table)
instead of requiring environment variables. Falls back to app.config /
environment variables if nothing has been saved in the UI yet — so existing
deployments that set env vars keep working unchanged.
"""

from flask import current_app

from app.db import get_db

KNOWN_KEYS = [
    "TMDB_API_KEY",
    "SPOTIFY_CLIENT_ID",
    "SPOTIFY_CLIENT_SECRET",
    "SPORTS_API_KEY",
]


def get_setting(name, fallback=None):
    db = get_db()
    row = db.execute("SELECT value FROM settings WHERE key = ?", (name,)).fetchone()
    if row and row["value"]:
        return row["value"]
    if fallback is not None:
        return fallback
    return current_app.config.get(name, "")


def set_setting(name, value):
    db = get_db()
    db.execute(
        """
        INSERT INTO settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (name, value),
    )
    db.commit()


def all_settings_masked():
    """Return {key: masked_value_or_empty} for display in the settings form."""
    result = {}
    for key in KNOWN_KEYS:
        value = get_setting(key, fallback="")
        if value:
            result[key] = f"••••••••{value[-4:]}" if len(value) > 4 else "••••••••"
        else:
            result[key] = ""
    return result
