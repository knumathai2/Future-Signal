# 백엔드 — Outlook AI Signals

FastAPI 기반 이슈 데이터 API, PostgreSQL 저장 계층, 시장 데이터 수집기, 근거 기반
v8 브리핑 및 시나리오 작업자로 구성됩니다.

## 실행 구조

- API는 이슈·분류·이력·브리핑을 조회하고 온디맨드 생성 요청과 상태 이벤트를
  추가합니다.
- 제공자 호출과 결과 저장은 API 프로세스가 아니라 요청별 격리 작업자 프로세스가
  담당합니다.
- 일반 시장 데이터 수집은 외부 맥락 조사나 브리핑 생성을 실행하지 않습니다.
- v8 브리핑과 시나리오 응답은 모든 검증을 통과해 저장된 완전한 블록만 SSE로
  전달합니다. 제공자의 원본 조각은 브라우저로 보내지 않습니다.
- 데이터베이스가 없거나 조회에 실패하면 API는 보고서를 만들어 내지 않고, 기준
  시각이 표시된 정적 이슈 예시와 정직한 빈 상태를 반환합니다.

브리핑 블록 스트리밍에는 마이그레이션 005가 필요합니다. 시나리오 대화 API는
기본 비활성화 상태이며, 마이그레이션 006이 적용된 데이터베이스와
`SCENARIO_CONVERSATION_ENABLED=true`가 필요합니다. 운영 환경에서 생성 작업자를
실행하려면 `AI_GENERATION_WORKERS_ENABLED=true`도 설정해야 합니다.

## 설치

macOS arm 환경에서는 Python 3.11을 사용합니다. 이 프로젝트의 고정 PostgreSQL
드라이버는 시스템 Python 3.9에서 설치되지 않을 수 있습니다.

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate     # macOS/Linux
# .venv\Scripts\activate      # Windows
pip install -r requirements-dev.txt
cp .env.example .env
```

`.env`에는 로컬에서 사용할 값을 채우되 저장소에 커밋하지 않습니다.

### Supabase `DATABASE_URL`

다음 두 형식을 모두 지원합니다.

```text
postgresql://USER:ENCODED_PASSWORD@HOST:5432/postgres
postgresql+psycopg://USER:ENCODED_PASSWORD@HOST:5432/postgres
```

비밀번호에 `@`, `#`, `/`, `?`, `&`, `%`, `:` 같은 URL 예약 문자가 있으면 URL
인코딩해야 합니다. Supabase 직접 호스트 연결이 IPv6 경로 오류로 실패하면 대시보드의
pooler 연결 문자열을 사용합니다.

## API 실행

```bash
uvicorn app.main:app --reload
```

- 상태 확인: `http://127.0.0.1:8000/api/health`
- OpenAPI 문서: `http://127.0.0.1:8000/docs`

주요 공개 경로는 `/api/categories`, `/api/issues`,
`/api/issues/{id}/history`, `/api/issues/{id}/report`입니다. 공개 경로 이름은 제품
문구 정책에 맞춰 `issues`, `signals`, `reports`, `categories`를 사용합니다.

## 온디맨드 생성 작업자

`ENV=local`, `dev`, `development`에서는 생성 요청이 큐에 추가된 뒤 요청별 자식
작업자가 자동으로 시작됩니다. 운영 환경에서는
`AI_GENERATION_WORKERS_ENABLED=true`일 때만 자동 시작됩니다. API는 작업 완료를
기다리지 않고 HTTP 202를 반환합니다.

브리핑 작업자를 수동 복구할 때는 처리할 요청을 지정합니다.

```bash
ENV=local ./.venv/bin/python -m app.core.on_demand_worker \
  --request-id <uuid> \
  --confirm-generation-write
```

프런트엔드는 브리핑 요청에 `refresh_context=true`를 전달합니다. 작업자는 승인된
예산 한도 안에서 90일 또는 180일 맥락 조사 경로를 구성하고, 검증된 인용 근거만
저장한 뒤 입력 지문이 바뀌면 후속 요청을 처리합니다.

시나리오 작업자를 수동 복구할 때도 정확한 요청 ID가 필요합니다.

```bash
ENV=local ./.venv/bin/python -m app.core.scenario_worker \
  --request-id <uuid> \
  --confirm-generation-write
```

시나리오 응답은 도구를 사용하지 않는 단일 제공자 호출 뒤 전제 분류, 근거, 문구,
정보 유출, 숫자, 제한된 Markdown, 완전성 검증을 모두 통과한 경우에만 저장됩니다.
시도 횟수가 0인 채 5초 이상 큐에 남은 요청은 인증된 상태 조회나 SSE 재연결 때
프로세스별 20초 대기와 최대 3회 실행 제한 안에서 복구할 수 있습니다. 실행 중이거나
종료된 요청은 자동 재실행하지 않습니다.

## 데이터베이스 연결 풀

프로세스당 기본값은 영구 연결 3개와 초과 연결 1개입니다. 다음 환경 변수는 코드에
정해진 범위 안에서만 조정됩니다.

- `DB_POOL_SIZE`
- `DB_MAX_OVERFLOW`
- `DB_POOL_TIMEOUT_SECONDS`

## 로컬·개발용 차트 이력 채우기

첫 수집 뒤 이슈별 이력이 한 점뿐일 때 승인된 로컬·개발 데이터베이스에 CLOB 가격
이력을 추가할 수 있습니다.

```bash
ENV=local ./.venv/bin/python -m app.core.historical_seed \
  --confirm-local-dev-write
```

이 명령은 기존 행이나 스키마를 바꾸지 않고 `market_snapshots`, `market_metrics`,
변화 감지 결과와 수집 로그를 추가합니다. `ENV`가 `local`, `dev`, `development`,
`test`가 아니거나 확인 플래그가 없으면 실행을 거부합니다.

선택 항목은 다음과 같습니다.

```bash
ENV=local ./.venv/bin/python -m app.core.historical_seed \
  --interval 1w \
  --fidelity 60 \
  --max-markets 10 \
  --confirm-local-dev-write
```

## 정기 시장 데이터 수집

현재 GitHub Actions 워크플로는 UTC 기준 4시간마다 17분에 실행됩니다. 활성 이진
시장 최대 50개를 가져와 스냅샷·지표·변화 감지 결과·수집 상태를 추가하며, AI 관련
단계는 명시적으로 건너뜁니다.

```bash
ENV=local ./.venv/bin/python -m app.core.scheduled_batch \
  --use-live-fetch \
  --max-samples 50 \
  --skip-ai-reports \
  --skip-context-research \
  --confirm-local-dev-write
```

워크플로 파일은 `.github/workflows/four-hour-collection.yml`이며 `DATABASE_URL`만
사용합니다. `--reports-only`와 v4 호환 옵션은 감사·개발 비교를 위해 남아 있지만
현재 v8 운영 경로에는 포함되지 않습니다.

## 검사

```bash
ruff check .
pytest
```

마이그레이션, 제공자 호출, 다른 데이터베이스 쓰기, 운영 데이터 쓰기와 배포에는
각각 `AGENTS.md`에 기록된 승인이 필요합니다.
