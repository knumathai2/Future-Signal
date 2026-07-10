<!--
Purpose:        Executable task plan for a fully automated, evidence-grounded context-candidate and v4 report pipeline
Owner:          PM / Planner
Update Trigger: Policy approval, task scope change, or implementation handoff
Harness Version: 1.1
-->

# TASK-055 — 자동 맥락 수집·검증·요약 실행 계획

_작성일: 2026-07-10_

_계획 기준: 한 사람이 AI 개발 도구를 사용해 약 20시간 동안 순차 구현_

_현재 상태: 계획만 작성됨. 코드, DB, API, 정책, 외부 호출은 변경하지 않음._

## 1. 목표

변화가 관찰된 이슈에 대해 사람의 후보 검토 없이 다음 흐름을 자동으로
완성한다.

```text
변화 감지
→ OpenRouter 웹 검색
→ 인용 정보 정규화
→ 규칙 기반 검증
→ 독립 AI 검증
→ 자동 공개 판정
→ 근거 묶음 저장
→ 근거 ID 기반 v4 요약
→ 차트·맥락·출처 통합 표시
```

최종 사용자는 한 화면에서 다음을 이해할 수 있어야 한다.

1. 언제, 어느 정도의 변화가 관찰됐는가
2. 같은 구간에 어떤 공개 정보가 확인됐는가
3. 해당 정보와 변화 사이에서 현재 알 수 없는 것은 무엇인가
4. 이후 어떤 자료와 데이터 갱신을 확인해야 하는가

## 2. 범위와 비범위

### 포함

- 기존 OpenRouter 키와 OpenAI 호환 SDK 경로 재사용
- OpenRouter `openrouter:web_search` 서버 도구 사용
- 시장별 제한된 검색 질의 생성
- API가 반환한 URL 인용 정보만 후보 근거로 인정
- URL, 날짜, 도메인, 엔티티, 중복 규칙 검증
- 연구 모델과 다른 계열의 독립 검증 모델 사용
- 자동 공개/미표시 판정
- 새 append-only migration과 후보 저장
- 기존 정기 배치에 자동 맥락 단계를 연결
- 근거 ID가 포함된 v4 리포트
- 변화 에피소드 중심 API와 UI
- 실패·비용·출처·모델·정책 버전 감사 기록

### 제외

- 범용 웹 크롤러
- 벡터 DB
- 무제한 에이전트 반복
- 임의 소셜 게시물 수집
- 외부 사건이 데이터 움직임을 만들었다는 관계 판단
- 개별 참여자 데이터
- 검색 원문 전체 장기 저장
- 자동화 조건을 통과하지 못한 후보의 사용자 표시
- 기존 migration 수정

## 3. 사전 승인 게이트

`TASK-056`이 승인되기 전에는 `TASK-057` 이후를 시작하지 않는다.

승인 문서에는 다음 변경을 하나씩 명시해야 한다.

- 현재 금지된 공개 자동 맥락 매칭을 검증 기반 자동화로 대체
- 사람 검토 조건 제거
- 자동 공개 조건과 fail-closed 원칙
- OpenRouter 웹 검색과 검증 모델 호출 허용
- 총 `$100` 범위의 해커톤 외부 호출 예산
- 새 DB migration 허용
- v4 공개 API 응답 변경 허용
- UI의 변화 에피소드 구조 변경 허용
- local/dev DB 후보·리포트 쓰기 허용 범위
- 배포는 여전히 별도 승인 대상으로 유지

## 4. 고정 아키텍처

### 4.1 배치 순서

```text
scheduled_batch
├─ collect/normalize
├─ snapshots/metrics
├─ expectation-shift detection
├─ context research and verification
├─ v4 report generation
└─ collection log
```

`context research and verification`는 `signal_detection` 뒤,
`ai_report_batch` 앞에 들어간다.

### 4.2 실행 대상

다음 중 하나를 만족하는 이슈만 조사한다.

