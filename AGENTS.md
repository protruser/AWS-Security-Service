# Repository rules

- 기존 코드와 더미데이터를 요청 없이 삭제하지 않는다.
- 실제 인증정보를 커밋하지 않는다. `.env`, DB 데이터, 로그, 키 파일은 Git에서 제외한다.
- 관련 없는 파일을 변경하지 않는다.
- Python 수정 후 `python -m pytest`를 실행한다.
- Docker 설정 수정 후 이미지 빌드와 Health Check를 확인한다. 환경 제한 시 정확히 보고한다.
- 의도적인 취약점은 별도 요청 없이 추가하지 않는다.
- 사용자 요청 없이 Git push 또는 배포하지 않는다.
- 현재 범위는 로컬 Flask/MySQL 환경이다. AWS/Terraform/ECR/CI 배포를 추가하지 않는다.
