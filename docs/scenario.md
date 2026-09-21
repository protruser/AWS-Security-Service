# 보안 공격 시나리오 정의

## 1. 문서 목적

본 문서는 교육용 쇼핑몰에서 재현할 보안 시나리오의 취약 위치, 탐지 근거, 로그, 영향 및 개선 방법을 정의한다.

쇼핑몰은 더미 데이터만 사용하며 실제 개인정보·인증정보를 저장하지 않는다. 웹 취약점은 먼저 로컬 Docker 환경에서 검증하고, AWS 배포 이후 WAF, CloudWatch, GuardDuty, Inspector 등의 실제 탐지 결과를 확인한다.

## 2. 공통 처리 흐름

```text
취약 상태 배포
→ 공격 또는 이상행위 발생
→ 로그 및 AWS Finding 생성
→ 보안결과 DB 저장
→ 대시보드 위험 위치 표시
→ 관리자 조치 승인
→ 개선 버전 배포 또는 설정 변경
→ 동일 시나리오 재점검
→ 해결 상태 표시
```

## 3. 공통 이벤트 형식

쇼핑몰에서 생성하는 보안 관련 로그는 JSON 한 줄 형식으로 출력한다.

```json
{
  "event_id": "evt-001",
  "scenario_id": "BRUTE_FORCE",
  "event_type": "LOGIN_FAILED",
  "severity": "HIGH",
  "source": "SHOP_APP",
  "source_ip": "127.0.0.1",
  "target": "shop-flask",
  "path": "/login",
  "method": "POST",
  "status_code": 401,
  "action": "DETECTED",
  "request_id": "req-1234",
  "timestamp": "2026-09-21T10:30:00Z"
}
```

### 공통 상태

```text
NORMAL
DETECTED
BLOCKED
ACTION_REQUIRED
REMEDIATING
RESOLVED
```

애플리케이션 로그에는 비밀번호, 세션 토큰, Cookie, AWS Access Key, DB 비밀번호를 기록하지 않는다.

---

# 4. 시나리오 정의

## SCN-01. SQL Injection

### 취약 위치

```text
Flask App → 상품 검색 API → Shopping MySQL
GET /search?q=...
```

### 취약 원인

사용자 입력값을 안전하게 처리하지 않고 SQL 쿼리 생성에 사용해 데이터베이스 쿼리 구조가 변경될 수 있다.

### 로컬 구현 범위

* 상품 검색 기능을 시나리오 대상으로 사용
* 취약 버전과 개선 버전을 분리
* 쇼핑몰 더미 데이터만 사용
* 쇼핑몰 DB 전용 최소권한 계정 사용
* 의심 검색 요청과 DB 오류를 JSON 로그로 기록

### 예상 이벤트

```text
SUSPICIOUS_SEARCH_INPUT
DATABASE_QUERY_ERROR
```

### AWS 탐지

* AWS WAF SQLi 관리형 규칙
* WAF Logs
* CloudWatch Logs

### 대시보드 표시 위치

```text
쇼핑몰 WAF → K3s nginx → Flask App → Shopping MySQL
```

* WAF: 공격 탐지·차단 위치
* Flask App: 근본 취약점 위치
* Shopping MySQL: 공격 영향 대상

### 개선 방법

* ORM 사용
* Prepared Statement 또는 파라미터 바인딩
* DB 계정 최소권한 적용
* 상세 DB 오류 외부 노출 방지

### 조치 완료 기준

동일한 비정상 입력을 다시 전달했을 때 쿼리 구조가 변경되지 않고 정상적인 입력값으로만 처리되어야 한다.

---

## SCN-02. XSS

### 취약 위치

```text
Flask App → 상품 후기 기능
POST /products/<id>/reviews
GET  /products/<id>/reviews
```

### 취약 원인

사용자가 입력한 후기 내용을 출력할 때 HTML 인코딩과 검증을 적용하지 않는다.

### 로컬 구현 범위

* 더미 사용자가 작성한 후기만 사용
* 취약 버전과 개선 버전 분리
* 의심 후기 입력 시 구조화 로그 생성
* 실제 관리자 계정, 인증 토큰, 개인정보 사용 금지

### 예상 이벤트

```text
SUSPICIOUS_REVIEW_INPUT
INPUT_VALIDATION_FAILED
```

### AWS 탐지

* AWS WAF XSS 관리형 규칙
* WAF Logs
* CloudWatch Logs

### 대시보드 표시 위치

```text
쇼핑몰 WAF → K3s nginx → Flask App 후기 기능
```

### 개선 방법

