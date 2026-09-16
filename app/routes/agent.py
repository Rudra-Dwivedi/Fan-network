"""
Routes for the AI Movie Agent.
Allows users to ask questions about films, view ratings analytics,
and discover cinema recommendations.
"""

from flask import Blueprint, render_template, request, jsonify
from app.db import get_db
from app.services.movie_agent import ask_movie_agent

bp = Blueprint("agent", __name__, url_prefix="/agent")


@bp.route("/", methods=["GET"])
def index():
    """Render Movie Agent chat interface with optional initial query."""
    query = request.args.get("q", "").strip()
    initial_response = None
    if query:
        initial_response = ask_movie_agent(query)

    db = get_db()
    movies = db.execute(
        "SELECT id, title FROM items WHERE type = 'movie' ORDER BY title"
    ).fetchall()

    return render_template(
        "movie_agent.html",
        initial_query=query,
        initial_response=initial_response,
        catalog_movies=movies,
    )


@bp.route("/ask", methods=["POST"])
def ask():
    """JSON API endpoint for asynchronous Movie Agent conversation."""
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "Please enter a question or movie name."}), 400

    response = ask_movie_agent(query)
    return jsonify(response)