- 이번 실행에서 새 expectation-shift가 생성됨
- 24시간 절대 변화가 설정 기준 이상
- 현재 heat 상위 10개
- 성공한 후보 묶음이 없거나 24시간 이상 지남

최초 backfill만 전체 30~50개를 한 번 처리한다.

### 4.3 호출 상한

- 시장당 검색 최대 6회
- 검색 결과 전체 최대 30개
- 규칙 검증을 통과한 후보 최대 8개
- 독립 AI 검증 대상 최대 5개
- 저장 가능한 자동 공개 후보 최대 3개
- 연구 호출 1회, 검증 호출 1회, 작성 호출 1회
- malformed/schema 실패는 한 번만 보정 재시도
- 안전 또는 의미 검증 실패는 같은 입력으로 자동 재시도하지 않음

## 5. 데이터 계약

### 5.1 연구 입력

```json
{
  "market_id": "uuid",
  "episode_at": "ISO-8601",
  "title": "...",
  "description": "...",
  "category": "...",
  "tracked_condition": "...",
  "end_date": "ISO-8601|null",
  "resolution_source": "url|null",
  "current_value": 0.225,
  "change_24h": -0.065,
  "change_7d": 0.02,
  "inflection_at": "ISO-8601|null",
  "search_window_start": "ISO-8601",
  "search_window_end": "ISO-8601",
  "allowed_domains": ["example.gov"]
}
```

### 5.2 OpenRouter 인용 정규화

모델 본문에 포함된 URL은 근거로 인정하지 않는다. API 응답의
`url_citation` annotation만 아래 구조로 변환한다.

```json
{
  "citation_id": "citation:sha256",
  "url": "https://...",
  "canonical_url": "https://...",
  "title": "...",
  "domain": "...",
  "content_excerpt": "...",
  "content_hash": "sha256",
  "retrieved_at": "ISO-8601"
}
```

`content_excerpt`는 검증 입력에만 사용하고 사용자 화면에는 그대로 노출하지
않는다.

### 5.3 연구 모델 출력

```json
{
  "queries": ["..."],
  "candidates": [
    {
      "candidate_key": "candidate:local-id",
      "title": "...",
      "event_at": "ISO-8601|null",
      "citation_ids": ["citation:sha256"],
      "matched_entities": ["..."],
      "matched_condition": "...",
      "temporal_relation": "before_window|same_window|after_window"
    }
  ]
}
```

### 5.4 독립 검증 출력

```json
{
  "candidate_key": "candidate:local-id",
  "accepted": true,
  "condition_match": true,
  "date_match": true,
  "source_supported": true,
  "unsupported_claims": [],
  "conflicting_citation_ids": [],
  "neutral_summary_ko": "...",
  "reason_code": "primary_source_direct_match"
}
```

### 5.5 자동 공개 판정

다음 경로 중 하나와 공통 조건을 모두 충족해야 한다.

허용 경로:

- 공식 출처 한 개가 핵심 주체와 추적 조건을 직접 언급
- 독립된 출처 두 개 이상이 동일 사건·날짜를 확인
- `resolutionSource`와 같은 공식 출처 계열이 핵심 조건을 직접 언급

공통 조건:

- 모든 URL이 OpenRouter annotation에서 유래
- URL 접근과 canonicalization 성공
- 핵심 주체와 추적 조건 일치
- 사건 날짜가 검색 구간과 호환
- 상충하는 인용 정보 없음
- 연구 모델과 검증 모델이 관련성에 동의
- 사용자용 중립 요약이 근거 범위를 넘지 않음
- 관계 단정과 실제 결과 단정이 없음

미충족 후보는 `withheld` 또는 `rejected`로 저장할 수 있지만 공개 API에서
제외한다.

### 5.6 v4 리포트 응답 초안

