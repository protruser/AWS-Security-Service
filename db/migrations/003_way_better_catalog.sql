-- Authorized training database only; never apply to real production data.
-- Back up the database and pause application writes before applying.
-- Requires migration 001 if users.balance is absent. Do not rerun schema.sql/seed.sql.
-- Product IDs and existing order prices, accounts, balances and stock are preserved.
-- New seed stock levels apply only to a fresh database, not existing inventory.
-- Product names/descriptions/prices for IDs 1-8 are intentionally replaced.
SET NAMES utf8mb4;
START TRANSACTION;
UPDATE products SET name = '저소음 무선 키보드', description = '편안한 타건감과 조용한 사용 환경을 제공하는 슬림형 무선 키보드입니다.', price = 45000 WHERE id = 1;
UPDATE products SET name = '인체공학 무선 마우스', description = '손목 부담을 줄이고 안정적인 그립감을 제공하는 무선 마우스입니다.', price = 39000 WHERE id = 2;
UPDATE products SET name = 'USB-C 멀티 허브', description = 'HDMI, USB, 메모리 카드 연결을 하나로 지원하는 휴대용 멀티 허브입니다.', price = 59000 WHERE id = 3;
UPDATE products SET name = '27인치 QHD 모니터', description = '선명한 QHD 화면과 넓은 작업 공간을 제공하는 사무용 모니터입니다.', price = 289000 WHERE id = 4;
UPDATE products SET name = '노이즈 캔슬링 헤드폰', description = '외부 소음을 줄이고 풍부한 사운드를 제공하는 무선 헤드폰입니다.', price = 129000 WHERE id = 5;
UPDATE products SET name = '알루미늄 노트북 거치대', description = '노트북 화면 높이를 편안하게 조절할 수 있는 접이식 거치대입니다.', price = 32000 WHERE id = 6;
UPDATE products SET name = '와이드 데스크 매트', description = '키보드와 마우스를 여유 있게 배치할 수 있는 생활 방수 데스크 매트입니다.', price = 19000 WHERE id = 7;
UPDATE products SET name = '무선 LED 데스크 스탠드', description = '밝기와 색온도를 조절할 수 있는 충전식 LED 스탠드입니다.', price = 42000 WHERE id = 8;
UPDATE reviews SET content = '키감이 부드럽고 소음이 적어서 사무실에서 사용하기 좋습니다.' WHERE user_id = 1 AND product_id = 1 AND content IN ('교육용 테스트 후기입니다.', '키감이 부드럽고 책상에 잘 어울려요.');
UPDATE reviews SET content = '손에 편하게 잡히고 오래 사용해도 손목 부담이 적어요.' WHERE user_id = 2 AND product_id = 2 AND content IN ('더미 상품의 후기 표시를 확인합니다.', '클릭 소리가 조용해서 사용하기 편합니다.');
INSERT INTO reviews (user_id, product_id, content, created_at) SELECT u.id, p.id, '키감이 부드럽고 소음이 적어서 사무실에서 사용하기 좋습니다.', UTC_TIMESTAMP() FROM users u JOIN products p ON p.id = 1 WHERE u.id = 1 AND u.username = 'user1' AND NOT EXISTS (SELECT 1 FROM reviews r WHERE r.user_id = u.id AND r.product_id = p.id AND r.content = '키감이 부드럽고 소음이 적어서 사무실에서 사용하기 좋습니다.');
INSERT INTO reviews (user_id, product_id, content, created_at) SELECT u.id, p.id, '손에 편하게 잡히고 오래 사용해도 손목 부담이 적어요.', UTC_TIMESTAMP() FROM users u JOIN products p ON p.id = 2 WHERE u.id = 2 AND u.username = 'user2' AND NOT EXISTS (SELECT 1 FROM reviews r WHERE r.user_id = u.id AND r.product_id = p.id AND r.content = '손에 편하게 잡히고 오래 사용해도 손목 부담이 적어요.');
INSERT INTO reviews (user_id, product_id, content, created_at) SELECT u.id, p.id, '노트북에 필요한 포트를 한 번에 연결할 수 있어서 편리합니다.', UTC_TIMESTAMP() FROM users u JOIN products p ON p.id = 3 WHERE u.id = 3 AND u.username = 'guest' AND NOT EXISTS (SELECT 1 FROM reviews r WHERE r.user_id = u.id AND r.product_id = p.id AND r.content = '노트북에 필요한 포트를 한 번에 연결할 수 있어서 편리합니다.');
INSERT INTO reviews (user_id, product_id, content, created_at) SELECT u.id, p.id, '높이 조절이 간단하고 책상이 한결 깔끔해졌습니다.', UTC_TIMESTAMP() FROM users u JOIN products p ON p.id = 6 WHERE u.id = 4 AND u.username = 'test' AND NOT EXISTS (SELECT 1 FROM reviews r WHERE r.user_id = u.id AND r.product_id = p.id AND r.content = '높이 조절이 간단하고 책상이 한결 깔끔해졌습니다.');
INSERT INTO reviews (user_id, product_id, content, created_at) SELECT u.id, p.id, '크기가 넉넉하고 마우스 움직임도 부드럽습니다.', UTC_TIMESTAMP() FROM users u JOIN products p ON p.id = 7 WHERE u.id = 5 AND u.username = 'shop' AND NOT EXISTS (SELECT 1 FROM reviews r WHERE r.user_id = u.id AND r.product_id = p.id AND r.content = '크기가 넉넉하고 마우스 움직임도 부드럽습니다.');
COMMIT;
