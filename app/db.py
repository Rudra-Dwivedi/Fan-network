import json
import os
import sqlite3

from flask import current_app, g
from werkzeug.security import generate_password_hash

DEFAULT_CATALOG_ITEMS = [
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


def get_db():
    """Return a request-scoped SQLite connection with row access by column name."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    """Create tables from schema.sql if they don't exist yet, run migrations, and seed initial data."""
    with app.app_context():
        db = sqlite3.connect(app.config["DATABASE_PATH"])
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        with open(schema_path, "r", encoding="utf-8") as f:
            db.executescript(f.read())

        cursor = db.cursor()

        # Migration: ensure users table has is_active and avatar_url columns
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [row[1] for row in cursor.fetchall()]
        if "is_active" not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")
        if "avatar_url" not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
        if "last_login" not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")

        # Migration: ensure posts table has is_pinned column
        cursor.execute("PRAGMA table_info(posts)")
        post_columns = [row[1] for row in cursor.fetchall()]
        if "is_pinned" not in post_columns:
            cursor.execute("ALTER TABLE posts ADD COLUMN is_pinned INTEGER NOT NULL DEFAULT 0")

        # Seed initial catalog items if catalog is empty (ensures immediate usability in production)
        cursor.execute("SELECT COUNT(*) FROM items")
        if cursor.fetchone()[0] == 0:
            for item_type, title, tags, img_url in DEFAULT_CATALOG_ITEMS:
                cursor.execute(
                    "INSERT INTO items (type, title, genre_tags, metadata) VALUES (?, ?, ?, ?)",
                    (item_type, title, tags, json.dumps({"image_url": img_url})),
                )

        # Optional auto-provision of admin via environment variables (e.g. Railway Variables)
        admin_user = os.environ.get("ADMIN_USERNAME", "").strip()
        admin_pass = os.environ.get("ADMIN_PASSWORD", "").strip()
        if admin_user and admin_pass:
            admin_email = os.environ.get("ADMIN_EMAIL", f"{admin_user}@fannetwork.local").strip()
            cursor.execute("SELECT id, role FROM users WHERE username = ?", (admin_user,))
            existing = cursor.fetchone()
            if not existing:
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, 'admin')",
                    (admin_user, admin_email, generate_password_hash(admin_pass)),
                )
            elif existing[1] != "admin":
                cursor.execute("UPDATE users SET role = 'admin' WHERE id = ?", (existing[0],))

        db.commit()
        db.close()


def register_db(app):
    app.teardown_appcontext(close_db)
    init_db(app)