```json
{
  "id": "uuid",
  "status": "success",
  "report_version": "v4",
  "generated_at": "ISO-8601",
  "data_as_of": "ISO-8601",
  "episode_at": "ISO-8601",
  "content": {
    "issue_overview": "...",
    "observed_change": "...",
    "context_summary": "...",
    "relationship_boundary": "...",
    "what_to_check": "...",
    "data_limitations": "...",
    "caution_note": "..."
  },
  "evidence_refs": ["metric:123", "candidate:uuid"],
  "context_candidates": [
    {
      "id": "uuid",
      "title": "...",
      "event_at": "ISO-8601",
      "summary": "...",
      "sources": [
        {
          "title": "...",
          "url": "https://...",
          "domain": "...",
          "published_at": "ISO-8601|null",
          "source_type": "official|independent_secondary"
        }
      ]
    }
  ]
}
```

`context_summary`는 공개 후보가 없으면 `null`로 둘 수 있다. 공개 후보가 없을
때 긴 후보 부재 문장을 생성하지 않는다.

## 6. 저장 모델

새 migration은 `backend/migrations/002_context_candidates.sql`로 추가하고
기존 `001_initial_schema.sql`을 수정하지 않는다.

### `context_candidates`

| 필드 | 목적 |
|---|---|
| `id` | 후보 UUID |
| `market_id` | 시장 FK |
| `episode_at` | 연결된 변화 에피소드 시각 |
| `event_title` | 검증된 후보 제목 |
| `event_at` | 공개 정보의 기록 시각 |
| `neutral_summary` | 검증된 한국어 중립 요약 |
| `sources` | 출처 배열 JSONB |
| `verification_state` | `verified`, `withheld`, `rejected` |
| `verification_score_internal` | 감사·디버깅용 내부 점수 |
| `research_model` | 연구 모델 식별자 |
| `verifier_model` | 검증 모델 식별자 |
| `policy_version` | 자동 공개 정책 버전 |
| `evidence_hash` | 인용 묶음 해시 |
| `collected_at` | 수집 시각 |
| `expires_at` | 재검증 기준 시각 |

### `context_collection_runs`

| 필드 | 목적 |
|---|---|
| `id` | 실행 UUID |
| `market_id` | 시장 FK |
| `episode_at` | 대상 변화 시각 |
| `started_at`, `finished_at` | 실행 시각 |
| `status` | `success`, `partial`, `failed`, `no_candidate` |
| `query_count` | 검색 횟수 |
| `result_count` | 검색 결과 수 |
| `accepted_count` | 공개 후보 수 |
| `model_usage` | 모델·토큰·웹 검색 횟수 JSONB |
| `error_detail` | 비밀값이 없는 오류 JSONB |

## 7. 작업 패킷

### TASK-056 — 자동 맥락 정책과 v4 계약 승인

- **Owner**: PM / Planner
- **Branch**: `pm/TASK-056-auto-context-policy`
- **예상 시간**: 1시간
- **의존성**: TASK-055
- **승인 게이트**: 이 작업 자체가 후속 구현의 인간 승인 게이트
- **수정 범위**:
  - `AGENTS.md`
  - `memory/decisions.md`
  - `memory/glossary.md`
  - `standards.md`
  - `roadmap.md`
  - PRD, Service Design, Technical Design, UX Design 관련 섹션
  - `backend/API_CONTRACT.md`의 v4 설계 구간
- **수행 내용**:
  1. 사람 검토 제거를 자동 검증 정책으로 대체한다.
  2. 자동 공개 조건과 미표시 조건을 고정한다.
  3. OpenRouter 검색·검증·작성 호출과 `$100` 예산을 승인 범위에 넣는다.
  4. 새 migration, 공개 API, local/dev 쓰기 범위를 승인 항목으로 기록한다.
  5. 관계 단정, 실제 결과 단정, 개별 참여자 기능 금지는 유지한다.
- **완료 조건**:
  - [ ] 새 ADR이 Accepted 상태이며 사용자가 명시적으로 승인함
  - [ ] 기존 자동 매칭 금지 조항과 새 허용 경계가 충돌하지 않음
  - [ ] v4 응답 필드, nullability, 근거 참조 규칙이 문서에 고정됨
  - [ ] DB/API/provider/local-dev-write 승인 범위가 각각 기록됨
  - [ ] 배포는 승인 범위에서 제외됨
