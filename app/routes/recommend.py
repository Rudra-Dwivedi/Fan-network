from flask import Blueprint, render_template, request, g, redirect, url_for, flash, abort

from app.db import get_db
from app.auth_utils import login_required
from app.services.recommender import similar_users, group_recommendation
from app.services.item_media import resolve_image_url, with_image_urls
from app.services.sentiment import label

bp = Blueprint("recommend", __name__, url_prefix="/recommend")


@bp.route("/people")
@login_required
def people():
    """Show users with the most similar taste, so you can follow them."""
    matches = similar_users(g.user["id"], top_n=10)

    db = get_db()
    following_ids = {
        row["followed_id"]
        for row in db.execute(
            "SELECT followed_id FROM follows WHERE follower_id = ?", (g.user["id"],)
        ).fetchall()
    }

    results = []
    for uid, score in matches:
        user = db.execute(
            "SELECT id, username, avatar_url FROM users WHERE id = ?", (uid,)
        ).fetchone()
        if user:
            results.append(
                {
                    "user": user,
                    "score": round(float(score), 3),
                    "following": user["id"] in following_ids,
                }
            )

    return render_template("similar_people.html", matches=results)


@bp.route("/follow/<int:user_id>", methods=["POST"])
@login_required
def follow(user_id):
    db = get_db()
    db.execute(
        "INSERT OR IGNORE INTO follows (follower_id, followed_id) VALUES (?, ?)",
        (g.user["id"], user_id),
    )
    db.commit()
    return redirect(request.referrer or url_for("recommend.people"))


@bp.route("/unfollow/<int:user_id>", methods=["POST"])
@login_required
def unfollow(user_id):
    db = get_db()
    db.execute(
        "DELETE FROM follows WHERE follower_id = ? AND followed_id = ?",
        (g.user["id"], user_id),
    )
    db.commit()
    return redirect(request.referrer or url_for("recommend.people"))


@bp.route("/user/<username>")
def profile(username):
    """Public user profile showing someone's taste, ratings, and feed activity."""
    db = get_db()
    user = db.execute(
        "SELECT id, username, role, is_active, created_at, avatar_url FROM users WHERE username = ?",
        (username,),
    ).fetchone()

    if user is None:
        abort(404)

    if not user["is_active"] and (g.user is None or g.user["role"] != "admin"):
        abort(404)

    # User ratings with media
    ratings = db.execute(
        """
        SELECT r.rating, r.created_at, i.id as item_id, i.title, i.type, i.genre_tags, i.metadata
        FROM user_preferences r
        JOIN items i ON r.item_id = i.id
        WHERE r.user_id = ?
        ORDER BY r.rating DESC, r.created_at DESC
        """,
        (user["id"],),
    ).fetchall()
    ratings_with_media = with_image_urls(ratings)

    # User posts
    posts = db.execute(
        """
        SELECT p.*, i.title as item_title, i.type as item_type
        FROM posts p
        LEFT JOIN items i ON p.item_id = i.id
        WHERE p.user_id = ?
        ORDER BY p.is_pinned DESC, p.created_at DESC
        LIMIT 20
        """,
        (user["id"],),
    ).fetchall()
    posts_with_labels = [
        {**dict(p), "sentiment_label": label(p["sentiment_score"])}
        for p in posts
    ]

    # Follow counts & state
    followers_count = db.execute(
        "SELECT COUNT(*) as c FROM follows WHERE followed_id = ?", (user["id"],)
    ).fetchone()["c"]

    following_count = db.execute(
        "SELECT COUNT(*) as c FROM follows WHERE follower_id = ?", (user["id"],)
    ).fetchone()["c"]

    is_following = False
    if g.user is not None and g.user["id"] != user["id"]:
        f = db.execute(
            "SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = ?",
            (g.user["id"], user["id"]),
        ).fetchone()
        is_following = f is not None

    return render_template(
        "user_profile.html",
        profile_user=user,
        ratings=ratings_with_media,
        posts=posts_with_labels,
        followers_count=followers_count,
        following_count=following_count,
        is_following=is_following,
    )


@bp.route("/group", methods=["GET", "POST"])
@login_required
def group():
    """Pick a group of users and get a ranked group recommendation."""
    db = get_db()
    # Only show members the logged-in user is following (excluding admins and suspended accounts)
    all_users = db.execute(
        """
        SELECT u.id, u.username, u.avatar_url
        FROM follows f
        JOIN users u ON f.followed_id = u.id
        WHERE f.follower_id = ? AND u.role != 'admin' AND u.is_active = 1
        ORDER BY u.username
        """,
        (g.user["id"],),
    ).fetchall()

    winner = None
    runner_ups = []
    winner_members = []
    explanation = None
    selected_ids = []
    strategy = "average"
    item_type = None

    if request.method == "POST":
        valid_uids = {row["id"] for row in all_users}
        selected_ids = [int(uid) for uid in request.form.getlist("user_ids") if int(uid) in valid_uids]
        strategy = request.form.get("strategy", "average")
        item_type = request.form.get("item_type") or None

        if g.user["id"] not in selected_ids:
            selected_ids.append(g.user["id"])

        if len(selected_ids) < 2:
            flash("Pick at least one other person to form a group.")
        else:
            recommendations = group_recommendation(
                selected_ids, item_type=item_type, strategy=strategy, top_n=10
            )
            for rec in recommendations:
                item_row = db.execute(
                    "SELECT * FROM items WHERE id = ?", (rec["item_id"],)
                ).fetchone()
                rec["image_url"] = resolve_image_url(item_row) if item_row else None

            if recommendations:
                winner = recommendations[0]
                runner_ups = recommendations[1:]

                member_rows = [
                    db.execute(
                        "SELECT id, username, avatar_url FROM users WHERE id = ?", (uid,)
                    ).fetchone()
                    for uid in selected_ids
                ]
                winner_members = list(zip(member_rows, winner["individual_scores"]))

                if strategy == "least_misery":
                    lowest = min(winner["individual_scores"])
                    explanation = (
                        f"Nobody in the group is predicted to rate this below "
                        f"{lowest} / 5 — the safest pick for a picky group."
                    )
                else:
                    explanation = (
                        f"Averaged across the group, this scores {winner['score']} / 5 "
                        f"— the highest combined score of anything considered."
                    )

    return render_template(
        "group_recommend.html",
        all_users=all_users,
        winner=winner,
        winner_members=winner_members,
        explanation=explanation,
        runner_ups=runner_ups,
        selected_ids=selected_ids,
        strategy=strategy,
        item_type=item_type,
    )
