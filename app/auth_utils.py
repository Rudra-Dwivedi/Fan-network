from functools import wraps

from flask import session, redirect, url_for, g, abort

from app.db import get_db


def load_logged_in_user():
    """Run before every request: attach the current user (or None) to g.user."""
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        db = get_db()
        user = db.execute(
            "SELECT id, username, email, role, is_active, avatar_url FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if user is None or not user["is_active"]:
            session.clear()
            g.user = None
        else:
            g.user = user


def login_required(view):
    """Require any logged-in user (regular or admin)."""

    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view


def admin_required(view):
    """Require a logged-in user with the 'admin' role. Regular users get a 403,
    logged-out visitors get sent to the admin login page."""

    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("admin.login"))
        if g.user["role"] != "admin":
            abort(403)
        return view(**kwargs)

    return wrapped_view