- **검증**:
  - 문서 상호참조 확인
  - hard-block 및 관계 단정 문구 lint
  - `git diff --check`
- **handoff**: TASK-057, TASK-058

### TASK-057 — 자동 맥락 저장 스키마

- **Owner**: Backend Implementer
- **Branch**: `backend/TASK-057-context-schema`
- **예상 시간**: 1.5시간
- **의존성**: TASK-056 승인
- **승인 게이트**: TASK-056에 기록된 DB schema 승인 필요
- **수정 범위**:
  - `backend/migrations/002_context_candidates.sql`
  - `backend/app/db/models.py`
  - schema/model 테스트
- **수행 내용**:
  1. `context_candidates`, `context_collection_runs`를 append-only로 추가한다.
  2. `market_id`, `episode_at`, `verification_state` 조회 인덱스를 추가한다.
  3. 출처·사용량·오류는 JSONB로 저장하되 비밀값은 저장하지 않는다.
  4. 기존 `related_events`와 `ai_reports`는 수정하지 않는다.
- **완료 조건**:
  - [ ] 새 migration만 추가되고 기존 migration은 변경되지 않음
  - [ ] Postgres와 테스트 DB에서 모델 생성 가능
  - [ ] verified/withheld/rejected 상태가 enum 또는 check constraint로 제한됨
  - [ ] duplicate `evidence_hash` 처리 규칙이 존재함
  - [ ] cascade/delete 동작이 문서화됨
- **검증**:
  - `DATABASE_URL= .venv/bin/pytest tests/test_context_models.py`
  - `.venv/bin/ruff check app tests`
  - `git diff --check`
- **handoff**: TASK-060, TASK-062

### TASK-058 — OpenRouter 웹 연구 클라이언트

- **Owner**: Data/AI Implementer
- **Branch**: `data-ai/TASK-058-context-research`
- **예상 시간**: 2.5시간
- **의존성**: TASK-056 승인
- **수정 범위**:
  - `backend/app/core/context_research.py`
  - `backend/app/core/config.py`
  - `backend/.env.example`
  - `backend/tests/test_context_research.py`
- **수행 내용**:
  1. 기존 OpenRouter SDK/base URL/key 선택 경로를 재사용한다.
  2. `openrouter:web_search` 서버 도구 요청을 구현한다.
  3. 시장 메타데이터에서 최대 6개 검색 질의를 만든다.
  4. API `url_citation` annotation을 별도 구조로 파싱한다.
  5. 모델 본문 URL을 폐기하고 annotation URL만 반환한다.
  6. 엄격한 JSON schema로 후보 초안을 파싱한다.
  7. 모델·검색 횟수·결과 상한을 설정으로 노출한다.
- **완료 조건**:
  - [ ] 웹 검색 도구가 없는 일반 응답은 안전하게 실패함
  - [ ] annotation이 없는 후보는 반환되지 않음
  - [ ] 검색 결과 30개, 질의 6개 상한이 강제됨
  - [ ] prompt/response 전문과 API key가 로그에 남지 않음
  - [ ] fake client로 성공·빈 결과·malformed·timeout 테스트 통과
- **검증**:
  - `DATABASE_URL= .venv/bin/pytest tests/test_context_research.py`
  - `.venv/bin/ruff check app tests`
  - provider 호출 없이 전체 테스트 통과
- **handoff**: TASK-059

### TASK-059 — 규칙 검증과 독립 AI 검증자

- **Owner**: Data/AI Implementer
- **Branch**: `data-ai/TASK-059-context-verification`
- **예상 시간**: 2.5시간
- **의존성**: TASK-058
- **수정 범위**:
  - `backend/app/core/context_verification.py`
  - `backend/tests/test_context_verification.py`