* Jinja2 자동 Escape 유지
* 사용자 입력 HTML 인코딩
* 입력값 길이 및 형식 검증
* Content-Security-Policy 적용
* Cookie에 HttpOnly, Secure 속성 적용

### 조치 완료 기준

후기 입력값이 실행 가능한 코드가 아니라 일반 문자열로 출력되어야 한다.

---

## SCN-03. 디렉터리 서치

### 취약 위치

```text
K3s nginx 및 Flask App URL 경로
```

### 대상 경로 예시

```text
/admin
/backup
/old
/config
```

### 취약 원인

예측 가능한 관리·백업 경로가 존재하며 반복적인 경로 탐색에 대한 제한과 탐지 기준이 부족하다.

### 로컬 구현 범위

* 더미 관리 경로 구성
* 실제 `.env`, DB 백업, 인증정보는 노출하지 않음
* 반복되는 403·404 요청 로그 생성
* 출발지 IP별 요청 횟수를 분석할 수 있게 기록

### 예상 이벤트

```text
SUSPICIOUS_PATH_REQUEST
INVALID_PATH
```

### AWS 탐지

* WAF Logs
* ALB/nginx Access Logs
* CloudWatch Logs
* Lambda 자체 분석 로직

### 대시보드 표시 위치

```text
쇼핑몰 WAF → Shop ALB → K3s nginx
```

### 개선 방법

* 불필요한 경로 제거
* 디렉터리 목록 기능 비활성화
* 관리 경로 접근 제어
* 반복 요청에 대한 Rate Limit 적용
* 민감 파일 배포 제외

### 조치 완료 기준

불필요한 경로가 제거되고 반복적인 경로 요청이 탐지·차단되어야 한다.

---

## SCN-04. 로그인 무차별대입

### 취약 위치

```text
Flask App 로그인 API
POST /login
```

### 취약 원인

반복 로그인 실패에 대한 횟수 제한, 지연, 계정 잠금 정책이 적용되어 있지 않다.

### 로컬 구현 범위

* 실습용 더미 계정만 사용
* 로그인 실패 제한이 없는 초기 상태 구성
* 실패 내역을 `login_attempts` 테이블에 저장
* 로그인 성공·실패 JSON 로그 생성
* 비밀번호는 로그에 기록하지 않음

### 예상 이벤트

```text
LOGIN_SUCCESS
LOGIN_FAILED
BRUTE_FORCE_SUSPECTED
```

### AWS 탐지

* AWS WAF Rate-based Rule
* WAF Logs
* CloudWatch Logs
* Lambda 자체 임계치 분석

### 대시보드 표시 위치

```text
쇼핑몰 WAF → K3s nginx → Flask App 로그인 API
```

### 개선 방법

* 일정 횟수 이상 실패 시 계정 임시 잠금
* 로그인 실패 응답 지연
* IP·계정 기준 Rate Limit
* 추가 인증 적용
* 반복 공격 IP 차단

### 조치 완료 기준

설정된 임계치를 초과하면 추가 로그인이 제한되고 대시보드 상태가 해결 또는 방어 중으로 변경되어야 한다.

---

## SCN-05. 취약 컨테이너 이미지

### 취약 위치

```text
쇼핑몰 Flask Docker 이미지
Amazon ECR
```

### 취약 원인

오래되었거나 알려진 취약점이 포함된 Base Image 또는 패키지를 사용한다.

### 로컬 구현 범위

* 취약 이미지와 개선 이미지 분리
* 이미지 안에 `.env` 및 인증정보 포함 금지
* 로컬 이미지 스캔 결과 저장
* 정상 이미지와 취약 이미지의 결과 비교

### 이미지 구분

```text
shop-app:vulnerable-v1
shop-app:fixed-v2
```

### AWS 탐지

* Amazon ECR Image Scan
* Amazon Inspector
* Security Hub

### 대시보드 표시 위치

```text
Amazon ECR → Inspector → Flask App 이미지
```

### 개선 방법

* Base Image 업데이트
* 취약 패키지 업데이트 또는 제거
* 불필요한 패키지 제거
* 비root 사용자 실행
* 이미지 재빌드 및 재검사

### 조치 완료 기준

개선 이미지를 다시 검사했을 때 대상 Critical/High 취약점이 제거되거나 허용 기준 이하로 감소해야 한다.

---

## SCN-06. Port Scan

### 취약 위치

```text
K3s EC2 또는 Flask App EC2의 네트워크 접근 지점
```

### 취약 원인

필요하지 않은 포트가 열려 있거나 보안그룹의 출발지 범위가 지나치게 넓다.

