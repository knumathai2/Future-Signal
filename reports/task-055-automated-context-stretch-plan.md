<!--
Purpose:        Prioritized stretch-task plan after the 20-hour automated-context core program
Owner:          PM / Planner
Update Trigger: TASK-065 completion, additional time allocation, or stretch-scope approval
Harness Version: 1.1
-->

# TASK-055 — 자동 맥락 파이프라인 추가 시간 계획

_작성일: 2026-07-10_

_시작 조건: `TASK-056` 승인과 `TASK-057`~`TASK-065` 완료_

_현재 상태: 계획만 작성됨. 구현, 외부 호출, DB 쓰기, 정책 변경은 없음._

## 1. 우선순위 원칙

추가 시간은 새로운 화면 수보다 다음 순서로 사용한다.

1. 잘못된 후보를 자동 공개하지 않는 능력
2. 출처 선택과 검증 판정의 재현성
3. 시간이 지나도 후보가 유효한지 다시 확인하는 능력
4. 과거 변화 구간과 비영어권 출처의 커버리지
5. 사용자가 근거를 직접 추적할 수 있는 화면
6. 검색·모델·네트워크 장애에 대한 운영 안정성
7. 같은 외부 사건을 여러 이슈에서 재사용하는 구조

`TASK-065` 완료 직후에는 기능 확장보다 `TASK-066` 평가 harness를 먼저
실행한다. 평가 없이 검색 범위나 모델 호출을 늘리지 않는다.

## 2. 추가 시간별 권장 중단 지점

| 추가 가능 시간 | 수행 작업 | 누적 추가 시간 | 얻는 효과 |
|---:|---|---:|---|
| 3시간 | TASK-066 | 3h | 자동화 품질을 수치와 회귀 fixture로 확인 |
| 6시간 | + TASK-067 | 6h | 공식 출처 선택의 재현성과 카테고리 커버리지 향상 |
| 9시간 | + TASK-068 | 9h | 출처 간 상충과 근거 밖 서술 차단 강화 |
| 11시간 | + TASK-069 | 11h | 링크·내용 변경·후보 만료 자동 처리 |
| 14시간 | + TASK-070 | 14h | 7일/30일 변화 에피소드 타임라인 제공 |
| 17시간 | + TASK-071 | 17h | 비영어권 공식 출처 발견 범위 확대 |
| 19.5시간 | + TASK-072 | 19.5h | 사용자가 출처와 검증 근거를 직접 확인 |
| 22시간 | + TASK-073 | 22h | 캐시·재시도·provider 장애 대응 강화 |
| 25시간 | + TASK-074 | 25h | 하나의 사건을 여러 관련 이슈와 공유 |

가장 높은 효율 구간은 추가 6시간(`TASK-066`~`TASK-067`)이다. 추가 11시간을
확보하면 자동 공개 정확도와 후보 수명 관리까지 닫을 수 있다.

## 3. Stretch 작업 패킷

### TASK-066 — 자동 맥락 평가 harness

- **Owner**: Reviewer + Data/AI Implementer
- **Branch**: `review/TASK-066-context-evaluation`
- **예상 시간**: 3시간
- **의존성**: TASK-065
- **목표**: 실제 provider를 반복 호출하지 않고도 수집·검증·요약의 품질을
  재현 가능한 fixture와 지표로 평가한다.
- **수정 범위**:
  - `backend/tests/fixtures/context_evaluation/`
  - `backend/app/evaluation/context_pipeline_eval.py`
  - `backend/tests/test_context_pipeline_eval.py`
  - 평가 결과 보고서
- **수행 내용**:
  1. 공식 단일 출처, 독립 복수 출처, 재배포 중복, 날짜 불일치, 약한 주체
     일치, 출처 상충, 후보 없음, 모델 생성 URL 사례를 fixture로 만든다.
  2. OpenRouter annotation과 모델 JSON을 저장한 offline replay 형식을 만든다.
  3. citation integrity, condition match, temporal match, duplicate rejection,
     unsupported-claim rejection, no-candidate accuracy를 계산한다.
  4. v4 요약의 metric/evidence ref 정합성과 관계 경계 문구를 평가한다.
  5. 기준 미달이면 CI에서 실패하도록 임계값을 고정한다.
- **완료 조건**:
  - [ ] 최소 20개 fixture와 8개 실패 유형 존재
  - [ ] provider/DB 없이 전체 평가 실행 가능
  - [ ] 모델 생성 URL 수용률 0%
  - [ ] known-conflict 자동 공개율 0%
  - [ ] known-duplicate 독립 출처 계산률 0%
  - [ ] metric/evidence ref 불일치 저장률 0%
  - [ ] 결과가 JSON과 Markdown으로 생성됨
