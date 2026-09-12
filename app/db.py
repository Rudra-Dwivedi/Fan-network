import sqlite3
import os

from flask import current_app, g


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
    """Create tables from schema.sql if they don't exist yet, and run migrations."""
    with app.app_context():
        db = sqlite3.connect(app.config["DATABASE_PATH"])
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        with open(schema_path, "r") as f:
            db.executescript(f.read())

        # Migration: ensure users table has is_active column
        cursor = db.cursor()
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [row[1] for row in cursor.fetchall()]
        if "is_active" not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")
        if "avatar_url" not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")

        # Migration: ensure posts table has is_pinned column
        cursor.execute("PRAGMA table_info(posts)")
        post_columns = [row[1] for row in cursor.fetchall()]
        if "is_pinned" not in post_columns:
            cursor.execute("ALTER TABLE posts ADD COLUMN is_pinned INTEGER NOT NULL DEFAULT 0")

        db.commit()
        db.close()


def register_db(app):
    app.teardown_appcontext(close_db)
    init_db(app)
