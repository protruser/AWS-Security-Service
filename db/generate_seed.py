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
    products = [
        ("무선 기계식 키보드", "부드러운 키감과 깔끔한 디자인의 무선 키보드입니다.", 45000, 19),
        ("저소음 무선 마우스", "편안한 그립과 조용한 클릭으로 업무에 집중하세요.", 18000, 40),
        ("데일리 줄노트", "필기하기 편한 종이와 단정한 표지의 노트입니다.", 3500, 80),
        ("세라믹 머그컵", "따뜻한 커피 한 잔에 어울리는 350ml 머그컵입니다.", 9000, 30),
        ("코튼 에코백", "넉넉한 수납공간으로 매일 들기 좋은 면 가방입니다.", 12000, 25),
        ("스테인리스 텀블러", "음료의 온도를 오래 유지하는 500ml 텀블러입니다.", 22000, 35),
        ("LED 데스크 스탠드", "밝기를 조절할 수 있는 실용적인 책상 조명입니다.", 32000, 15),
        ("트래블 미니 파우치", "작은 소지품을 간편하게 정리하는 지퍼 파우치입니다.", 7500, 50),
    ]
    for i, (name, description, price, stock) in enumerate(products, 1):
        seed.append(f"INSERT INTO products (id, name, description, price, stock, created_at) VALUES ({i}, {quoted(name)}, {quoted(description)}, {price}, {stock}, UTC_TIMESTAMP());")
    seed.extend([
        "INSERT INTO orders (id, user_id, status, total_price, created_at) VALUES (1, 1, 'created', 45000, UTC_TIMESTAMP());",
        "INSERT INTO order_items (id, order_id, product_id, quantity, price) VALUES (1, 1, 1, 1, 45000);",
        "INSERT INTO reviews (user_id, product_id, content, created_at) VALUES (1, 1, '키감이 부드럽고 책상에 잘 어울려요.', UTC_TIMESTAMP()), (2, 2, '클릭 소리가 조용해서 사용하기 편합니다.', UTC_TIMESTAMP());",
        "COMMIT;",
    ])
    (ROOT / "db/seed.sql").write_text("\n".join(seed) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
