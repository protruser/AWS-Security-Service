import uuid
from pathlib import Path
from flask import Flask, g, render_template, request, session
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix
from app.config import Config, environment_config
from app.extensions import db
from app.logging_config import configure_logging, event
from app.services.lab import SUSPICIOUS_PATHS, record_login_attempt


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
    if app.config["TRUST_PROXY_HEADERS"]:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    db.init_app(app)
    configure_logging(app)
    from app.models import User
    from app.routes import health, auth, products, reviews, orders
    for module in (health, auth, products, reviews, orders):
        app.register_blueprint(module.bp)
    @app.before_request
    def prepare_request():
        g.request_id = str(uuid.uuid4())
        g.user = None
        # Dummy directory-search paths: no files or administrator functionality.
        if (request.path.rstrip("/") in SUSPICIOUS_PATHS
                or getattr(request.routing_exception, "code", None) == 404):
            from flask import abort
            abort(404)
        # Liveness and readiness must never depend on a session user lookup.
        if request.endpoint in {"health.health", "health.ready", "static"}:
            return None
        if session.get("user_id"):
            g.user = db.session.get(User, session["user_id"])
        if (request.method == "POST" and request.endpoint in {"reviews.create", "orders.create"}
                and g.user is None):
            from flask import abort
            abort(401)

    @app.after_request
    def finish_request(response):
        response.headers["X-Request-ID"] = g.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "default-src 'self'; form-action 'self'; frame-ancestors 'none'"
        if app.config["VULNERABLE_LAB"] and request.endpoint == "reviews.index":
            # vuln_service only: allow inline execution for the XSS lesson.
            # Other pages retain their CSP; external resources remain disallowed.
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; script-src 'unsafe-inline'; style-src 'self'; "
                "form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
            )
        response.headers["Referrer-Policy"] = "same-origin"
        return response

    @app.errorhandler(HTTPException)
    def http_error(error):
        if (request.endpoint == "auth.login" and request.method == "POST"
                and error.code in {400, 413, 422} and not getattr(g, "login_attempt_recorded", False)):
            # Oversized/malformed bodies cannot safely be parsed for an account.
            record_login_attempt("", False, error.code)
        if error.code == 404:
            event("SUSPICIOUS_PATH_REQUEST" if request.path.rstrip("/") in SUSPICIOUS_PATHS else "INVALID_PATH", 404)
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
