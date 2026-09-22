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
    (ROOT / "db/schema.sql").write_text("\n\n".join(schema) + "\n", encoding="utf-8")
    seed = ["-- FICTIONAL TRAINING DATA ONLY. Intentionally weak public passwords; never use with real data.\nSET NAMES utf8mb4;\nSTART TRANSACTION;"]
    for i, (username, password, role) in enumerate([
        ("user1", "1234", "user"),
        ("user2", "password", "user"),
        ("guest", "guest", "user"),
        ("test", "test", "user"),
        ("shop", "shop", "user"),
        ("admin", "admin", "admin"),
    ], 1):
        seed.append(f"INSERT INTO users (id, username, password_hash, role, created_at) VALUES ({i}, {quoted(username)}, {quoted(generate_password_hash(password))}, {quoted(role)}, UTC_TIMESTAMP());")
    products = [("데모 키보드", 45000), ("데모 마우스", 18000), ("데모 노트", 3500),
                ("데모 머그컵", 9000), ("데모 에코백", 12000), ("데모 텀블러", 22000),
                ("데모 스탠드", 32000), ("데모 파우치", 7500)]
    for i, (name, price) in enumerate(products, 1):
        seed.append(f"INSERT INTO products (id, name, description, price, stock, created_at) VALUES ({i}, {quoted(name)}, '교육용 가상 상품입니다. 실제 판매 및 배송하지 않습니다.', {price}, {19 if i == 1 else 20}, UTC_TIMESTAMP());")
    seed.extend([
        "INSERT INTO orders (id, user_id, status, total_price, created_at) VALUES (1, 1, 'created', 45000, UTC_TIMESTAMP());",
        "INSERT INTO order_items (id, order_id, product_id, quantity, price) VALUES (1, 1, 1, 1, 45000);",
        "INSERT INTO reviews (user_id, product_id, content, created_at) VALUES (1, 1, '교육용 테스트 후기입니다.', UTC_TIMESTAMP()), (2, 2, '더미 상품의 후기 표시를 확인합니다.', UTC_TIMESTAMP());",
        "COMMIT;",
    ])
    (ROOT / "db/seed.sql").write_text("\n".join(seed) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