- **수행 내용**:
  1. URL canonicalization, 도메인 분류, 날짜 범위, 엔티티 일치, 중복 제거를
     결정적으로 구현한다.
  2. 공식 출처 1개 또는 독립 출처 2개 경로를 구현한다.
  3. 연구 모델과 다른 모델 식별자를 사용하는 검증 클라이언트를 구현한다.
  4. 검증 모델에는 annotation 근거와 후보만 전달하고 웹 검색을 허용하지 않는다.
  5. 자동 공개 조건을 코드 판정으로 구현한다.
  6. 상충·약한 일치·근거 밖 서술은 withheld/rejected로 보낸다.
- **완료 조건**:
  - [ ] 모델이 승인하더라도 hard gate 실패 후보는 verified가 될 수 없음
  - [ ] 공식 단일 출처와 독립 복수 출처 경로 테스트 통과
  - [ ] 모델 생성 URL·날짜·고유명사는 근거와 불일치 시 거부됨
  - [ ] 연구자/검증자 불일치 시 공개되지 않음
  - [ ] 동일 기사 재배포는 독립 출처로 계산되지 않음
  - [ ] 관계 단정 문구 검출 시 거부됨
- **검증**:
  - `DATABASE_URL= .venv/bin/pytest tests/test_context_verification.py`
  - `.venv/bin/ruff check app tests`
  - 고정 fixture로 판정 재현성 확인
- **handoff**: TASK-060

### TASK-060 — 맥락 조사 배치와 저장 연결

- **Owner**: Data/AI Implementer
- **Branch**: `data-ai/TASK-060-context-batch`
- **예상 시간**: 2시간
- **의존성**: TASK-057, TASK-058, TASK-059
- **수정 범위**:
  - `backend/app/core/context_research_batch.py`
  - `backend/app/core/scheduled_batch.py`
  - DB query/helper
  - `backend/tests/test_context_research_batch.py`
  - `backend/tests/test_scheduled_batch.py`
- **수행 내용**:
  1. 조사 대상 이슈를 signal/heat/staleness 규칙으로 선택한다.
  2. 조사 → 규칙 검증 → 독립 검증 → 저장을 시장별로 격리한다.
  3. 후보와 실행 로그를 append-only로 저장한다.
  4. verified 후보만 후속 v4 생성 입력으로 전달한다.
  5. 한 시장 실패가 전체 배치를 중단하지 않게 한다.
  6. provider 실패가 있으면 기존 성공 후보·리포트를 유지한다.
- **완료 조건**:
  - [ ] 신규 signal, heat, staleness 선택 규칙 테스트 통과
  - [ ] 시장별 실패 격리와 transaction rollback 확인
  - [ ] 후보 3개·검색 6회 상한 강제
  - [ ] verified만 리포트 입력에 포함
  - [ ] no_candidate도 정상 성공 상태로 기록
  - [ ] 비용/토큰/검색 횟수가 run log에 기록됨
- **검증**:
  - `DATABASE_URL= .venv/bin/pytest tests/test_context_research_batch.py tests/test_scheduled_batch.py`
  - `.venv/bin/ruff check app tests`
  - fake research/verifier client 통합 테스트
- **handoff**: TASK-061

### TASK-061 — 근거 기반 v4 리포트 생성

- **Owner**: Data/AI Implementer
- **Branch**: `data-ai/TASK-061-evidence-report-v4`
- **예상 시간**: 2시간
- **의존성**: TASK-060
- **수정 범위**:
  - `backend/app/core/ai_report.py`
  - `backend/app/core/ai_report_batch.py`
  - v4 content 모델과 safety/semantic validation
  - 관련 테스트
- **수행 내용**:
  1. 구조화 지표와 verified 후보만 작성 모델 입력으로 전달한다.
  2. v4 고정 필드와 `evidence_refs`를 생성한다.
  3. 수치 문장은 metric ID, 맥락 문장은 candidate ID를 참조하게 한다.
  4. 후보가 없으면 `context_summary=null`로 둔다.
  5. 수치 일치, 후보 ID 존재, 출처 존재, 관계 경계 문구를 검증한다.
  6. v3 행은 감사 이력으로 보존하고 v4 응답에서 제외한다.
