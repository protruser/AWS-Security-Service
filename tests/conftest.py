import pytest
from werkzeug.security import generate_password_hash
from app import create_app
from app.extensions import db
from app.models import Product, User


@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SECRET_KEY": "test-only-secret-key-not-for-deployment",
                      "SQLALCHEMY_DATABASE_URI": "sqlite://", "SQLALCHEMY_ENGINE_OPTIONS": {}})
    with app.app_context():
        db.create_all()
        db.session.add_all([
            User(username="demo_user1", password_hash=generate_password_hash("DemoUser1!2026"), role="user"),
            User(username="demo_user2", password_hash=generate_password_hash("DemoUser2!2026"), role="user"),
            Product(name="Demo Keyboard", description="Dummy product", price=12000, stock=5),
        ])
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def token(client):
    client.get("/login")
    with client.session_transaction() as session:
        return session["csrf_token"]


def login(client, username="demo_user1", password="DemoUser1!2026"):
    return client.post("/login", data={"username": username, "password": password, "csrf_token": token(client)})
