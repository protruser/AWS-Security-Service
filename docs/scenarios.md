# vuln_service 로컬 구현 메모

기존 시나리오 정의는 [scenario.md](scenario.md)에 있으며 원문을 보존했습니다.
이 문서는 이번에 구현한 네 가지 웹 시나리오만 보충합니다.
로컬 및 허가된 AWS 교육용 실습 환경과 더미 데이터 전용이며 인터넷 공개는 금지합니다.
실제 운영 환경이나 실제 데이터에는 취약 버전을 배포하지 않습니다.

| 시나리오 | 구현 | 이벤트 |
| --- | --- | --- |
| BRUTE_FORCE | routes/auth.py, services/lab.py의 record_login_attempt | LOGIN_SUCCESS, LOGIN_FAILED, BRUTE_FORCE_SUSPECTED |
| DIRECTORY_SEARCH | app/__init__.py의 요청·오류 처리 | SUSPICIOUS_PATH_REQUEST, INVALID_PATH |
| SQL_INJECTION | routes/products.py, services/lab.py의 vulnerable_search | SUSPICIOUS_SEARCH_INPUT, DATABASE_QUERY_ERROR |
| XSS | routes/reviews.py, templates/lab/review_content.html | SUSPICIOUS_REVIEW_INPUT, INPUT_VALIDATION_FAILED |

## 동작과 제한

- 로그인 실패는 기존 login_attempts에 저장합니다. 같은 IP **또는** 계정으로 최근 300초에 5회 이상 실패하면 탐지하며 각 기준은 따로 계산합니다. 오래된 실패는 제외하고 성공 후에도 기간 내 실패를 지우지 않습니다. 탐지 이후에도 잠금·Rate Limit 없이 요청을 처리합니다.
- seed에는 관리자 1명과 일반 사용자 5명의 공개 더미 계정이 있으며, 무차별 대입 탐지 실습을 위해 아이디와 비밀번호를 의도적으로 단순하게 구성했습니다. 계정 목록은 README를 기준으로 하며 다른 서비스에서 재사용하지 않습니다.
- 실패한 로그인 입력 검증 요청도 기록하며 과도한 본문처럼 계정을 읽을 수 없는 요청은 빈 계정명으로 저장합니다. 비밀번호를 저장하거나 로그 인자로 전달하지 않습니다. DB 장애 중에는 실패 내역 저장을 보장할 수 없습니다.
- /admin, /backup, /old, /config 및 끝 슬래시는 모든 메서드에서 404입니다. 실제 파일이나 관리자 기능은 없습니다. 다른 없는 경로는 INVALID_PATH입니다.
- 검색은 교육 모드에서 문자열 결합 SQL을 사용합니다. 와일드카드의 정상 문자 검색 의미는 유지하지만 따옴표를 바인딩하지 않는 의도적인 취약점이 있습니다. 기존 앱 DB 계정만 사용하고 권한을 확대하지 않습니다. DB 오류는 rollback 후 일반 503 페이지와 민감정보 없는 이벤트로 처리합니다.
- 후기는 길이 검증과 로그인을 유지하면서 교육 모드의 전용 partial에서만 HTML 인코딩을 생략합니다. 후기 GET에서만 inline script CSP 예외를 둡니다. 테스트에는 실행하지 않는 b 태그만 사용합니다.
- 의심 입력 감지는 단순 휴리스틱으로 오탐·미탐이 가능하며 WAF나 방어 수단이 아닙니다. 문자열 원문, SQL, 예외, Cookie, 인증 헤더를 이벤트에 넣지 않습니다.
- 기본 설정의 안전 검색과 후기 출력은 회귀 비교용이며 로그인 제한까지 구현한 개선 버전은 아닙니다. vuln_service 분리는 브랜치·주석·명시적 설정으로 관리하며 런타임 Git 검사는 없습니다.

## 이벤트 규격과 검증

기존 JSON stdout 로거에 event_id(UUID), scenario_id, severity, source, action을 추가했습니다.
기존 request_id, timestamp(UTC), source_ip, target, path, method, status_code와 level은 유지합니다.
일반 주문·상태 이벤트의 scenario_id는 null이며 보안 이벤트는 해당 네 가지 ID를 사용합니다.
정상은 INFO/NORMAL, 의심·실패는 HIGH/DETECTED이며 탐지 상태는 요청 차단 여부와 별개입니다.

`tests/test_app.py`는 기존 안전 동작 11개를 유지하고 이벤트 필드 검증만 확장합니다.
`tests/test_scenarios.py`는 교육 모드에서 더미 sentinel로 실패 저장·기간·IP/계정 집계,
경로, 검색, 후기, 오류 비노출, 비밀값 로그 제외, health/ready를 확인합니다.
실제 공격 payload 모음이나 실행 자동화는 추가하지 않습니다.

## 이후 개선

별도 개선 버전에서 로그인 제한, ORM/파라미터 바인딩, 후기 자동 인코딩과 엄격한 CSP를 적용하고
동일 테스트의 정상 기능 및 탐지 회귀를 비교합니다. WAF·CloudWatch 및 그 외 AWS 연동은 미구현입니다.
