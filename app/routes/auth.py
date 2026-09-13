import os
import sqlite3
import uuid

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    g,
    current_app,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from app.db import get_db
from app.auth_utils import login_required

bp = Blueprint("auth", __name__, url_prefix="/auth")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Manage personal profile settings and profile photo."""
    db = get_db()
    if request.method == "POST":
        action = request.form.get("action")

        # 1. Remove photo action
        if action == "remove":
            db.execute("UPDATE users SET avatar_url = NULL WHERE id = ?", (g.user["id"],))
            db.commit()
            flash("Profile photo removed. Your avatar now shows your initial.")
            return redirect(url_for("auth.profile"))

        # 2. File upload action
        file = request.files.get("avatar_file")
        if file and file.filename != "":
            if not allowed_file(file.filename):
                flash("Invalid image format. Allowed formats: PNG, JPG, JPEG, GIF, WEBP.")
                return redirect(url_for("auth.profile"))

            ext = file.filename.rsplit(".", 1)[1].lower()
            safe_name = f"avatar_{g.user['id']}_{uuid.uuid4().hex[:8]}.{ext}"
            upload_folder = os.path.join(current_app.root_path, "static", "avatars")
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, safe_name)
            file.save(file_path)

            new_url = url_for("static", filename=f"avatars/{safe_name}")
            db.execute("UPDATE users SET avatar_url = ? WHERE id = ?", (new_url, g.user["id"]))
            db.commit()
            flash("Profile photo updated successfully!")
            return redirect(url_for("auth.profile"))

        # 3. Image URL action
        avatar_url = request.form.get("avatar_url", "").strip()
        if avatar_url:
            if not (avatar_url.startswith("http://") or avatar_url.startswith("https://") or avatar_url.startswith("/static/")):
                flash("Please enter a valid image URL starting with http:// or https://")
                return redirect(url_for("auth.profile"))

            db.execute("UPDATE users SET avatar_url = ? WHERE id = ?", (avatar_url, g.user["id"]))
            db.commit()
            flash("Profile photo updated successfully!")
            return redirect(url_for("auth.profile"))

        flash("Please choose an image file to upload or enter an image web URL.")
        return redirect(url_for("auth.profile"))

    return render_template("profile_edit.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]

        error = None
        if not username or not email or not password:
            error = "Username, email, and password are all required."

        if error is None:
            db = get_db()
            try:
                db.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (username, email, generate_password_hash(password)),
                )
                db.commit()
            except sqlite3.IntegrityError:
                error = f"Username or email already taken."
            else:
                flash("Account created — you can log in now.")
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        db = get_db()
        error = None

        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            error = "Incorrect username or password."
        elif not user["is_active"]:
            error = "Your account has been deactivated or suspended by an administrator."
        elif user["role"] == "admin":
            error = "Admin accounts log in from the admin login page, not here."

        if error is None:
            db.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user["id"],)
            )
            db.commit()
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("index"))

        flash(error)

    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
