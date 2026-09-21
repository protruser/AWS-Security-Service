"""Local dummy-data tests; sentinels contain no executable attack code."""
import io
import json
import logging
from datetime import timedelta
from unittest.mock import patch

import pytest
from sqlalchemy.exc import OperationalError

from app.extensions import db
from app.logging_config import JsonFormatter
from app.models import LoginAttempt, utcnow
from conftest import login, token


@pytest.fixture
def events(app):
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    app.logger.addHandler(handler)
    yield lambda: [json.loads(line) for line in stream.getvalue().splitlines()]
    app.logger.removeHandler(handler)


@pytest.fixture(autouse=True)
def lab(app):
    app.config.update(VULNERABLE_LAB=True, BRUTE_FORCE_THRESHOLD=3)


@pytest.mark.parametrize("same_account", [False, True])
def test_repeated_failures_detect_without_blocking(client, app, events, same_account):
    for index in range(4):
        response = client.post("/login", data={
            "username": "missing" if same_account else f"missing-{index}",
            "password": "dummy-wrong", "csrf_token": token(client),
        }, environ_overrides={"REMOTE_ADDR": f"127.0.0.{index + 1}" if same_account else "127.0.0.1"})
        assert response.status_code == 401
    with app.app_context():
        attempts = db.session.scalars(db.select(LoginAttempt)).all()
        assert len(attempts) == 4 and all(not row.success for row in attempts)
    suspected = [row for row in events() if row["event_type"] == "BRUTE_FORCE_SUSPECTED"]
    assert len(suspected) == 2
    assert all(row["scenario_id"] == "BRUTE_FORCE" and row["action"] == "DETECTED" for row in suspected)
    assert login(client).status_code == 302
    assert events()[-1]["event_type"] == "LOGIN_SUCCESS"


def test_old_failures_do_not_trigger(client, app, events):
    with app.app_context():
        db.session.add_all([LoginAttempt(username="demo_user1", source_ip="127.0.0.1", success=False,
                                        created_at=utcnow() - timedelta(hours=1)) for _ in range(5)])
        db.session.commit()
    login(client, password="dummy-wrong")
    assert not any(row["event_type"] == "BRUTE_FORCE_SUSPECTED" for row in events())


def test_invalid_login_and_csrf_failures_are_stored(client, app, events):
    assert client.post("/login", data={"username": "dummy"}).status_code == 400
    assert client.post("/login", data={"username": "", "csrf_token": token(client)}).status_code == 400
    with app.app_context():
        assert len(db.session.scalars(db.select(LoginAttempt)).all()) == 2
    assert sum(row["event_type"] == "LOGIN_FAILED" for row in events()) == 2


def test_oversized_login_is_stored(client, app, events):
    assert client.post("/login", data={"password": "s" * 17000}).status_code == 413
    with app.app_context():
        row = db.session.scalar(db.select(LoginAttempt))
        assert row.username == "" and row.success is False
    assert [row["event_type"] for row in events()] == ["LOGIN_FAILED", "INPUT_VALIDATION_FAILED"]


@pytest.mark.parametrize("path", ["/admin", "/backup", "/old", "/config", "/admin/"])
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_dummy_paths(client, events, path, method):
    response = client.open(path, method=method)
    assert response.status_code == 404
    row = events()[-1]
    assert row["event_type"] == "SUSPICIOUS_PATH_REQUEST"
    assert row["scenario_id"] == "DIRECTORY_SEARCH"
    assert row["path"] == path and row["method"] == method and row["status_code"] == 404
    assert row["source_ip"] == "127.0.0.1"
    assert row["request_id"] == response.headers["X-Request-ID"]
    assert row["timestamp"].endswith("Z")


def test_unknown_path(client, events):
    assert client.get("/missing-sentinel").status_code == 404
    assert events()[-1]["event_type"] == "INVALID_PATH"
    assert client.post("/missing-sentinel").status_code == 404
    assert events()[-1]["event_type"] == "INVALID_PATH"


def test_search_and_detection(client, events):
    assert b"Demo Keyboard" in client.get("/search?q=Keyboard").data
    assert b"Demo Keyboard" not in client.get("/search?q=%25").data
    # A standalone keyword, not an SQL statement or executable payload.
    assert client.get("/search?q=select").status_code == 200
    assert any(row["event_type"] == "SUSPICIOUS_SEARCH_INPUT" for row in events())


def test_query_error_is_redacted(client, events):
    with patch("app.routes.products.vulnerable_search", side_effect=OperationalError(
            "private-sql-sentinel", {}, Exception("private-db-sentinel"))):
        response = client.get("/search?q=Keyboard")
    assert response.status_code == 503
    assert events()[-1]["event_type"] == "DATABASE_QUERY_ERROR"
    combined = response.get_data(as_text=True) + json.dumps(events())
    assert "private-sql-sentinel" not in combined and "private-db-sentinel" not in combined


def test_reviews_and_validation(client, events):
    login(client)
    for content in ["normal-dummy-review", "<b>review-sentinel</b>"]:
        assert client.post("/products/1/reviews", data={"content": content, "csrf_token": token(client)}).status_code == 303
    response = client.get("/products/1/reviews")
    assert b"normal-dummy-review" in response.data
    assert b"<b>review-sentinel</b>" in response.data
    assert "script-src 'unsafe-inline'" in response.headers["Content-Security-Policy"]
    assert "unsafe-inline" not in client.get("/products").headers["Content-Security-Policy"]
    assert client.post("/products/1/reviews", data={"content": " ", "csrf_token": token(client)}).status_code == 400
    assert any(row["event_type"] == "SUSPICIOUS_REVIEW_INPUT" and row["scenario_id"] == "XSS" for row in events())
    assert events()[-1]["event_type"] == "INPUT_VALIDATION_FAILED"
    assert events()[-1]["scenario_id"] == "XSS"


def test_event_contract_and_secrets(client, app, events):
    client.set_cookie("dummy", "private-cookie-sentinel")
    with client.session_transaction() as session:
        session["private"] = "private-session-sentinel"
    csrf = token(client)
    client.post("/login", data={"username": "missing", "password": "private-password-sentinel", "csrf_token": csrf},
                headers={"Authorization": "Bearer private-bearer-sentinel", "X-Forwarded-For": "192.0.2.9"})
    serialized = json.dumps(events())
    for secret in ["private-cookie-sentinel", "private-session-sentinel", "private-password-sentinel",
                   "private-bearer-sentinel", csrf, app.config["SECRET_KEY"]]:
        assert secret not in serialized
    for row in events():
        assert row["source"] == "SHOP_APP" and row["target"] == "shop-flask"
        assert row["source_ip"] == "127.0.0.1"
    assert len({row["event_id"] for row in events()}) == len(events())


def test_lab_health_and_ready(client):
    assert client.get("/health").json["status"] == "healthy"
    assert client.get("/ready").json["status"] == "ready"
