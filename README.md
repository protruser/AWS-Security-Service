# AWS-Security-Service
AWS 기반 서비스 보안 구축 프로젝트(서비스)

## 교육용 Flask 쇼핑몰

AWS 보안 모니터링 프로젝트의 대상 서비스 기본 버전입니다. 현재 범위는 로컬 Docker Compose의 Flask + MySQL 실행까지입니다. 모든 계정, 상품, 후기, 주문은 가상 데이터이며 실제 개인정보, 결제, 배송은 사용하지 않습니다. 의도적인 SQL Injection/XSS 취약점이나 공격 실행 코드는 포함하지 않습니다. 공개된 더미 계정을 사용하는 학습 환경이므로 인터넷에 그대로 공개하지 마세요.

### 구조

```text
app/
  __init__.py             # Application Factory, 요청 ID, CSRF, 오류 처리
  config.py              # 개발/배포 설정 분리
  extensions.py          # SQLAlchemy
  models/__init__.py     # 6개 테이블의 ORM 모델 (order_items 포함)
  routes/                # health, auth, products, reviews, orders
  services/security.py   # 인증 데코레이터와 CSRF 토큰
  logging_config.py      # stdout JSON 이벤트
templates/               # Jinja2 화면
static/css/              # 반응형 CSS; JavaScript 없이 동작
db/schema.sql            # MySQL 8.4 스키마, FK/인덱스/제약조건
db/seed.sql              # 해시된 더미 계정과 초기 데이터
db/generate_seed.py      # ORM 기준 스키마/더미 데이터 재생성 도구
tests/                   # 격리된 SQLite 테스트
Dockerfile
docker-compose.local.yml
requirements.txt
requirements-dev.txt     # pytest는 개발 환경에만 설치
.env.example
AGENTS.md
run.py
```

### 사전 요구사항 및 실행

- Docker Engine 또는 Docker Desktop (Linux 컨테이너)과 Docker Compose
- 호스트에서 테스트하려면 Python 3.12
- 로컬 TCP 5000 포트

