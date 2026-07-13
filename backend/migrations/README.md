# 데이터베이스 마이그레이션

이 프로젝트는 별도 마이그레이션 프레임워크 대신 검토 가능한 일반 SQL 파일을
사용합니다. 기존 마이그레이션은 수정하지 않고 새 번호의 파일만 추가합니다. 새
의존성 도입이나 스키마 변경, 다른 데이터베이스에 대한 적용은 `AGENTS.md`에 따른
사전 승인이 필요합니다.

## 파일 목록

| 파일                                    | 역할                                                                                 |
| --------------------------------------- | ------------------------------------------------------------------------------------ |
| `001_initial_schema.sql`                | 이슈, 결과 항목, 스냅샷, 지표, 변화 감지, 보고서, 관련 자료, 수집 로그의 초기 스키마 |
| `002_context_candidates.sql`            | 검증 대상 맥락 자료와 수집 실행 기록                                                 |
| `003_market_resolution_rules.sql`       | 출처를 보존하는 이슈 판정 기준 근거                                                  |
| `004_ai_report_generation_requests.sql` | 온디맨드 브리핑 요청, 상태 이벤트, 임대와 캐시 식별자                                |
| `005_ai_report_generation_blocks.sql`   | v8 검증 완료 브리핑 블록                                                             |
| `006_scenario_conversations.sql`        | 24시간 만료 시나리오 세션, 대화 차례, 전제, 요청·이벤트·응답 블록                    |

001~006은 명시적으로 승인된 현재 로컬·개발 데이터베이스에만 적용되어 있습니다.
공유·운영 환경이나 다른 데이터베이스에는 별도의 환경별 승인 없이 적용하면 안
됩니다. 시나리오 세션 그래프는 유효 기간 중 추가 전용이며, 만료 뒤 또는 소유자의
인증된 삭제 요청이 있을 때 해당 임시 그래프만 완전 삭제할 수 있습니다.

## 적용 방법

대상 데이터베이스와 실행 자체를 승인받은 경우, 저장소의 `backend` 디렉터리에서
번호 순서대로 실행합니다.

```bash
psql "$DATABASE_URL" -f migrations/001_initial_schema.sql
psql "$DATABASE_URL" -f migrations/002_context_candidates.sql
psql "$DATABASE_URL" -f migrations/003_market_resolution_rules.sql
psql "$DATABASE_URL" -f migrations/004_ai_report_generation_requests.sql
psql "$DATABASE_URL" -f migrations/005_ai_report_generation_blocks.sql
psql "$DATABASE_URL" -f migrations/006_scenario_conversations.sql
```

`psql`은 `postgresql://...` 형식의 일반 PostgreSQL URL을 사용합니다. 애플리케이션
설정이 `postgresql+psycopg://...` 형식이라면 실제 값을 출력하지 말고 스킴만
`postgresql://...`로 바꿔 별도 셸 변수에 넣은 뒤 실행합니다.