### 로컬 구현 범위

* 실제 AWS 탐지 대신 더미 이벤트 준비
* Docker 컨테이너 포트 노출 상태 확인
* MySQL 3306은 호스트에 공개하지 않음
* Flask는 로컬 환경에서 `127.0.0.1`에만 바인딩

### AWS 탐지

* GuardDuty
* VPC Flow Logs
* CloudWatch Logs 기반 분석

### 대시보드 표시 위치

```text
Security Group → K3s EC2 또는 Flask App EC2
```

### 개선 방법

* 불필요한 포트 제거
* 보안그룹 출발지를 다른 보안그룹 ID로 제한
* MySQL 접근을 Flask App SG로 한정
* SSH 22번 차단
* SSM Session Manager 사용

### 조치 완료 기준

허용되지 않은 출발지와 불필요한 포트로의 연결이 거부되어야 한다.

---

## SCN-07. 탈취 자격증명 비정상 API 호출

### 취약 위치

```text
AWS IAM 실습용 사용자 또는 역할
```

### 취약 원인

장기 미사용 자격증명이 활성화되어 있거나 필요 이상의 IAM 권한이 부여되어 있다.

### 로컬 구현 범위

* 실제 AWS 자격증명을 생성하거나 저장하지 않음
* 더미 CloudTrail 및 GuardDuty 이벤트 준비
* 이벤트 파싱과 대시보드 표시만 테스트
* 실제 시나리오는 AWS 실습 계정에서 최소권한 자격증명으로 진행

### AWS 탐지

* CloudTrail
* GuardDuty
* EventBridge

Access Analyzer는 자격증명 탈취 탐지보다 외부에 공개된 IAM·S3 접근 정책 분석에 사용한다.

### 대시보드 표시 위치

```text
IAM → CloudTrail → GuardDuty
```

### 개선 방법

* 대상 Access Key 비활성화
* IAM 정책 권한 축소
* 자격증명 교체
* 장기 미사용 자격증명 제거
* 임시 자격증명과 IAM Role 사용

### 조치 완료 기준

문제 자격증명이 비활성화되고 동일한 자격증명을 통한 추가 API 호출이 거부되어야 한다.

---

# 5. 시나리오별 구현 범위 요약

| ID     | 시나리오          | 로컬 구현             | AWS 검증               |
| ------ | ------------- | ----------------- | -------------------- |
| SCN-01 | SQL Injection | Flask 검색 기능       | WAF                  |
| SCN-02 | XSS           | Flask 후기 기능       | WAF                  |
| SCN-03 | 디렉터리 서치       | Flask/nginx 더미 경로 | WAF/CloudWatch       |
| SCN-04 | 로그인 무차별대입     | Flask 로그인 기능      | WAF/CloudWatch       |
| SCN-05 | 취약 컨테이너 이미지   | Docker 이미지·로컬 스캔  | ECR/Inspector        |
| SCN-06 | Port Scan     | 더미 이벤트·포트 점검      | GuardDuty/Flow Logs  |
| SCN-07 | 탈취 자격증명       | 더미 이벤트            | GuardDuty/CloudTrail |

# 6. 대시보드 표시 항목

각 탐지 결과에는 다음 정보가 포함되어야 한다.

```text
시나리오명
발생 위치
탐지 시간
탐지 서비스
심각도
출발지 IP 또는 주체
공격 대상
탐지 근거
방어 결과
근본 취약점
권장 조치
조치 상태
재점검 결과
```

WAF가 공격을 차단했더라도 애플리케이션 취약점이 수정되지 않았다면 다음처럼 구분한다.

```text
공격 결과: 차단됨
근본 취약점: 미조치
현재 상태: 조치 필요
```

# 7. 안전 조건

* 모든 데이터는 더미 데이터를 사용한다.
* 실제 개인정보와 운영 자격증명을 사용하지 않는다.
* 로컬 Flask 포트는 `127.0.0.1`에만 바인딩한다.
* 로컬 MySQL 포트는 호스트에 공개하지 않는다.
* 취약 환경은 허가된 실습 AWS 계정에서만 실행한다.
* SSH 22번은 사용하지 않고 SSM을 사용한다.
* 실습 종료 후 취약 서버를 중지하거나 접근을 제한한다.
* 취약 코드와 개선 코드의 변경 이력을 구분한다.

# 8. 완료 기준

각 시나리오는 다음 자료가 준비되면 완료로 판단한다.

```text
취약 위치
취약 원인
탐지 이벤트
관련 로그
탐지 서비스
대시보드 표시 정보
권장 조치
개선 버전
재점검 결과
```