PowerShell에서 저장소 루트 기준으로 실행합니다. `.env`가 이미 있으면 덮어쓰지 않습니다.

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
docker compose -f docker-compose.local.yml config --quiet
docker compose -f docker-compose.local.yml build
docker compose -f docker-compose.local.yml up -d --wait
docker compose -f docker-compose.local.yml ps
```

Bash에서는 `test -f .env || cp .env.example .env`로 환경 파일을 준비하고 같은 Docker 명령을 사용합니다. 브라우저에서 <http://localhost:5000>을 엽니다.

`.env.example`의 값은 로컬 예시입니다. `.env`의 `SECRET_KEY`는 최소 32자 이상의 무작위 값으로 교체할 수 있습니다 (`python -c "import secrets; print(secrets.token_urlsafe(48))"`). DB 비밀번호도 이 실습 전용 값으로 지정합니다. 실제 사용 중인 비밀번호를 재사용하지 않습니다. `.env`, 가상환경, DB 데이터, 로그, 키 파일은 Git과 이미지에서 제외됩니다. `docker compose config`는 확장된 비밀번호를 출력할 수 있으므로 검증에는 `config --quiet`를 권장합니다.

| 환경변수 | 의미 |
| --- | --- |
| FLASK_ENV | development 또는 production; production은 Secure 세션 쿠키를 사용하므로 HTTPS 필요 |
| SECRET_KEY | 세션 서명 키, 최소 32자, 모든 앱 인스턴스가 같은 값 사용 |
| DB_HOST | 직접 실행 시 DB 호스트; 로컬 Compose에서는 shop-db로 고정 |
| DB_PORT | 직접 실행 시 DB 포트; Compose에서는 3306으로 고정 |
| DB_NAME / DB_USER / DB_PASSWORD | DB 이름 및 앱 전용 계정 |
| APP_PORT | Compose 호스트 공개 포트, 기본 5000; 컨테이너 내부는 항상 5000 |

MySQL 8.4는 호스트 포트를 공개하지 않습니다. 앱 포트는 `127.0.0.1`에만 바인딩합니다. DB root 비밀번호는 MySQL이 무작위 생성하며 앱은 별도 계정으로 접속합니다. MySQL 최초 초기화 로그에는 생성된 root 비밀번호가 포함될 수 있으므로 DB 로그를 공유하거나 커밋하지 않습니다. 앱의 구조화 로그에는 인증정보를 기록하지 않습니다.

### 중지, 재실행 및 데이터 보존

```powershell
docker compose -f docker-compose.local.yml down
docker compose -f docker-compose.local.yml up -d --wait
# 소스 수정 후
docker compose -f docker-compose.local.yml up -d --build --wait
```

Named Volume `shop-db-data`는 `down` 후에도 유지됩니다. **`down -v`를 사용하지 마세요.** 스키마와 seed SQL은 빈 볼륨의 최초 초기화 때만 적용됩니다. 기존 볼륨에 SQL 변경이나 `.env` DB 비밀번호 변경이 자동 반영되지는 않습니다. 스키마 변경은 추후 마이그레이션으로 관리해야 합니다. 초기 데이터는 일반 사용자 2명, 관리자 1명, 상품 8개, 후기 2개, 주문 1개입니다.

### 더미 사용자 (공개된 교육용 비밀번호)

| 사용자 이름 | 교육용 비밀번호 | 역할 |
| --- | --- | --- |
| demo_user1 | DemoUser1!2026 | user |
| demo_user2 | DemoUser2!2026 | user |
| demo_admin | DemoAdmin!2026 | admin |

DB에는 Werkzeug scrypt 해시만 저장됩니다. 관리자 역할은 저장 및 화면 표시로 구분하며 별도 관리자 기능은 현재 범위에 없습니다. seed를 재생성하려면 의존성 설치 후 `python db/generate_seed.py`를 실행합니다. 이 명령은 `db/schema.sql`, `db/seed.sql`만 갱신하며 실행 중 DB에는 접근하지 않습니다. 재생성 시 무작위 salt 때문에 해시가 변경됩니다.

### 기능 및 엔드포인트

| 메서드 / 경로 | 동작 |
| --- | --- |
| GET / | 쇼핑몰 홈 및 상품 목록 |
| GET /health | DB와 독립된 liveness, 200 |
| GET /ready | SELECT 1 성공 시 200, DB 장애 시 503 |
| GET /products | 상품 목록 |
| GET /products/&lt;id&gt; | 상품 상세 |
| GET /search?q=검색어 | 이름 부분 검색, 최대 120자 |
| GET, POST /login | 세션 로그인, 성공 302 / 실패 401 |
| POST /logout | 세션 삭제 |
| GET, POST /products/&lt;id&gt;/reviews | 후기 조회 / 로그인 사용자 작성 (1~2,000자) |
| POST /orders | product_id, quantity로 더미 주문 생성 (수량 1~100) |
| GET /orders | 자신의 주문만 조회 |

모든 POST는 화면의 hidden 필드 `csrf_token`과 해당 세션 쿠키가 필요합니다. 인증되지 않은 후기/주문 생성은 401, 잘못된 입력/CSRF는 400, 없는 상품은 404, 재고 부족은 409입니다. 주문/후기 성공은 303 리다이렉트입니다. 주문 금액은 DB 가격으로 계산하며 MySQL 행 잠금과 하나의 트랜잭션으로 재고 차감 및 주문 생성을 처리합니다. ORM 파라미터 바인딩, 검색 와일드카드 이스케이프, Jinja2 자동 출력 인코딩을 사용합니다.

### 테스트 및 상태 확인

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python -m pytest -q
curl.exe -i http://localhost:5000/health
curl.exe -i http://localhost:5000/ready
curl.exe -i http://localhost:5000/products
# 실행 중인 Compose 앱의 로그인/후기/주문/관리자 역할 통합 검증
python tests/smoke_local.py
```

Bash에서는 `.venv/bin/python`을 사용합니다. 가상환경을 활성화했다면 `python -m pytest`로도 실행할 수 있습니다. 테스트는 매번 별도의 메모리 SQLite DB를 만들며 `.env`나 운영 DB가 필요하지 않습니다. MySQL 고유 잠금/초기화 동작은 Compose 실행으로 별도 확인해야 합니다.

통합 검증 스크립트는 더미 후기 1개와 주문 1개를 생성하고 DB에 보존합니다. 반복 실행하면 키보드 재고가 차감됩니다. `SMOKE_BASE_URL`로 대상 주소를 바꿀 수 있습니다.

정상 `/health` 응답은 `{"status":"healthy","service":"shop-app"}`, `/ready`는 `{"status":"ready","database":"connected"}`입니다. 매 응답의 `X-Request-ID`로 로그를 연결할 수 있습니다.

### 로컬 인증서 환경에서 빌드

현재 검증 PC에서는 컨테이너의 PyPI TLS 인증서 검증이 실패하여 Windows의 공개 신뢰 CA 번들을 BuildKit secret `pip_ca_bundle`로 전달했습니다. TLS 검증을 비활성화하지 않으며 번들은 최종 이미지에 저장되지 않습니다. 일반 환경에서는 기본 빌드 명령만 사용합니다. 이 PC에는 Git에서 제외되는 `.local/build-ca.pem`과 `.local/compose-ca.yml`을 준비했습니다.

```powershell
docker compose -f docker-compose.local.yml -f .local/compose-ca.yml build
docker compose -f docker-compose.local.yml up -d --wait
```

