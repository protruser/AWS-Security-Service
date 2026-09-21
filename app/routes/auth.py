from flask import Blueprint, abort, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from app.extensions import db
from app.models import User, LoginAttempt
from app.logging_config import event

bp = Blueprint("auth", __name__)
DUMMY_HASH = generate_password_hash("unused-dummy-comparison")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if not 1 <= len(username) <= 80 or not 1 <= len(password) <= 256:
        abort(400)
    user = db.session.scalar(db.select(User).where(User.username == username))
    valid = check_password_hash(user.password_hash if user else DUMMY_HASH, password)
    success = user is not None and valid
    db.session.add(LoginAttempt(username=username, source_ip=request.remote_addr or "unknown", success=success))
    db.session.commit()
    if not success:
        event("LOGIN_FAILED", 401)
        return render_template("login.html", error="사용자 이름 또는 비밀번호가 올바르지 않습니다."), 401
    session.clear()
    session["user_id"] = user.id
    event("LOGIN_SUCCESS", 302)
    return redirect(url_for("products.index"))


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("products.index"))
