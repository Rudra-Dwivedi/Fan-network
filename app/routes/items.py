from flask import Blueprint, render_template, request, redirect, url_for, g, flash

from app.db import get_db
from app.auth_utils import login_required
from app.services.item_media import with_image_urls

bp = Blueprint("items", __name__, url_prefix="/items")


@bp.route("/")
def browse():
    """Browse items, optionally filtered by type: movie | song | team."""
    item_type = request.args.get("type")
    db = get_db()

    if item_type in ("movie", "song", "team"):
        items = db.execute(
            "SELECT * FROM items WHERE type = ? ORDER BY title", (item_type,)
        ).fetchall()
    else:
        items = db.execute("SELECT * FROM items ORDER BY type, title").fetchall()

    items = with_image_urls(items)

    user_ratings = {}
    if g.user is not None:
        rows = db.execute(
            "SELECT item_id, rating FROM user_preferences WHERE user_id = ?",
            (g.user["id"],),
        ).fetchall()
        user_ratings = {row["item_id"]: row["rating"] for row in rows}

    return render_template(
        "items.html", items=items, active_type=item_type, user_ratings=user_ratings
    )


@bp.route("/<int:item_id>/rate", methods=["POST"])
@login_required
def rate(item_id):
    rating = int(request.form["rating"])
    if rating < 1 or rating > 5:
        flash("Rating must be between 1 and 5.")
        return redirect(url_for("items.browse"))

    db = get_db()
    db.execute(
        """
        INSERT INTO user_preferences (user_id, item_id, rating)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, item_id) DO UPDATE SET rating = excluded.rating
        """,
        (g.user["id"], item_id, rating),
    )
    db.commit()
    return redirect(request.referrer or url_for("items.browse"))
