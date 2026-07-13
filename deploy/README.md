# VPS 배포

현재 운영 구성은 백엔드와 빌드된 프런트엔드를 Docker Compose 네트워크에서
실행합니다. 호스트에는 프런트엔드 게이트웨이만 `127.0.0.1:8600`으로 공개하고,
호스트의 Caddy가 `osignal.gilgop.cloud` TLS 연결을 종료합니다. 백엔드는 내부
애플리케이션 네트워크와 외부 통신용 네트워크를 분리해 사용합니다.

## DNS

현재 서비스 주소는 다음 A 레코드를 사용합니다.

```text
유형: A
이름: osignal
값: REDACTED_DEPLOY_IP
프록시: DNS 전용
TTL: 자동
```

## 환경 변수

`deploy/.env.example`을 `deploy/.env`로 복사한 뒤 필요한 값만 설정합니다.

- `DATABASE_URL`: 마이그레이션 001~006이 적용된 승인된 PostgreSQL 연결 주소
- `OPENAI_API_KEY`, `OPENAI_MODEL`: 승인된 온디맨드 작업자용 제공자 설정
- `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT_SECONDS`: 소규모 DB 요금제를
  위한 선택적 연결 풀 설정

값을 비워 두면 기준 시각이 포함된 정적 예시 데이터 상태로 실행할 수 있습니다.
운영 Compose는 브리핑·시나리오 작업자와 시나리오 기능을 명시적으로 켜므로,
실데이터 생성 기능을 사용하려면 데이터베이스와 제공자 설정이 모두 준비되어야
합니다. 실제 키는 추적되지 않는 `deploy/.env`에만 보관합니다.

## 실행과 확인

배포 승인을 받은 뒤 저장소 루트에서 실행합니다.

```bash
docker compose --env-file deploy/.env -f deploy/compose.yml up -d --build
curl -fsS http://127.0.0.1:8600/api/health
```

외부 상태 확인 주소는 `https://osignal.gilgop.cloud/api/health`입니다. Caddy 사이트
설정은 `deploy/osignal.gilgop.cloud.caddy`에 있습니다. 재배포, 운영 데이터 쓰기,
마이그레이션 적용에는 각각 프로젝트 운영 규칙에 따른 승인이 필요합니다.
