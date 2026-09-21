import secrets
import uuid
from pathlib import Path
from flask import Flask, g, render_template, request, session
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException
from app.config import Config, environment_config
from app.extensions import db
from app.logging_config import configure_logging, event
from app.services.security import csrf_token


def create_app(test_config=None):
    root = Path(__file__).resolve().parent.parent
    app = Flask(__name__, template_folder=str(root / "templates"), static_folder=str(root / "static"))
    if test_config is None:
        cls, values = environment_config()
        app.config.from_object(cls)
        app.config.update(values)
    else:
        app.config.from_object(Config)
        app.config.update(test_config)
    db.init_app(app)
    configure_logging(app)
    from app.models import User
    from app.routes import health, auth, products, reviews, orders
    for module in (health, auth, products, reviews, orders):
        app.register_blueprint(module.bp)
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def prepare_request():
        g.request_id = str(uuid.uuid4())
        g.user = None
        # Liveness and readiness must never depend on a session user lookup.
        if request.endpoint in {"health.health", "health.ready", "static"}:
            return None
        if session.get("user_id"):
            g.user = db.session.get(User, session["user_id"])
        if request.method == "POST":
            # Report unauthenticated protected writes as 401 before CSRF validation.
            if request.endpoint in {"reviews.create", "orders.create"} and g.user is None:
                from flask import abort
                abort(401)
            supplied = request.form.get("csrf_token", "")
            expected = session.get("csrf_token", "")
            if not expected or not secrets.compare_digest(supplied, expected):
                from flask import abort
                abort(400)

    @app.after_request
    def finish_request(response):
        response.headers["X-Request-ID"] = g.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "default-src 'self'; form-action 'self'; frame-ancestors 'none'"
        response.headers["Referrer-Policy"] = "same-origin"
        return response

    @app.errorhandler(HTTPException)
    def http_error(error):
        if error.code == 404:
            event("INVALID_PATH", 404)
        elif error.code in {400, 413, 422}:
            event("INPUT_VALIDATION_FAILED", error.code)
        return render_template("error.html", code=error.code), error.code

    @app.errorhandler(Exception)
    def server_error(error):
        db.session.rollback()
        is_db = isinstance(error, SQLAlchemyError)
        code = 503 if is_db else 500
        event("DB_CONNECTION_FAILED" if is_db else "SERVER_ERROR", code)
        return render_template("error.html", code=code), code

    return app