- **완료 조건**:
  - [ ] extra/missing field가 저장되지 않음
  - [ ] 모델이 만든 수치가 입력과 다르면 거부됨
  - [ ] 존재하지 않는 evidence ref가 있으면 거부됨
  - [ ] context가 있는데 관계 경계 문구가 없으면 거부됨
  - [ ] context가 없을 때 부재 설명을 생성하지 않음
  - [ ] hard-block, 관계 단정, 실제 결과 단정 필터 통과
- **검증**:
  - `DATABASE_URL= .venv/bin/pytest tests/test_ai_report.py tests/test_ai_report_batch.py`
  - `.venv/bin/ruff check app tests`
  - metric/candidate 불일치 회귀 테스트
- **handoff**: TASK-062

### TASK-062 — v4 맥락·리포트 API

- **Owner**: Backend Implementer
- **Branch**: `backend/TASK-062-context-report-api`
- **예상 시간**: 2시간
- **의존성**: TASK-057, TASK-061
- **수정 범위**:
  - `backend/API_CONTRACT.md`
  - `backend/app/schemas/issues.py`
  - `backend/app/api/routes/issues.py`
  - DB query helper
  - API contract/live 테스트
- **수행 내용**:
  1. v4 성공 응답을 strict schema로 제공한다.
  2. verified 후보와 공개 가능한 출처 필드만 반환한다.
  3. `data_as_of <= generated_at`과 episode/candidate 연결을 검증한다.
  4. v1~v3, failed, malformed, evidence 불일치 행은 제공하지 않는다.
  5. 후보/리포트 부재와 unknown issue 동작을 문서화한다.
- **완료 조건**:
  - [ ] v4 필드·타입·nullability가 계약과 일치
  - [ ] verified 이외 후보가 API에 노출되지 않음
  - [ ] 출처 URL이 citation 저장값과 일치
  - [ ] legacy/malformed/evidence-missing 행은 not-yet-generated 처리
  - [ ] timestamp와 연결 무결성 테스트 통과
- **검증**:
  - `DATABASE_URL= .venv/bin/pytest tests/test_issues_contract.py tests/test_issues_live.py`
  - `.venv/bin/ruff check app tests`
  - OpenAPI schema 확인
- **handoff**: TASK-063

### TASK-063 — 변화 에피소드 UI

- **Owner**: Frontend Implementer
- **Branch**: `frontend/TASK-063-change-episode-ui`
- **예상 시간**: 2.5시간
- **의존성**: TASK-062
- **수정 범위**:
  - Frontend v4 API types/parser
  - `IssueReportCard` 대체 또는 v4 분기
  - 변화 에피소드·출처 카드 컴포넌트
  - 차트 marker 연결
  - 관련 parser/component 테스트
- **수행 내용**:
  1. 7~8개 one-section 흐름을 한 장의 변화 에피소드로 바꾼다.
  2. 관찰된 변화, 같은 구간의 공개 정보, 추가 확인, 데이터 한계를 순서대로
     배치한다.
  3. 후보 날짜와 차트 marker를 같은 episode/candidate ID로 연결한다.
  4. 출처 제목·도메인·발행일·원문 링크를 제공한다.
  5. 후보가 없으면 맥락 영역 전체를 숨긴다.
  6. 짧은 상시 주의와 상세 한계를 계층화한다.
- **완료 조건**:
  - [ ] 320px, 375px, desktop에서 가로 넘침 없음
  - [ ] 후보 0/1/3개 상태 모두 정상
  - [ ] 출처 링크가 새 창에서 안전하게 열림
  - [ ] data-as-of와 해석 주의가 같은 viewport에 존재
  - [ ] 차트 marker와 후보 카드 ID가 일치
  - [ ] loading/not-yet-generated/error 상태가 기존보다 퇴행하지 않음
- **검증**:
  - `npm run typecheck`
  - `npm run lint`
  - `npm run build`
  - parser/component 테스트
  - Browser QA 320px/375px/desktop
- **handoff**: TASK-064

