from flask import Blueprint, abort, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from app.extensions import db
from app.models import User
from app.services.lab import record_login_attempt

bp = Blueprint("auth", __name__)
DUMMY_HASH = generate_password_hash("unused-dummy-comparison")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if not 1 <= len(username) <= 80 or not 1 <= len(password) <= 256:
        record_login_attempt(username, False, 400)
        abort(400)
    user = db.session.scalar(db.select(User).where(User.username == username))
    valid = check_password_hash(user.password_hash if user else DUMMY_HASH, password)
    success = user is not None and valid
    record_login_attempt(username, success, 302 if success else 401)
    if not success:
        return render_template("login.html", error="사용자 이름 또는 비밀번호가 올바르지 않습니다."), 401
    session.clear()
    session["user_id"] = user.id
    return redirect(url_for("products.index"))


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("products.index"))
