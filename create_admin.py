"""
Creates (or promotes an existing user to) an admin account.

Admins aren't created through the public registration form on purpose —
that's a deliberate security choice: only someone with server/database
access can provision an admin. Run this once to set one up:

    python create_admin.py
"""

import getpass
import sqlite3

from werkzeug.security import generate_password_hash

from app import create_app
from app.db import get_db


def run():
    app = create_app()
    with app.app_context():
        db = get_db()

        username = input("Admin username: ").strip()
        existing = db.execute(
            "SELECT id, role FROM users WHERE username = ?", (username,)
        ).fetchone()

        if existing:
            if existing["role"] == "admin":
                print(f"'{username}' is already an admin.")
                return
            db.execute(
                "UPDATE users SET role = 'admin' WHERE id = ?", (existing["id"],)
            )
            db.commit()
            print(f"Promoted existing user '{username}' to admin.")
            return

        email = input("Admin email: ").strip()
        password = getpass.getpass("Admin password: ")

        try:
            db.execute(
                "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, 'admin')",
                (username, email, generate_password_hash(password)),
            )
            db.commit()
            print(f"Admin account '{username}' created. Log in at /admin/login.")
        except sqlite3.IntegrityError:
            print("That username or email is already taken.")


if __name__ == "__main__":
    run()
