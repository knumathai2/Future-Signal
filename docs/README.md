<!--
목적: 제품 기준 문서의 진입점
소유자: PM
갱신 시점: 기준 문서의 분할, 이름 또는 위치가 바뀔 때
Harness 버전: 1.1
-->

# Outlook AI Signals 제품 기준 문서

제품 기준 문서는 주제와 절 범위에 따라 `docs/` 아래에 나뉘어 있습니다.

## 기준 문서 진입점

- [PRD](prd/README.md): 제품 요구사항, MVP 범위, 5일 일정, 발표 전략과 문구
- [서비스 설계](service-design/README.md): 데이터 수집, 지표, AI 입출력, 변화 감지,
  참여자 분석 정책
- [기술 설계](tech-design/README.md): 기술 스택, 아키텍처, DB 스키마, API 계약,
  배치 파이프라인과 AI 설계
- [UX 설계](ux-design/README.md): 화면 흐름, 문구 정책, 안전 장치, 고지 방식과 제한
  기능 정책

## 문서 우선순위

`AGENTS.md`, `standards.md`, `dependencies.md`, `memory/project.md`,
`memory/architecture.md`는 유지보수와 현재 구현 상태를 정합니다. 위 네 문서 묶음은
제품의 요구사항과 설계를 정합니다. 내용이 충돌하면 실행 가능한 코드와 공개 API
계약을 확인하고 관련 기준 문서를 함께 갱신합니다. 과거 개발 결정과 완료 이력은
`memory/decisions.md`와 `tasks/completed.md`에만 보관합니다.