### TASK-064 — 자동 맥락 통합 검수

- **Owner**: Reviewer
- **Branch**: `review/TASK-064-auto-context-integration`
- **예상 시간**: 2시간
- **의존성**: TASK-057~063
- **수정 범위**:
  - 통합 테스트
  - wording lint
  - 계약·스키마·UI 검수 보고서
  - 발견된 범위 내 수정
- **수행 내용**:
  1. schema → batch → 후보 → v4 report → API → UI를 한 흐름으로 검증한다.
  2. 모델 생성 URL, 날짜, 수치, candidate ID 불일치 공격 fixture를 넣는다.
  3. 공식 단일 출처, 독립 복수 출처, 상충, 약한 일치, no-candidate를 검증한다.
  4. 모든 사용자 노출 문장에 관계 단정·실제 결과 단정·행동 유도가 없는지
     검사한다.
  5. source link, data-as-of, caution, null 상태를 브라우저에서 확인한다.
- **완료 조건**:
  - [ ] Backend 전체 테스트와 Ruff 통과
  - [ ] Frontend typecheck/lint/build/test 통과
  - [ ] content-safety lint 통과
  - [ ] 자동 공개 hard gate 우회가 없음
  - [ ] UI 3개 viewport 통과
  - [ ] 스키마/API/정책 변경이 TASK-056 승인 범위를 넘지 않음
- **검증**:
  - Backend full suite
  - Frontend full suite
  - `git diff --check`
  - local Browser QA
- **handoff**: TASK-065

### TASK-065 — local/dev backfill과 데모 증거

- **Owner**: Data/AI Implementer + PM
- **Branch**: `data-ai/TASK-065-context-backfill`
- **예상 시간**: 2시간
- **의존성**: TASK-064
- **승인 게이트**: TASK-056의 provider 비용 및 local/dev DB 쓰기 승인 범위
- **수정 범위**:
  - guarded CLI 또는 기존 scheduled batch 옵션
  - 실행·평가 보고서
  - 필요 시 fixture와 threshold 조정
- **수행 내용**:
  1. local/dev에서 전체 30~50개를 한 번 backfill한다.
  2. 검색·후보·공개·미표시·실패 분포를 기록한다.
  3. 대표 이슈 5개에 대해 차트→후보→요약→출처 흐름을 캡처한다.
  4. 오류가 큰 규칙은 코드 상수 범위에서 한 번 조정한다.
  5. 마지막으로 정기 배치 한 회를 실행해 증분 경로를 검증한다.
- **완료 조건**:
  - [ ] 30개 이상 이슈 조사 완료
  - [ ] verified 후보는 모두 annotation 출처를 가짐
  - [ ] 공개 후보의 URL 접근 성공률 100%
  - [ ] 수치/evidence ref 불일치 0건
  - [ ] 관계 단정·실제 결과 단정 문구 0건
  - [ ] no-candidate가 정상 상태로 표시됨
  - [ ] 총 사용량이 승인 예산 안에 기록됨
  - [ ] 대표 5개 데모 흐름이 중단 없이 동작
- **검증**:
  - guarded local/dev batch
  - read-only post-run audit query
  - API sample validation
  - Browser screenshot/console check
- **handoff**: 별도 승인 후 배포 또는 종료

## 8. 한 사람 순차 실행 순서

| 순서 | 작업 | 누적 시간 | 시작 조건 |
|---:|---|---:|---|
| 1 | TASK-056 정책·계약 | 1h | 사용자 승인 대기 |
| 2 | TASK-057 스키마 | 2.5h | TASK-056 승인 |
| 3 | TASK-058 웹 연구 | 5h | TASK-056 승인 |
| 4 | TASK-059 자동 검증 | 7.5h | TASK-058 완료 |
| 5 | TASK-060 배치 연결 | 9.5h | TASK-057~059 완료 |
| 6 | TASK-061 v4 생성 | 11.5h | TASK-060 완료 |
| 7 | TASK-062 API | 13.5h | TASK-057, 061 완료 |
| 8 | TASK-063 UI | 16h | TASK-062 완료 |
| 9 | TASK-064 통합 검수 | 18h | TASK-057~063 완료 |
| 10 | TASK-065 backfill·데모 | 20h | TASK-064 통과 |

