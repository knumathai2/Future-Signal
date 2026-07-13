# 기술 설계

기술 스택, 아키텍처, 데이터베이스 스키마, API 계약, 배치 파이프라인, AI 설계와
운영 보안을 절 단위로 나눈 기준 문서입니다.

## 절 구성

| 절         | 파일                                                                            |
| ---------- | ------------------------------------------------------------------------------- |
| 1~3        | [기술 요약, 기술 스택, 아키텍처 개요](01-architecture-stack-overview.md)        |
| 4          | [데이터베이스 스키마](02-database-schema.md)                                    |
| 5~6        | [API 구조와 배치 수집](03-api-and-batch-pipeline.md)                            |
| 7~10       | [지표, 변화 감지, AI 보고서 아키텍처](04-metrics-signals-ai-architecture.md)    |
| 11, 15, 17 | [보안, 운영 위험, 유지보수 규칙](05-security-tasks-implementation-risk-next.md) |

## 교차 참조

다른 문서의 `Technical Design §N` 표기는 위 표에서 해당 절이 포함된 파일을 찾아
확인합니다.
