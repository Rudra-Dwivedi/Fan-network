"""
Populates the database with sample movies/songs/teams and a few demo users
with ratings, so you can see similarity matching and group recommendations
working immediately — no API keys required.

Run with:  python seed_demo_data.py
"""

import json
import random

from werkzeug.security import generate_password_hash

from app import create_app
from app.db import get_db

SAMPLE_ITEMS = [
    ("movie", "Inception", "sci-fi,thriller", "https://m.media-amazon.com/images/M/MV5BMjAxMzY3NjcxNF5BMl5BanBnXkFtZTcwNTI5OTM0Mw@@._V1_FMjpg_UX1000_.jpg"),
    ("movie", "The Dark Knight", "action,crime", "https://m.media-amazon.com/images/M/MV5BMTMxNTMwODM0NF5BMl5BanBnXkFtZTcwODAyMTk2Mw@@._V1_FMjpg_UX1000_.jpg"),
    ("movie", "La La Land", "musical,romance", "https://m.media-amazon.com/images/M/MV5BMDllYjliOTUtMDJjZC00ODIzLWJmNGMtOWI2NzQxMjA2NzdlXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"),
    ("movie", "Parasite", "thriller,drama", "https://m.media-amazon.com/images/M/MV5BYjk1Y2U4MjQtY2ZiNS00OWQyLWI3MmYtZWUwNmRjYWRiNWNhXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"),
    ("movie", "The Grand Budapest Hotel", "comedy,drama", "https://m.media-amazon.com/images/M/MV5BMzM5NjUxOTEyMl5BMl5BanBnXkFtZTgwNjEyMDM0MDE@._V1_FMjpg_UX1000_.jpg"),
    ("song", "Blinding Lights — The Weeknd", "pop,synthwave", "https://is1-ssl.mzstatic.com/image/thumb/Music115/v4/61/e7/3f/61e73f94-018d-5f50-50ec-8521952bc72e/20UM1IM11629.rgb.jpg/1000x1000bb.jpg"),
    ("song", "HUMBLE. — Kendrick Lamar", "hip-hop", "https://is1-ssl.mzstatic.com/image/thumb/Music112/v4/ab/16/ef/ab16efe9-e7f1-66ec-021c-5592a23f0f9e/17UMGIM88793.rgb.jpg/1000x1000bb.jpg"),
    ("song", "Bohemian Rhapsody — Queen", "rock", "https://is1-ssl.mzstatic.com/image/thumb/Music115/v4/4d/08/2a/4d082a9e-7898-1aa1-a02f-339810058d9e/14DMGIM05632.rgb.jpg/1000x1000bb.jpg"),
    ("song", "As It Was — Harry Styles", "pop", "https://is1-ssl.mzstatic.com/image/thumb/Music126/v4/2a/19/fb/2a19fb85-2f70-9e44-f2a9-82abe679b88e/886449990061.jpg/1000x1000bb.jpg"),
    ("song", "Levitating — Dua Lipa", "pop,dance", "https://is1-ssl.mzstatic.com/image/thumb/Music116/v4/6c/11/d6/6c11d681-aa3a-d59e-4c2e-f77e181026ab/190295092665.jpg/1000x1000bb.jpg"),
    ("team", "Mumbai Indians", "cricket,IPL", "https://r2.thesportsdb.com/images/media/team/badge/l40j8p1487678631.png"),
    ("team", "Real Madrid", "football,La Liga", "https://r2.thesportsdb.com/images/media/team/badge/vwvwrw1473502969.png"),
    ("team", "Los Angeles Lakers", "basketball,NBA", "https://r2.thesportsdb.com/images/media/team/badge/d8uoxw1714254511.png"),
    ("team", "Chennai Super Kings", "cricket,IPL", "https://r2.thesportsdb.com/images/media/team/badge/okceh51487601098.png"),
    ("team", "Manchester United", "football,Premier League", "https://r2.thesportsdb.com/images/media/team/badge/xzqdr11517660252.png"),
]

DEMO_USERS = ["asha", "rohan", "priya", "vikram"]


def run():
    app = create_app()
    with app.app_context():
        db = get_db()

        item_ids = []
        for item_type, title, tags, img_url in SAMPLE_ITEMS:
            cur = db.execute(
                "INSERT INTO items (type, external_id, title, genre_tags, metadata) "
                "VALUES (?, NULL, ?, ?, ?)",
                (item_type, title, tags, json.dumps({"image_url": img_url})),
            )
            item_ids.append(cur.lastrowid)
        db.commit()

        user_ids = []
        for username in DEMO_USERS:
            cur = db.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, f"{username}@example.com", generate_password_hash("password123")),
            )
            user_ids.append(cur.lastrowid)

        # A demo admin account so the Settings page has something to log into
        # without needing to run create_admin.py separately.
        db.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, 'admin')",
            ("admin", "admin@example.com", generate_password_hash("admin123")),
        )
        db.commit()

        # Give each demo user random-ish ratings on a subset of items so
        # similarity matching and group recommendations have something to work with.
        random.seed(42)
        for uid in user_ids:
            rated_items = random.sample(item_ids, k=len(item_ids) // 2)
            for item_id in rated_items:
                rating = random.randint(2, 5)
                db.execute(
                    "INSERT INTO user_preferences (user_id, item_id, rating) VALUES (?, ?, ?)",
                    (uid, item_id, rating),
                )
        db.commit()

        print(f"Seeded {len(item_ids)} items and {len(user_ids)} demo users.")
        print("Demo login: username 'asha' / 'rohan' / 'priya' / 'vikram', password 'password123'")
        print("Demo admin login (at /admin/login): username 'admin', password 'admin123'")


if __name__ == "__main__":
    run()