다른 인증서 중계 환경에서는 신뢰할 수 있는 CA PEM 파일을 같은 BuildKit secret으로 제공해야 합니다. `.local` 폴더는 Git과 이미지에서 제외되므로 다른 PC로 자동 전달되지 않습니다.

### 로그 및 인프라 연동 규격

앱 이벤트는 stdout에 한 줄 JSON으로 출력합니다. 필드는 `timestamp` (UTC ISO-8601), `level`, `event_type`, `source_ip`, `target=shop-flask`, `path`, `method`, `status_code`, `request_id`입니다. 이벤트는 LOGIN_SUCCESS, LOGIN_FAILED, PRODUCT_SEARCH, PRODUCT_VIEWED, REVIEW_CREATED, ORDER_CREATED, INVALID_PATH, INPUT_VALIDATION_FAILED, DB_CONNECTION_FAILED, SERVER_ERROR입니다. 요청 본문, 검색어, 비밀번호, 쿠키, 세션 토큰, SQL 및 예외 원문은 기록하지 않습니다. Gunicorn 프로세스 시작/종료 로그는 stderr의 일반 텍스트이며 애플리케이션 JSON 이벤트와 구분하여 수집합니다. 원문 요청 URL을 남기는 Gunicorn access log는 켜지 않습니다.

현재 `source_ip`는 직접 연결한 클라이언트 주소이며 임의의 `X-Forwarded-For`를 신뢰하지 않습니다. ALB/Ingress 도입 시 실제 프록시 수와 신뢰 경계를 확인한 뒤 전달 IP 처리를 추가해야 합니다.

Terraform/인프라 담당자는 다음 규격을 사용합니다.

- 앱: Linux Python 3.12 이미지, UID 10001, Gunicorn 2 workers, 내부 TCP 5000, 상태 파일 불필요
- probe: `/health`는 liveness, `/ready`는 DB 연결 readiness (현재 Compose 자체 healthcheck는 `/ready`)
- DB: MySQL 8.4, TCP 3306, utf8mb4, InnoDB, 앱 전용 계정과 영구 스토리지 필요
- 설정: 위 환경변수 주입, 비밀값은 이미지/코드 밖에서 관리, production은 TLS 종료 필요
- 로그: 앱 stdout JSON, 프로세스 stderr, CloudWatch 수집 시 request_id와 event_type으로 조회
- 초기화: 새 DB에서 schema.sql → seed.sql 순서. 공개 교육용 seed의 배포 여부는 다음 단계에서 결정
- 공개 경로는 앱만 제공하고 DB 접근은 앱에서만 허용하도록 다음 단계에서 구성

### 현재 미구현 및 다음 단계

Terraform, AWS 리소스, ECR Push, EC2/K3s 배포, GitHub Actions 배포, CloudWatch 수집 인프라는 구현하지 않았습니다. 실제 결제/배송, 회원가입, 관리자 CRUD, 의도적인 취약점 및 공격 실행 코드도 없습니다. 다음 단계는 ECR → EC2/K3s → GitHub Actions 연동이며, 그 전에 마이그레이션, HTTPS/프록시 신뢰 설정, 비밀값 관리, 로그인 시도 제한과 MySQL 동시 주문 테스트를 보완하는 것을 권장합니다.

### 직접 검증 결과 (2026-09-21)

- Python 3.12: `python -m pytest -q` → 11 passed (격리된 테스트 DB).
- `docker compose -f docker-compose.local.yml config --quiet` → 성공.
- Docker Desktop 시작 후 CA secret override로 이미지 빌드 성공. 이후 기본 `build` 명령도 캐시를 사용해 성공. 이 PC의 캐시 없는 빌드는 위 CA 설정이 필요합니다.
- `docker compose -f docker-compose.local.yml up -d --wait` → shop-app, shop-db 모두 healthy.
- `python tests/smoke_local.py` → 실제 HTTP/MySQL 상품 조회·검색, 로그인 성공/실패, 비로그인 후기/주문 차단, 후기 인코딩, 주문 생성, 관리자 역할 및 다른 계정의 주문 비노출 확인.
- `/health`, `/ready`, `/products` → 모두 200, X-Request-ID 존재.
- DB 중지 시 `/health` 200, `/ready` 503; DB 복구 후 `/ready` 200 확인.
- 컨테이너 UID 10001, 이미지 내부 `.env` 및 빌드 CA secret 부재 확인.
- 검증 후 `docker compose -f docker-compose.local.yml down` 수행. Named Volume `aws-security-service_shop-db-data` 보존 확인. 최초 seed 외에 통합 검증 후기 1개, 주문 1개, 로그인 시도 3개가 남아 있습니다.
- `.env`, `.local`, `.venv` Git 제외 및 `git diff --check` 통과. commit/push/merge는 수행하지 않았습니다.
