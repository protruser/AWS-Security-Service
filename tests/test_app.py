import io
import json
import logging
from unittest.mock import patch
from sqlalchemy.exc import OperationalError
from app.extensions import db
from app.models import LoginAttempt, Order, Product, Review
from app.logging_config import JsonFormatter
from conftest import login


def test_health_and_request_id(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json == {"status": "healthy", "service": "shop-app"}
    assert response.headers["X-Request-ID"] != client.get("/health").headers["X-Request-ID"]


def test_readiness_and_liveness_without_database(client):
    assert client.get("/ready").status_code == 200
    with client.session_transaction() as session:
        session["user_id"] = 1
    with patch.object(db.session, "execute", side_effect=OperationalError("secret SQL", {}, Exception("secret"))):
        assert client.get("/health").status_code == 200
        response = client.get("/ready")
        assert response.status_code == 503
        assert response.json["database"] == "disconnected"


def test_not_found(client):
    assert client.get("/missing").status_code == 404


def test_products_and_search(client):
    for path in ["/", "/products", "/products/1", "/search?q=Keyboard"]:
        response = client.get(path)
        assert response.status_code == 200
        assert b"Demo Keyboard" in response.data
    for query in ["absent", "' OR 1=1 --", "%"]:
        assert b"Demo Keyboard" not in client.get("/search", query_string={"q": query}).data
    assert client.get("/search", query_string={"q": "a" * 121}).status_code == 400


def test_login_success(client, app):
    assert login(client).status_code == 302
    with client.session_transaction() as session:
        assert session["user_id"] == 1
    with app.app_context():
        assert db.session.scalar(db.select(LoginAttempt)).success is True


def test_login_failure(client, app):
    assert login(client, password="incorrect").status_code == 401
    assert login(client, username="unknown").status_code == 401
    with client.session_transaction() as session:
        assert "user_id" not in session
    with app.app_context():
        assert len(db.session.scalars(db.select(LoginAttempt).where(LoginAttempt.success.is_(False))).all()) == 2


def test_unauthenticated_writes(client):
    assert client.post("/products/1/reviews", data={"content": "hello"}).status_code == 401
    assert client.post("/orders", data={"product_id": 1, "quantity": 1}).status_code == 401
    assert client.get("/orders").status_code == 401


def test_login_and_logout_without_token(client):
    assert client.post("/login", data={"username": "user1", "password": "1234"}).status_code == 302
    assert client.post("/logout").status_code == 302
    assert client.get("/orders").status_code == 401


def test_review_validation_and_escaping(client, app):
    login(client)
    assert client.post("/products/1/reviews", data={"content": " "}).status_code == 400
    assert client.post("/products/1/reviews", data={"content": "x" * 2001}).status_code == 400
    assert client.post("/products/1/reviews", data={"content": "<script>alert(1)</script>"}).status_code == 303
    response = client.get("/products/1/reviews")
    assert b"&lt;script&gt;" in response.data
    assert b"<script>" not in response.data
    with app.app_context():
        assert db.session.scalar(db.select(Review)).user_id == 1


def test_orders_stock_and_ownership(client, app):
    login(client)
    for quantity in ["no", "0", "-1", "101"]:
        assert client.post("/orders", data={"product_id": 1, "quantity": quantity}).status_code == 400
    assert client.post("/orders", data={"product_id": 999, "quantity": 1}).status_code == 404
    assert client.post("/orders", data={"product_id": 1, "quantity": 6}).status_code == 409
    assert client.post("/orders", data={"product_id": 1, "quantity": 2}).status_code == 303
    assert b"Demo Keyboard" in client.get("/orders").data
    with app.app_context():
        assert db.session.get(Product, 1).stock == 3
        order = db.session.scalar(db.select(Order))
        assert order.total_price == 24000
        assert order.items[0].quantity == 2
    login(client, "user2", "password")
    assert b"Demo Keyboard" not in client.get("/orders").data


def test_json_logs_exclude_secrets(client, app):
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    app.logger.addHandler(handler)
    try:
        response = login(client, password="private-password-marker")
        record = json.loads(stream.getvalue().splitlines()[-1])
        assert record["event_type"] == "LOGIN_FAILED"
        assert record["request_id"] == response.headers["X-Request-ID"]
        assert record["status_code"] == 401
        assert set(record) == {"timestamp", "level", "event_type", "source_ip", "target", "path", "method", "status_code", "request_id",
                               "event_id", "scenario_id", "severity", "source", "action"}
        assert "private-password-marker" not in stream.getvalue()
        with patch.object(db.session, "scalars", side_effect=RuntimeError("private-exception-marker")):
            assert client.get("/products").status_code == 500
        assert "private-exception-marker" not in stream.getvalue()
        assert json.loads(stream.getvalue().splitlines()[-1])["event_type"] == "SERVER_ERROR"
    finally:
        app.logger.removeHandler(handler)
