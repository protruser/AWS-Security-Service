"""Exercise the versioned training seed against an isolated local database."""
from pathlib import Path

import pytest
from werkzeug.security import check_password_hash

from app.extensions import db
from app.models import Order, Product, Review, User
from conftest import login

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = ("demo", "데모", "더미", "교육용", "가상 상품", "실제 판매", "출력 확인")


def execute_sql(path):
    sql = path.read_text(encoding="utf-8").replace("SET NAMES utf8mb4;", "").replace("START TRANSACTION;", "BEGIN;")
    connection = db.engine.raw_connection()
    try:
        connection.create_function("UTC_TIMESTAMP", 0, lambda: "2026-01-01 12:00:00")
        connection.executescript(sql)
    finally:
        connection.close()
    db.session.expire_all()


@pytest.fixture
def catalog(app):
    with app.app_context():
        db.drop_all()
        db.create_all()
        execute_sql(ROOT / "db/seed.sql")
    return app


def test_seed_catalog_and_brand(catalog, client):
    response = client.get("/products")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "<title>Way Better | 조금 더 나은 삶을 위한 선택</title>" in page
    assert page.count('class="card product-card"') == 8
    assert page.count("상세보기</a>") == 8
    assert all(word not in page.lower() for word in FORBIDDEN)
    expected = [
        ("저소음 무선 키보드", 45000, 30), ("인체공학 무선 마우스", 39000, 25),
        ("USB-C 멀티 허브", 59000, 20), ("27인치 QHD 모니터", 289000, 12),
        ("노이즈 캔슬링 헤드폰", 129000, 18), ("알루미늄 노트북 거치대", 32000, 35),
        ("와이드 데스크 매트", 19000, 40), ("무선 LED 데스크 스탠드", 42000, 22),
    ]
    with catalog.app_context():
        products = db.session.scalars(db.select(Product).order_by(Product.id)).all()
        assert [p.id for p in products] == list(range(1, 9))
        assert [(p.name, p.price, p.stock) for p in products] == expected
        for product in products:
            assert product.name in page and product.description in page
            assert f"남은 재고 {product.stock}개" in page


def test_seed_reviews(catalog, client):
    expected = [
        ("user1", 1, "키감이 부드럽고 소음이 적어서 사무실에서 사용하기 좋습니다."),
        ("user2", 2, "손에 편하게 잡히고 오래 사용해도 손목 부담이 적어요."),
        ("guest", 3, "노트북에 필요한 포트를 한 번에 연결할 수 있어서 편리합니다."),
        ("test", 6, "높이 조절이 간단하고 책상이 한결 깔끔해졌습니다."),
        ("shop", 7, "크기가 넉넉하고 마우스 움직임도 부드럽습니다."),
    ]
    with catalog.app_context():
        reviews = db.session.scalars(db.select(Review).order_by(Review.id)).all()
        assert [(r.user.username, r.product_id, r.content) for r in reviews] == expected
    for _, product_id, content in expected:
        response = client.get(f"/products/{product_id}/reviews")
        assert response.status_code == 200
        assert content in response.get_data(as_text=True)
        assert all(word not in content.lower() for word in (*FORBIDDEN, "테스트", "실습"))


def test_seed_accounts_and_order(catalog, client):
    with catalog.app_context():
        users = db.session.scalars(db.select(User).order_by(User.id)).all()
        assert [u.username for u in users] == ["user1", "user2", "guest", "test", "shop", "admin"]
        for user, password in zip(users, ["1234", "password", "guest", "test", "shop", "admin"]):
            assert check_password_hash(user.password_hash, password)
        assert users[-1].role == "admin"
    assert login(client).status_code == 302
    assert client.get("/management/products").status_code == 403
    assert client.post("/orders", data={"product_id": 1, "quantity": 2}).status_code == 303
    with catalog.app_context():
        assert db.session.get(User, 1).balance == 410000
        assert db.session.get(Product, 1).stock == 28
        assert db.session.get(Order, 1).total_price == 45000
    page = client.get("/orders").get_data(as_text=True)
    for text in ["주문번호", "주문일시", "저소음 무선 키보드", "주문수량 2개", "결제금액 90,000원", "주문상태"]:
        assert text in page


def test_catalog_migration_preserves_existing_data(catalog):
    with catalog.app_context():
        db.session.get(Product, 1).stock = 17
        db.session.get(User, 1).balance = 123456
        review = db.session.get(Review, 1)
        review.content = "교육용 테스트 후기입니다."
        db.session.add(Review(user_id=1, product_id=1, content="내가 작성한 후기는 유지해주세요."))
        db.session.commit()
        migration = ROOT / "db/migrations/003_way_better_catalog.sql"
        execute_sql(migration)
        execute_sql(migration)
        assert db.session.get(Product, 1).stock == 17
        assert db.session.get(User, 1).balance == 123456
        assert db.session.get(Order, 1).items[0].price == 45000
        reviews = db.session.scalars(db.select(Review)).all()
        assert len(reviews) == 6
        assert any(r.content == "내가 작성한 후기는 유지해주세요." for r in reviews)
        assert all("교육용" not in r.content for r in reviews)
