"""Regenerate versioned schema/seed using fictional, publicly documented accounts.

Run from the repository root: python db/generate_seed.py
Only schema.sql and seed.sql are written; no live database is modified.
"""
import sys
from pathlib import Path
from sqlalchemy.dialects import mysql
from sqlalchemy.schema import CreateIndex, CreateTable
from werkzeug.security import generate_password_hash

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.extensions import db  # noqa: E402
from app import models  # noqa: E402, F401


PRODUCTS = [
    ("저소음 무선 키보드", "편안한 타건감과 조용한 사용 환경을 제공하는 슬림형 무선 키보드입니다.", 45000, 30),
    ("인체공학 무선 마우스", "손목 부담을 줄이고 안정적인 그립감을 제공하는 무선 마우스입니다.", 39000, 25),
    ("USB-C 멀티 허브", "HDMI, USB, 메모리 카드 연결을 하나로 지원하는 휴대용 멀티 허브입니다.", 59000, 20),
    ("27인치 QHD 모니터", "선명한 QHD 화면과 넓은 작업 공간을 제공하는 사무용 모니터입니다.", 289000, 12),
    ("노이즈 캔슬링 헤드폰", "외부 소음을 줄이고 풍부한 사운드를 제공하는 무선 헤드폰입니다.", 129000, 18),
    ("알루미늄 노트북 거치대", "노트북 화면 높이를 편안하게 조절할 수 있는 접이식 거치대입니다.", 32000, 35),
    ("와이드 데스크 매트", "키보드와 마우스를 여유 있게 배치할 수 있는 생활 방수 데스크 매트입니다.", 19000, 40),
    ("무선 LED 데스크 스탠드", "밝기와 색온도를 조절할 수 있는 충전식 LED 스탠드입니다.", 42000, 22),
]

REVIEWS = [
    (1, 1, "키감이 부드럽고 소음이 적어서 사무실에서 사용하기 좋습니다."),
    (2, 2, "손에 편하게 잡히고 오래 사용해도 손목 부담이 적어요."),
    (3, 3, "노트북에 필요한 포트를 한 번에 연결할 수 있어서 편리합니다."),
    (4, 6, "높이 조절이 간단하고 책상이 한결 깔끔해졌습니다."),
    (5, 7, "크기가 넉넉하고 마우스 움직임도 부드럽습니다."),
]


def quoted(value):
    return "'" + value.replace("'", "''") + "'"


def main():
    dialect = mysql.dialect()
    schema = ["-- Generated from app.models. MySQL 8.4, selected MYSQL_DATABASE.\nSET NAMES utf8mb4;"]
    for table in db.metadata.sorted_tables:
        schema.append(str(CreateTable(table).compile(dialect=dialect)).strip() + " ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;")
        for index in sorted(table.indexes, key=lambda item: item.name):
            schema.append(str(CreateIndex(index).compile(dialect=dialect)) + ";")
    schema_text = "\n".join(line.rstrip() for line in "\n\n".join(schema).splitlines())
    (ROOT / "db/schema.sql").write_text(schema_text + "\n", encoding="utf-8")
    seed = ["-- FICTIONAL TRAINING DATA ONLY. Intentionally weak public passwords; never use with real data.\nSET NAMES utf8mb4;\nSTART TRANSACTION;"]
    for i, (username, password, role, balance) in enumerate([
        ("user1", "1234", "user", 500000),
        ("user2", "password", "user", 300000),
        ("guest", "guest", "user", 100000),
        ("test", "test", "user", 200000),
        ("shop", "shop", "user", 1000000),
        ("admin", "admin", "admin", 5000000),
    ], 1):
        seed.append(f"INSERT INTO users (id, username, password_hash, role, balance, created_at) VALUES ({i}, {quoted(username)}, {quoted(generate_password_hash(password))}, {quoted(role)}, {balance}, UTC_TIMESTAMP());")
    for i, (name, description, price, stock) in enumerate(PRODUCTS, 1):
        seed.append(f"INSERT INTO products (id, name, description, price, stock, created_at) VALUES ({i}, {quoted(name)}, {quoted(description)}, {price}, {stock}, UTC_TIMESTAMP());")
    seed.extend([
        "INSERT INTO orders (id, user_id, status, total_price, created_at) VALUES (1, 1, 'created', 45000, UTC_TIMESTAMP());",
        "INSERT INTO order_items (id, order_id, product_id, quantity, price) VALUES (1, 1, 1, 1, 45000);",
    ])
    for user_id, product_id, content in REVIEWS:
        seed.append(f"INSERT INTO reviews (user_id, product_id, content, created_at) VALUES ({user_id}, {product_id}, {quoted(content)}, UTC_TIMESTAMP());")
    seed.append("COMMIT;")
    (ROOT / "db/seed.sql").write_text("\n".join(seed) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
