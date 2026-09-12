"""
Taste-matching and group recommendation engine.

Approach (deliberately simple so it's easy to explain in a report, but based
on real recommender-systems techniques):

1. Build a user x item ratings matrix (missing ratings = 0).
2. Use cosine similarity between rows to find users with similar taste.
3. Predict a rating for a user on an item they haven't rated yet as a
   similarity-weighted average of ratings from users who HAVE rated it
   (basic user-based collaborative filtering). Falls back to the item's
   global average, then to a neutral 3.0, if there's not enough data.
4. For a GROUP of users, aggregate each member's (real or predicted)
   rating for every candidate item using either:
     - "average": mean of the group's ratings (maximizes overall happiness)
     - "least_misery": minimum of the group's ratings (avoids anyone
       hating the pick — good for movie nights with picky friends)
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.db import get_db


def _build_matrix(db):
    """Returns (user_ids, item_ids, matrix) where matrix[i][j] is the rating
    user_ids[i] gave item_ids[j], or 0 if unrated."""
    users = [row["id"] for row in db.execute("SELECT id FROM users").fetchall()]
    items = [row["id"] for row in db.execute("SELECT id FROM items").fetchall()]

    user_index = {uid: i for i, uid in enumerate(users)}
    item_index = {iid: j for j, iid in enumerate(items)}

    matrix = np.zeros((len(users), len(items)))
    for row in db.execute("SELECT user_id, item_id, rating FROM user_preferences"):
        i = user_index.get(row["user_id"])
        j = item_index.get(row["item_id"])
        if i is not None and j is not None:
            matrix[i, j] = row["rating"]

    return users, items, matrix


def similar_users(user_id, top_n=5):
    """Return [(user_id, similarity_score), ...] for the most taste-similar users."""
    db = get_db()
    users, items, matrix = _build_matrix(db)

    if user_id not in users or matrix.shape[0] < 2:
        return []

    idx = users.index(user_id)
    sims = cosine_similarity(matrix[idx : idx + 1], matrix)[0]

    ranked = sorted(
        ((users[i], sims[i]) for i in range(len(users)) if users[i] != user_id),
        key=lambda pair: pair[1],
        reverse=True,
    )
    return [pair for pair in ranked if pair[1] > 0][:top_n]


def predict_rating(user_id, item_id, users=None, items=None, matrix=None):
    """Predict what `user_id` would rate `item_id`, using similarity-weighted
    collaborative filtering with sensible fallbacks."""
    db = get_db()
    if users is None:
        users, items, matrix = _build_matrix(db)

    if user_id not in users or item_id not in items:
        return 3.0

    u_idx = users.index(user_id)
    i_idx = items.index(item_id)

    # Already rated? Just return the real rating.
    if matrix[u_idx, i_idx] > 0:
        return float(matrix[u_idx, i_idx])

    sims = cosine_similarity(matrix[u_idx : u_idx + 1], matrix)[0]
    raters = [(j, sims[j]) for j in range(len(users)) if matrix[j, i_idx] > 0 and sims[j] > 0]

    if raters:
        weighted_sum = sum(sim * matrix[j, i_idx] for j, sim in raters)
        weight_total = sum(sim for _, sim in raters)
        return float(weighted_sum / weight_total)

    # Fallback: global average rating for this item.
    col = matrix[:, i_idx]
    rated = col[col > 0]
    if len(rated) > 0:
        return float(np.mean(rated))

    return 3.0  # neutral fallback for a brand-new, unrated item


def group_recommendation(user_ids, item_type=None, strategy="average", top_n=10):
    """Rank candidate items for a GROUP of users.

    strategy: "average" (maximize overall satisfaction) or
              "least_misery" (avoid any one person disliking the pick).
    """
    db = get_db()
    users, items, matrix = _build_matrix(db)

    if item_type:
        candidate_rows = db.execute(
            "SELECT id, title, type FROM items WHERE type = ?", (item_type,)
        ).fetchall()
    else:
        candidate_rows = db.execute("SELECT id, title, type FROM items").fetchall()

    results = []
    for row in candidate_rows:
        predicted = [
            predict_rating(uid, row["id"], users, items, matrix) for uid in user_ids
        ]
        if strategy == "least_misery":
            score = min(predicted)
        else:
            score = sum(predicted) / len(predicted)
        results.append(
            {
                "item_id": row["id"],
                "title": row["title"],
                "type": row["type"],
                "score": round(score, 2),
                "individual_scores": [round(p, 2) for p in predicted],
            }
        )

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_n]
