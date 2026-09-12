from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.db import get_db
from app.auth_utils import admin_required
from app.services.settings_store import set_setting, all_settings_masked
from app.services import tmdb_client, spotify_client, sports_client

bp = Blueprint("settings", __name__, url_prefix="/settings")


@bp.route("/", methods=["GET", "POST"])
@admin_required
def api_keys():
    if request.method == "POST":
        for field in ("tmdb_api_key", "spotify_client_id", "spotify_client_secret", "sports_api_key"):
            value = request.form.get(field, "").strip()
            if value:  # only overwrite if the person actually typed something new
                set_setting(field.upper(), value)
        flash("API keys saved.")
        return redirect(url_for("settings.api_keys"))

    return render_template("settings.html", saved=all_settings_masked())


@bp.route("/fetch/movies", methods=["POST"])
@admin_required
def fetch_movies():
    try:
        db = get_db()
        items = tmdb_client.fetch_popular_movies()
        tmdb_client.save_items(db, items)
        flash(f"Loaded {len(items)} popular movies from TMDB.")
    except Exception as e:
        flash(f"Couldn't fetch movies: {e}")
    return redirect(url_for("settings.api_keys"))


@bp.route("/fetch/music", methods=["POST"])
@admin_required
def fetch_music():
    query = request.form.get("query", "").strip()
    if not query:
        flash("Type an artist, song, or genre to search for first.")
        return redirect(url_for("settings.api_keys"))
    try:
        db = get_db()
        items = spotify_client.fetch_tracks_by_search(query)
        tmdb_client.save_items(db, items)  # save_items is format-agnostic, works for any item dict
        flash(f"Loaded {len(items)} tracks matching '{query}'.")
    except Exception as e:
        flash(f"Couldn't fetch tracks: {e}")
    return redirect(url_for("settings.api_keys"))


@bp.route("/fetch/sports", methods=["POST"])
@admin_required
def fetch_sports():
    league = request.form.get("league", "").strip()
    if not league:
        flash("Enter a league name first, e.g. 'English Premier League'.")
        return redirect(url_for("settings.api_keys"))
    try:
        db = get_db()
        items = sports_client.fetch_teams_by_league(league)
        tmdb_client.save_items(db, items)
        flash(f"Loaded {len(items)} teams from {league}.")
    except Exception as e:
        flash(f"Couldn't fetch teams: {e}")
    return redirect(url_for("settings.api_keys"))