- **검증**:
  - `DATABASE_URL= .venv/bin/pytest tests/test_context_pipeline_eval.py`
  - 평가 CLI 두 번 실행 결과가 동일함
  - `.venv/bin/ruff check app tests`
- **handoff**: TASK-067, 이후 모든 맥락 작업의 회귀 기준

### TASK-067 — 출처 정책 registry와 공식 소스 adapter

- **Owner**: Data/AI Implementer + PM
- **Branch**: `data-ai/TASK-067-source-registry`
- **예상 시간**: 3시간
- **의존성**: TASK-066
- **목표**: 모델이 임의로 출처 등급을 정하지 않고, 이슈 카테고리와
  `resolutionSource`에 따라 코드가 출처 정책을 선택한다.
- **수정 범위**:
  - `backend/app/core/context_source_registry.py`
  - `backend/config/context_sources.json`
  - `backend/tests/test_context_source_registry.py`
  - source-policy 문서
- **수행 내용**:
  1. 정치, 경제, 기술, 세계, 스포츠의 공식 도메인 registry를 만든다.
  2. `resolutionSource` 도메인을 시장별 최우선 출처로 합성한다.
  3. 공식 기관, 기업 공시/뉴스룸, 독립 보도 출처 유형을 구분한다.
  4. 도메인 wildcard, redirect, subdomain, canonical host 규칙을 구현한다.
  5. 출처별 날짜·제목 추출 차이를 adapter 인터페이스로 분리한다.
  6. registry에 없는 도메인은 자동으로 공식 출처가 될 수 없게 한다.
- **완료 조건**:
  - [ ] 5개 카테고리 registry와 fallback 정책 존재
  - [ ] `resolutionSource` 우선 적용 테스트 통과
  - [ ] redirect/subdomain 혼동 테스트 통과
  - [ ] registry 밖 도메인이 공식 단일 출처 경로를 통과하지 못함
  - [ ] 정책 버전이 후보와 collection run에 기록됨
  - [ ] TASK-066 평가 지표가 퇴행하지 않음
- **검증**:
  - `DATABASE_URL= .venv/bin/pytest tests/test_context_source_registry.py tests/test_context_pipeline_eval.py`
  - `.venv/bin/ruff check app tests`
- **handoff**: TASK-068, TASK-071

### TASK-068 — 주장 단위 상충 검증

- **Owner**: Data/AI Implementer
- **Branch**: `data-ai/TASK-068-context-contradiction`
- **예상 시간**: 3시간
- **의존성**: TASK-066, TASK-067
- **목표**: 기사 단위 일치만 보지 않고, 후보의 핵심 주장을 구조화해 출처별
  지지·상충 여부를 검사한다.
- **수정 범위**:
  - `backend/app/core/context_claims.py`
  - `backend/app/core/context_verification.py`
  - `context_candidates.sources` JSONB claim 구조
  - 관련 테스트와 평가 fixture
- **수행 내용**:
  1. 후보를 `subject`, `predicate`, `object`, `event_at` 주장으로 구조화한다.
  2. citation별로 `supports`, `contradicts`, `not_addressed`를 판정한다.
  3. 날짜·수량·상태 값이 다른 경우 상충으로 처리한다.
  4. 독립 출처 두 개가 서로 같은 원문을 재인용하면 하나로 계산한다.
  5. 상충이 해소되지 않은 후보는 verified가 될 수 없게 한다.
  6. 사용자용 요약에는 상충 내부 점수를 노출하지 않는다.
- **완료 조건**:
  - [ ] 동일 주장·상충 주장·무관 주장 fixture 통과
  - [ ] 날짜 또는 상태 불일치 후보 자동 공개율 0%
  - [ ] 재배포 출처가 복수 확인으로 계산되지 않음
  - [ ] 모든 verified 후보가 최소 한 개의 supported claim을 가짐
  - [ ] 근거에 없는 claim은 요약에 들어갈 수 없음
  - [ ] TASK-066 평가 기준 통과
- **검증**:
  - `DATABASE_URL= .venv/bin/pytest tests/test_context_verification.py tests/test_context_claims.py tests/test_context_pipeline_eval.py`
  - `.venv/bin/ruff check app tests`
- **handoff**: TASK-069, TASK-070

