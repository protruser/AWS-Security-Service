-- FICTIONAL TRAINING DATA ONLY. Public demo passwords are documented in README.
SET NAMES utf8mb4;
START TRANSACTION;
INSERT INTO users (id, username, password_hash, role, created_at) VALUES (1, 'demo_user1', 'scrypt:32768:8:1$w3tEBPhbYxJ3hIHL$2faba482ecf7e4a54f621d8150404af8a2453ba4aedb0f1d8fbe37d68d3a03e54ba4b554db88ce9f9b1dafee46c20f926ac0bd1672498108da0e057b6b64e3d8', 'user', UTC_TIMESTAMP());
INSERT INTO users (id, username, password_hash, role, created_at) VALUES (2, 'demo_user2', 'scrypt:32768:8:1$vo3lT45LlsTcWN8v$a1be3d9e3e93bbf64173a8330288b81fb8f430dabeb14624ed5b62d45fd60ae9db4c042376419df60c97d74e05ed1af2d95dafd762ff3b2a1c478226025a1e36', 'user', UTC_TIMESTAMP());
INSERT INTO users (id, username, password_hash, role, created_at) VALUES (3, 'demo_admin', 'scrypt:32768:8:1$nX85KuBOasN2BMxH$ce22cbe158ea59c947ed76b6ef5d648475de9812a617f86f33e5fc0e8c79c0f7d7d2e3860334b77de7f2f0d11fedb4abbfd47b04a168886ee2307de4da92d6bd', 'admin', UTC_TIMESTAMP());
INSERT INTO products (id, name, description, price, stock, created_at) VALUES (1, '데모 키보드', '교육용 가상 상품입니다. 실제 판매 및 배송하지 않습니다.', 45000, 19, UTC_TIMESTAMP());
INSERT INTO products (id, name, description, price, stock, created_at) VALUES (2, '데모 마우스', '교육용 가상 상품입니다. 실제 판매 및 배송하지 않습니다.', 18000, 20, UTC_TIMESTAMP());
INSERT INTO products (id, name, description, price, stock, created_at) VALUES (3, '데모 노트', '교육용 가상 상품입니다. 실제 판매 및 배송하지 않습니다.', 3500, 20, UTC_TIMESTAMP());
INSERT INTO products (id, name, description, price, stock, created_at) VALUES (4, '데모 머그컵', '교육용 가상 상품입니다. 실제 판매 및 배송하지 않습니다.', 9000, 20, UTC_TIMESTAMP());
INSERT INTO products (id, name, description, price, stock, created_at) VALUES (5, '데모 에코백', '교육용 가상 상품입니다. 실제 판매 및 배송하지 않습니다.', 12000, 20, UTC_TIMESTAMP());
INSERT INTO products (id, name, description, price, stock, created_at) VALUES (6, '데모 텀블러', '교육용 가상 상품입니다. 실제 판매 및 배송하지 않습니다.', 22000, 20, UTC_TIMESTAMP());
INSERT INTO products (id, name, description, price, stock, created_at) VALUES (7, '데모 스탠드', '교육용 가상 상품입니다. 실제 판매 및 배송하지 않습니다.', 32000, 20, UTC_TIMESTAMP());
INSERT INTO products (id, name, description, price, stock, created_at) VALUES (8, '데모 파우치', '교육용 가상 상품입니다. 실제 판매 및 배송하지 않습니다.', 7500, 20, UTC_TIMESTAMP());
INSERT INTO orders (id, user_id, status, total_price, created_at) VALUES (1, 1, 'created', 45000, UTC_TIMESTAMP());
INSERT INTO order_items (id, order_id, product_id, quantity, price) VALUES (1, 1, 1, 1, 45000);
INSERT INTO reviews (user_id, product_id, content, created_at) VALUES (1, 1, '교육용 테스트 후기입니다.', UTC_TIMESTAMP()), (2, 2, '더미 상품의 후기 표시를 확인합니다.', UTC_TIMESTAMP());
COMMIT;
