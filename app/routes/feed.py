from flask import Blueprint, render_template, request, redirect, url_for, g, flash

from app.db import get_db
from app.auth_utils import login_required
from app.services.sentiment import analyze, label
from app.services.item_media import resolve_image_url

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

    filter_tab = request.args.get("filter", "all")

    # Base query
    query = """
        SELECT posts.*, 
               users.username, users.role AS user_role, users.avatar_url, 
               items.title AS item_title, items.type AS item_type, items.metadata AS item_metadata,
               COALESCE(ROUND((SELECT AVG(rating) FROM user_preferences WHERE item_id = items.id), 1), 0) AS item_avg_rating
        FROM posts
        JOIN users ON posts.user_id = users.id
        LEFT JOIN items ON posts.item_id = items.id
    """
    params = []

    if filter_tab == "pinned":
        query += " WHERE posts.is_pinned = 1"
    elif filter_tab == "positive":
        query += " WHERE posts.sentiment_score > 0.15"
    elif filter_tab in ("movie", "song", "team"):
        query += " WHERE items.type = ?"
        params.append(filter_tab)

    query += " ORDER BY posts.is_pinned DESC, posts.created_at DESC LIMIT 50"
    posts = db.execute(query, params).fetchall()

    posts_with_labels = []
    for post in posts:
        post_dict = dict(post)
        post_dict["sentiment_label"] = label(post["sentiment_score"])
        # Resolve tagged item image if present
        if post["item_title"]:
            item_mock = {
                "type": post["item_type"],
                "title": post["item_title"],
                "metadata": post["item_metadata"]
            }
            post_dict["item_image_url"] = resolve_image_url(item_mock)
        else:
            post_dict["item_image_url"] = None
        posts_with_labels.append(post_dict)

    # Popular / Trending tagged items in feed
    trending_items = db.execute(
        """
        SELECT i.id, i.title, i.type, i.metadata, COUNT(p.id) AS post_count
        FROM items i
        JOIN posts p ON i.id = p.item_id
        GROUP BY i.id
        ORDER BY post_count DESC
        LIMIT 5
        """
    ).fetchall()

    all_items = db.execute("SELECT id, title, type FROM items ORDER BY type, title").fetchall()

    return render_template(
        "feed.html",
        posts=posts_with_labels,
        items=all_items,
        active_filter=filter_tab,
        trending_items=trending_items,
    )