### TASK-069 — 후보 재검증과 수명 관리

- **Owner**: Backend Implementer + Data/AI Implementer
- **Branch**: `backend/TASK-069-context-revalidation`
- **예상 시간**: 2시간
- **의존성**: TASK-068
- **추가 승인 가능성**: append-only 검사 이력 테이블이 TASK-056 승인 범위를
  넘으면 새 schema 승인을 먼저 받는다.
- **목표**: 출처 링크, 내용, 날짜가 바뀌어도 오래된 후보가 계속 공개되지
  않게 한다.
- **수정 범위**:
  - `backend/migrations/003_context_candidate_checks.sql`
  - `ContextCandidateCheck` 모델
  - `backend/app/core/context_revalidation.py`
  - scheduled batch 연결
  - 관련 테스트
- **수행 내용**:
  1. 후보별 최신 URL 접근, canonical URL, content hash를 재검사한다.
  2. `expires_at` 도달, 링크 실패, 내용 변경, 출처 상충을 기록한다.
  3. 기존 후보를 덮어쓰지 않고 append-only check를 추가한다.
  4. 최신 check가 invalid/stale이면 API와 v4 리포트에서 제외한다.
  5. 공개 후보가 사라지면 해당 리포트를 재생성 대상으로 표시한다.
- **완료 조건**:
  - [ ] 기존 migration은 수정되지 않음
  - [ ] 링크 404, redirect, hash 변경, unchanged fixture 통과
  - [ ] invalid/stale 후보가 공개 API에서 제외됨
  - [ ] 후보 제거 후 리포트가 부재 상태 또는 새 근거로 갱신됨
  - [ ] 재검증 실패가 전체 정기 배치를 중단하지 않음
  - [ ] TASK-066 평가 기준 통과
- **검증**:
  - `DATABASE_URL= .venv/bin/pytest tests/test_context_revalidation.py tests/test_issues_live.py`
  - `.venv/bin/ruff check app tests`
- **handoff**: TASK-070, TASK-073

### TASK-070 — 7일·30일 과거 변화 에피소드 backfill

- **Owner**: Data/AI Implementer
- **Branch**: `data-ai/TASK-070-historical-context`
- **예상 시간**: 3시간
- **의존성**: TASK-068, TASK-069
- **목표**: 현재 한 시점뿐 아니라 주요 과거 변화 구간과 맥락 후보를
  타임라인으로 제공한다.
- **수정 범위**:
  - `backend/app/core/context_episode_detection.py`
  - `backend/app/core/historical_context_backfill.py`
  - history/context API query
  - timeline fixture와 테스트
- **수행 내용**:
  1. 7일/30일 snapshot에서 임계값 이상 변화 구간을 찾는다.
  2. 12시간 이내 인접 marker는 하나의 에피소드로 묶는다.
  3. 에피소드마다 별도 검색 구간과 candidate ID를 가진다.
  4. 같은 후보가 여러 에피소드에 중복 저장되지 않게 한다.
  5. 최신 에피소드 우선, 최대 표시 개수를 제한한다.
  6. guarded backfill과 증분 실행을 분리한다.
- **완료 조건**:
  - [ ] 7일/30일 에피소드 탐지 fixture 통과
  - [ ] 인접 marker clustering 결과가 결정적임
  - [ ] 같은 URL/사건 중복 저장 없음
  - [ ] 사용자 화면 표시 에피소드 최대 수 강제
  - [ ] backfill 재실행이 idempotent함
  - [ ] 기존 최신 에피소드 흐름이 퇴행하지 않음
- **검증**:
  - `DATABASE_URL= .venv/bin/pytest tests/test_context_episode_detection.py tests/test_historical_context_backfill.py`
  - local fixture backfill 두 번 실행
  - `.venv/bin/ruff check app tests`
- **handoff**: TASK-071, TASK-072

### TASK-071 — 다국어 공식 출처 검색

- **Owner**: Data/AI Implementer
- **Branch**: `data-ai/TASK-071-multilingual-context`
- **예상 시간**: 3시간
- **의존성**: TASK-067, TASK-070
- **목표**: 영어 기사에만 의존하지 않고 이슈 국가·기관의 원문 공식 출처를
  찾되, 번역 과정에서 새 사실을 추가하지 않는다.
- **수정 범위**:
  - `backend/app/core/context_query_languages.py`
  - `backend/app/core/context_research.py`
  - source registry의 language metadata
  - 다국어 fixture와 테스트
