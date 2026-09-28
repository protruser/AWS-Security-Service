from decimal import Decimal
from unittest.mock import patch

import pytest
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models import Order, OrderItem, Product, User
from conftest import login


@pytest.fixture
def admin_client(app, client):
    with app.app_context():
        db.session.get(User, 1).role = "admin"
        db.session.commit()
    login(client)
    return client


def snapshot(app):
    with app.app_context():
        return (db.session.get(User, 1).balance, db.session.get(Product, 1).stock,
                len(db.session.scalars(db.select(Order)).all()),
                len(db.session.scalars(db.select(OrderItem)).all()))


def test_order_debits_balance_and_stock(client, app):
    login(client)
    assert client.post("/orders", data={"product_id": 1, "quantity": 2}).status_code == 303
    assert snapshot(app) == (Decimal("976000"), 3, 1, 1)
    page = client.get("/orders").get_data(as_text=True)
    for text in ["주문번호", "주문일시", "주문수량 2개", "결제금액 24,000원", "주문상태", "보유금액 976,000원"]:
        assert text in page
    login(client, "user2", "password")
    assert "주문번호 #1" not in client.get("/orders").get_data(as_text=True)


def test_insufficient_balance_is_atomic(client, app):
    with app.app_context():
        db.session.get(User, 1).balance = Decimal("11999")
        db.session.commit()
    login(client)
    before = snapshot(app)
    response = client.post("/orders", data={"product_id": 1, "quantity": 1})
    assert response.status_code == 409
    assert "보유금액이 부족합니다." in response.get_data(as_text=True)
    assert snapshot(app) == before


def test_commit_failure_rolls_back_all_changes(client, app):
    login(client)
    before = snapshot(app)
    with patch.object(db.session, "commit", side_effect=SQLAlchemyError("failed")):
        assert client.post("/orders", data={"product_id": 1, "quantity": 1}).status_code == 503
    assert snapshot(app) == before


@pytest.mark.parametrize("method,path", [
    ("get", "/management/products"), ("get", "/management/products/new"),
    ("post", "/management/products/new"), ("get", "/management/products/1/edit"),
    ("post", "/management/products/1/edit"), ("post", "/management/products/1/stock"),
])
def test_admin_access_control(client, method, path):
    assert getattr(client, method)(path).status_code == 401
    login(client)
    assert getattr(client, method)(path).status_code == 403
    assert "상품 관리" not in client.get("/").get_data(as_text=True)


def test_admin_create_edit_stock(admin_client, app):
    client = admin_client
    assert "상품 관리" in client.get("/").get_data(as_text=True)
    for path in ["/management/products", "/management/products/new", "/management/products/1/edit"]:
        assert client.get(path).status_code == 200
    values = dict(name="리넨 쿠션", description="편안한 쿠션", price="15000.50", stock="10")
    assert client.post("/management/products/new", data=values).status_code == 303
    with app.app_context():
        product = db.session.scalar(db.select(Product).where(Product.name == values["name"]))
        product_id = product.id
        assert product.price == Decimal("15000.50") and product.stock == 10
    values.update(name="코튼 쿠션", price="17000", stock="20")
    assert client.post(f"/management/products/{product_id}/edit", data=values).status_code == 303
    with app.app_context():
        product = db.session.get(Product, product_id)
        assert (product.name, product.price, product.stock) == ("코튼 쿠션", 17000, 20)
    assert client.post(f"/management/products/{product_id}/stock", data={"stock": 0}).status_code == 303
    with app.app_context():
        assert db.session.get(Product, product_id).stock == 0


@pytest.mark.parametrize("field,value", [
    ("name", ""), ("name", "x" * 121), ("description", " "),
    ("price", "-1"), ("price", "NaN"), ("price", "Infinity"),
    ("price", "100000000"), ("price", "0.001"), ("price", "bad"),
    ("stock", "-1"), ("stock", "1.5"), ("stock", "2147483648"),
])
def test_invalid_admin_input_is_atomic(admin_client, app, field, value):
    values = dict(name="상품", description="설명", price="100", stock="5")
    values[field] = value
    before = snapshot(app)
    assert admin_client.post("/management/products/new", data=values).status_code == 400
    assert admin_client.post("/management/products/1/edit", data=values).status_code == 400
    with app.app_context():
        assert len(db.session.scalars(db.select(Product)).all()) == 1
        assert db.session.get(Product, 1).price == 12000
    assert snapshot(app) == before


def test_missing_product_and_invalid_stock(admin_client):
    assert admin_client.get("/management/products/999/edit").status_code == 404
    assert admin_client.post("/management/products/999/edit").status_code == 404
    assert admin_client.post("/management/products/999/stock").status_code == 404
    assert admin_client.post("/management/products/1/stock", data={"stock": "-1"}).status_code == 400
    assert admin_client.get("/admin").status_code == 404


def test_customer_copy(client, app):
    # Preserve the legacy fixtures used by the existing scenario tests.
    with app.app_context():
        product = db.session.get(Product, 1)
        product.name = "무선 키보드"
        product.description = "편안한 타이핑을 위한 키보드"
        db.session.commit()
    login(client)
    for path in ["/", "/products", "/products/1", "/products/1/reviews", "/orders", "/login"]:
        response = client.get(path)
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        assert "CLOUD SHOP" in page
        for word in ["DEMO", "더미", "교육용", "실습"]:
            assert word not in page