각 작업은 직전 작업이 병합된 최신 기준에서 새 역할 브랜치를 만든다. 한 사람이
순차 실행하므로 동시에 두 구현 브랜치를 열지 않는다.

## 9. 중단 기준

다음 상황에서는 다음 작업으로 넘어가지 않는다.

- TASK-056 정책/스키마/API/provider 승인이 없음
- OpenRouter 응답에서 안정적으로 `url_citation`을 얻지 못함
- 모델 생성 URL과 annotation URL을 구분하지 못함
- 공식 단일 출처 또는 독립 복수 출처 판정이 재현되지 않음
- 후보가 없는 상태를 실패가 아닌 정상 상태로 처리하지 못함
- 근거 ID 없는 문장을 저장 단계에서 차단하지 못함
- 기존 data-as-of 또는 caution 표시가 사라짐
- 금지된 관계·실제 결과·행동 문구를 기계적으로 막지 못함

## 10. 최종 완료 정의

프로그램 전체는 다음 조건을 모두 만족할 때 완료다.

- [ ] 자동 맥락 정책과 v4 계약이 승인·문서화됨
- [ ] 기존 migration을 건드리지 않고 새 저장 구조가 추가됨
- [ ] OpenRouter 검색 결과의 annotation만 근거로 사용함
- [ ] 규칙 검증과 독립 AI 검증을 모두 통과해야 공개됨
- [ ] 조건 미달 후보는 사용자에게 보이지 않음
- [ ] AI 요약의 모든 수치·맥락 문장이 근거 ID를 가짐
- [ ] 변화 차트, 후보, 출처, AI 요약이 episode ID로 연결됨
- [ ] 후보가 없는 이슈도 자연스러운 화면을 제공함
- [ ] 모든 사용자 노출 화면에 data-as-of와 해석 주의가 존재함
- [ ] 전체 Backend/Frontend/문구/브라우저 검증이 통과함
- [ ] 실제 사용량과 오류가 감사 로그에 남음
- [ ] 배포는 별도 승인 없이는 수행되지 않음

## 11. 작업 시작용 공통 프롬프트

각 TASK 시작 시 아래 문장을 역할별 세부 지시 앞에 붙인다.

```text
AGENTS.md와 역할별 context loading order를 먼저 따른다.
TASK-055 실행 계획과 TASK-056에서 승인된 ADR을 구현 경계로 사용한다.
직전 TASK가 병합된 최신 기준에서 지정된 역할 브랜치를 만든다.
승인 범위를 넘는 정책, schema, public API, provider, local/dev DB write,
dependency, infrastructure, deployment 변경은 수행하지 않는다.
기존 migration은 수정하지 않는다.
자동 맥락은 OpenRouter url_citation annotation만 근거로 인정하고,
hard gate 실패 또는 검증 모델 불일치 시 사용자에게 표시하지 않는다.
모든 수치와 맥락 문장은 저장 전에 metric/candidate evidence ID와 대조한다.
완료 시 지정 테스트, wording lint, git diff --check를 실행하고
memory/session.md 및 task ledger를 갱신한다.
```

## 12. 관련 문서

- 배경 분석: `reports/task-055-context-candidate-ai-summary-strategy.md`
- 프로젝트 제약: `AGENTS.md`
- 현재 v3 결정: `memory/decisions.md` ADR-032~035
- 현재 리포트 계약: `backend/API_CONTRACT.md`
- 현재 AI 생성: `backend/app/core/ai_report.py`
- 현재 정기 배치: `backend/app/core/scheduled_batch.py`
- 현재 리포트 UI: `frontend/src/components/IssueReportCard.tsx`
- 핵심 20시간 이후 추가 계획:
  `reports/task-055-automated-context-stretch-plan.md`