- **수행 내용**:
  1. 시장의 국가·기관·언어 후보를 구조화한다.
  2. 영어와 최대 한 개 현지어 질의를 생성한다.
  3. 현지어 citation을 먼저 구조화하고 이후 한국어 중립 요약을 만든다.
  4. 고유명사·날짜·숫자는 원문 citation과 다시 대조한다.
  5. 번역이 불안정하면 원문 제목과 날짜만 공개하고 요약을 생략한다.
  6. 검색 횟수 전체 상한은 유지한다.
- **완료 조건**:
  - [ ] 최소 5개 언어 fixture 지원
  - [ ] 원문 citation 없는 번역 요약은 저장되지 않음
  - [ ] 고유명사·날짜·숫자 변경이 검출됨
  - [ ] 현지어 실패 시 영어 검색으로 안전하게 축소됨
  - [ ] 시장당 검색 상한이 증가하지 않음
  - [ ] TASK-066 평가 기준 통과
- **검증**:
  - `DATABASE_URL= .venv/bin/pytest tests/test_context_query_languages.py tests/test_context_research.py tests/test_context_pipeline_eval.py`
  - `.venv/bin/ruff check app tests`
- **handoff**: TASK-072

### TASK-072 — 출처 provenance와 검증 근거 UI

- **Owner**: Frontend Implementer + Backend Implementer
- **Branch**: `frontend/TASK-072-context-provenance-ui`
- **예상 시간**: 2.5시간
- **의존성**: TASK-070, TASK-071
- **목표**: 사용자가 후보가 표시된 이유와 원문 출처를 직접 확인할 수 있게
  하되 내부 점수나 모델 판단을 권위처럼 노출하지 않는다.
- **수정 범위**:
  - API source metadata 계약 보완
  - source/provenance drawer 컴포넌트
  - 변화 에피소드 타임라인
  - 접근성·반응형 테스트
- **수행 내용**:
  1. 후보별 출처 제목, 도메인, 발행일, 수집 시각을 표시한다.
  2. 공식 단일 출처/독립 복수 출처의 검증 경로를 설명한다.
  3. 모델명, 내부 점수, 내부 reasoning은 사용자에게 노출하지 않는다.
  4. 같은 사건의 중복 출처는 접어서 표시한다.
  5. 과거 에피소드 타임라인에서 차트 marker와 출처를 연결한다.
  6. 링크 실패 후보는 UI에 남지 않게 최신 check를 따른다.
- **완료 조건**:
  - [ ] 후보 0/1/3개와 과거 에피소드 상태 정상
  - [ ] source URL과 저장된 citation URL 일치
  - [ ] 내부 점수·모델 판단 문구 미노출
  - [ ] 키보드·스크린리더로 drawer 접근 가능
  - [ ] 320px/375px/desktop overflow 없음
  - [ ] data-as-of와 해석 주의 유지
- **검증**:
  - `npm run typecheck`
  - `npm run lint`
  - `npm run build`
  - component/parser 테스트
  - Browser QA
- **handoff**: TASK-073

### TASK-073 — 검색 캐시·provider 장애 대응·관측성

- **Owner**: Backend Implementer + Data/AI Implementer
- **Branch**: `backend/TASK-073-context-reliability`
- **예상 시간**: 2.5시간
- **의존성**: TASK-069, TASK-072
- **추가 승인 가능성**: 영속 cache 테이블이 TASK-056 승인 범위를 넘으면 새
  schema 승인을 먼저 받는다.
- **목표**: 동일 검색 반복, provider 지연, 부분 실패가 데모와 정기 실행을
  흔들지 않게 한다.
- **수정 범위**:
  - 검색 cache와 TTL
  - provider circuit breaker/retry policy
  - collection run observability
  - health/status API 또는 운영 보고서
  - 장애 fixture와 테스트
- **수행 내용**:
  1. `query + time window + source-policy version`으로 검색 결과를 cache한다.
  2. timeout, rate limit, malformed annotation, 부분 검색 실패를 분리한다.
  3. provider 장애 시 기존 verified 후보와 v4 리포트를 유지한다.
  4. 연속 실패 시 해당 실행에서 추가 호출을 중단한다.
  5. 검색 횟수, token, latency, cache hit, accepted/withheld/rejected를 기록한다.
  6. 로그와 상태 응답에서 key·prompt·원문 전문을 제외한다.
