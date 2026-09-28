-- Update unchanged training seed copy only; preserve prices and inventory.
SET NAMES utf8mb4;
START TRANSACTION;
UPDATE products SET name = '무선 기계식 키보드', description = '부드러운 키감과 깔끔한 디자인의 무선 키보드입니다.' WHERE id = 1 AND name = '데모 키보드' AND description = '교육용 가상 상품입니다. 실제 판매 및 배송하지 않습니다.';
UPDATE products SET name = '저소음 무선 마우스', description = '편안한 그립과 조용한 클릭으로 업무에 집중하세요.' WHERE id = 2 AND name = '데모 마우스' AND description = '교육용 가상 상품입니다. 실제 판매 및 배송하지 않습니다.';
UPDATE products SET name = '데일리 줄노트', description = '필기하기 편한 종이와 단정한 표지의 노트입니다.' WHERE id = 3 AND name = '데모 노트' AND description = '교육용 가상 상품입니다. 실제 판매 및 배송하지 않습니다.';
UPDATE products SET name = '세라믹 머그컵', description = '따뜻한 커피 한 잔에 어울리는 350ml 머그컵입니다.' WHERE id = 4 AND name = '데모 머그컵' AND description = '교육용 가상 상품입니다. 실제 판매 및 배송하지 않습니다.';
UPDATE products SET name = '코튼 에코백', description = '넉넉한 수납공간으로 매일 들기 좋은 면 가방입니다.' WHERE id = 5 AND name = '데모 에코백' AND description = '교육용 가상 상품입니다. 실제 판매 및 배송하지 않습니다.';
UPDATE products SET name = '스테인리스 텀블러', description = '음료의 온도를 오래 유지하는 500ml 텀블러입니다.' WHERE id = 6 AND name = '데모 텀블러' AND description = '교육용 가상 상품입니다. 실제 판매 및 배송하지 않습니다.';
UPDATE products SET name = 'LED 데스크 스탠드', description = '밝기를 조절할 수 있는 실용적인 책상 조명입니다.' WHERE id = 7 AND name = '데모 스탠드' AND description = '교육용 가상 상품입니다. 실제 판매 및 배송하지 않습니다.';
UPDATE products SET name = '트래블 미니 파우치', description = '작은 소지품을 간편하게 정리하는 지퍼 파우치입니다.' WHERE id = 8 AND name = '데모 파우치' AND description = '교육용 가상 상품입니다. 실제 판매 및 배송하지 않습니다.';
UPDATE reviews SET content = '키감이 부드럽고 책상에 잘 어울려요.' WHERE user_id = 1 AND product_id = 1 AND content = '교육용 테스트 후기입니다.';
UPDATE reviews SET content = '클릭 소리가 조용해서 사용하기 편합니다.' WHERE user_id = 2 AND product_id = 2 AND content = '더미 상품의 후기 표시를 확인합니다.';
COMMIT;
