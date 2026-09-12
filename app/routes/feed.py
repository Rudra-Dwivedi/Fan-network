from flask import Blueprint, render_template, request, redirect, url_for, g, flash

from app.db import get_db
from app.auth_utils import login_required
from app.services.sentiment import analyze, label

bp = Blueprint("feed", __name__, url_prefix="/feed")


@bp.route("/", methods=["GET", "POST"])
def feed():
    db = get_db()

    if request.method == "POST":
        if g.user is None:
            flash("Log in to post.")
            return redirect(url_for("auth.login"))

        content = request.form["content"].strip()
        item_id = request.form.get("item_id") or None
        is_pinned = 1 if (g.user["role"] == "admin" and request.form.get("is_pinned")) else 0
        if not content:
            flash("Post can't be empty.")
        else:
            score = analyze(content)
            db.execute(
                "INSERT INTO posts (user_id, item_id, content, sentiment_score, is_pinned) "
                "VALUES (?, ?, ?, ?, ?)",
                (g.user["id"], item_id, content, score, is_pinned),
            )
            db.commit()
            if is_pinned:
                flash("Official announcement published and pinned to feed!")
        return redirect(url_for("feed.feed"))

    posts = db.execute(
        """
        SELECT posts.*, users.username, users.role AS user_role, users.avatar_url, items.title AS item_title
        FROM posts
        JOIN users ON posts.user_id = users.id
        LEFT JOIN items ON posts.item_id = items.id
        ORDER BY posts.is_pinned DESC, posts.created_at DESC
        LIMIT 50
        """
    ).fetchall()

    posts_with_labels = [
        {**dict(post), "sentiment_label": label(post["sentiment_score"])}
        for post in posts
    ]

    items = db.execute("SELECT id, title FROM items ORDER BY title").fetchall()

    return render_template("feed.html", posts=posts_with_labels, items=items)