- **완료 조건**:
  - [ ] 동일 질의 cache hit로 provider 호출이 생략됨
  - [ ] TTL/source-policy 변경 시 cache가 무효화됨
  - [ ] timeout/rate-limit/partial failure fixture 통과
  - [ ] provider 전체 실패에도 기존 사용자 화면 유지
  - [ ] 연속 실패 상한과 circuit open/close가 결정적임
  - [ ] 사용량·오류 통계가 비밀값 없이 남음
- **검증**:
  - Backend reliability/cache 테스트
  - scheduled batch 장애 통합 테스트
  - `.venv/bin/ruff check app tests`
  - `git diff --check`
- **handoff**: TASK-074 또는 종료

### TASK-074 — 교차 이슈 사건 graph

- **Owner**: Data/AI Implementer + Backend Implementer
- **Branch**: `data-ai/TASK-074-cross-issue-context`
- **예상 시간**: 3시간
- **의존성**: TASK-068, TASK-070, TASK-073
- **추가 승인 가능성**: 새 event cluster/link 테이블과 공개 API가 TASK-056
  승인 범위를 넘으면 별도 schema/API 승인을 받는다.
- **목표**: 같은 외부 사건을 여러 시장에서 중복 수집하지 않고, 각 이슈의
  변화 에피소드와 별도로 연결한다.
- **수정 범위**:
  - `context_event_clusters`, `context_event_market_links` migration/model
  - title/date/entity/source 기반 clustering
  - 교차 이슈 API와 UI 연결
  - clustering fixture와 테스트
- **수행 내용**:
  1. canonical URL, 사건 날짜, 핵심 엔티티, supported claims로 사건을 묶는다.
  2. 하나의 사건 cluster를 여러 market/episode에 연결한다.
  3. 연결마다 별도의 condition match와 temporal relation을 검증한다.
  4. 한 시장에서 verified인 사건이 다른 시장에서 자동 verified되지 않게 한다.
  5. 검색 cache와 공유해 중복 provider 호출을 줄인다.
  6. UI에서는 관련 이슈를 읽기 탐색용으로만 제공한다.
- **완료 조건**:
  - [ ] 동일 사건 중복 cluster 생성 방지
  - [ ] 서로 다른 날짜·주장 사건의 잘못된 병합 방지
  - [ ] 시장별 검증 상태가 독립적임
  - [ ] 교차 이슈 연결이 관계 단정으로 표현되지 않음
  - [ ] 기존 단일 이슈 episode API가 퇴행하지 않음
  - [ ] TASK-066 평가 기준과 전체 통합 테스트 통과
- **검증**:
  - clustering/link API 테스트
  - Backend full suite와 Ruff
  - Frontend full suite
  - Browser QA
- **handoff**: 별도 승인 후 배포 또는 종료

## 4. 추가 작업 전체 의존성

```text
TASK-065
  └─ TASK-066 evaluation
       └─ TASK-067 source registry
            ├─ TASK-068 contradiction checks
            │    └─ TASK-069 revalidation
            │         ├─ TASK-070 historical episodes
            │         │    ├─ TASK-071 multilingual research
            │         │    │    └─ TASK-072 provenance UI
            │         │    │         └─ TASK-073 reliability
            │         │    │              └─ TASK-074 cross-issue graph
            │         │    └─ TASK-072 provenance UI
            │         └─ TASK-073 reliability
            └─ TASK-071 multilingual research
```

## 5. Stretch 전체 완료 정의

- [ ] 자동 평가 harness가 offline replay와 CI 회귀를 제공함
- [ ] 출처 등급과 도메인 정책이 모델 판단과 분리됨
- [ ] 출처별 핵심 주장 지지·상충 상태가 검증됨
- [ ] 링크·내용 변경·만료 후보가 자동으로 공개 경로에서 빠짐
- [ ] 7일/30일 변화 에피소드가 중복 없이 생성됨
- [ ] 비영어 공식 출처가 근거 대조를 거쳐 포함됨
- [ ] 사용자가 출처·발행일·검증 경로를 직접 확인함
- [ ] 검색 cache와 provider 장애 대응이 기존 성공 데이터를 보존함
- [ ] 같은 사건을 여러 이슈가 공유하되 시장별 검증은 독립적임
- [ ] 모든 단계가 TASK-056 정책과 후속 schema/API 승인 범위 안에 있음
- [ ] 배포는 별도 승인 없이는 수행되지 않음

## 6. 관련 문서

- 핵심 20시간 계획: `reports/task-055-automated-context-execution-plan.md`
- 배경 분석: `reports/task-055-context-candidate-ai-summary-strategy.md`
- 작업 목록: `tasks/backlog.md`
