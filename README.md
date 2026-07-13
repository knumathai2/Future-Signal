# Outlook AI Signals

Outlook AI Signals는 Polymarket의 공개 집계 데이터를 이용해 주요 이슈에 반영된
기대값의 변화를 보여 주는 모니터링 대시보드입니다. 모든 데이터 화면에 기준
시각과 해석 주의사항을 함께 표시하며, 미래 결과를 단정하거나 근거 없이 변화의
배경을 설명하지 않습니다.

## 저장소 구성

- `frontend/`: React 18, Vite, TypeScript, Tailwind CSS, Recharts 기반 웹 화면
- `backend/`: FastAPI API, PostgreSQL 연동, 시장 데이터 수집, 근거 기반 v8 브리핑
  및 시나리오 작업자
- `deploy/`: Docker Compose와 Caddy 운영 설정
- `docs/`: 제품 요구사항과 서비스·기술·UX 설계
- `memory/`: 최종 프로젝트 상태, 아키텍처, 결정 원장과 용어 정책
- `tasks/completed.md`: 완료된 개발 작업의 간결한 감사 원장

## 로컬 개발

백엔드는 Python 3.11을 사용합니다.

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload
```

두 번째 터미널에서 프런트엔드를 실행합니다.

```bash
cd frontend
npm install
npm run dev
```

브라우저에서 `http://127.0.0.1:5173`을 엽니다. Vite 개발 서버는 `/api` 요청을
`http://localhost:8000`의 백엔드로 전달합니다. 데이터베이스가 설정되지 않았거나
조회할 수 없으면 기준 시각과 주의 문구가 포함된 정적 예시 데이터가 표시됩니다.

환경 변수와 데이터베이스 연결 방법은 [백엔드 안내](backend/README.md), 별도 API
주소 설정은 [프런트엔드 안내](frontend/README.md)를 참고하세요.

운영 구성과 확인 방법은 [배포 안내](deploy/README.md)를 참고하세요. 저장소에 포함된
운영 Compose 프로필은 브리핑 작업자와 시나리오 기능을 활성화합니다.

## 검증

```bash
(cd backend && ./.venv/bin/ruff check . && ./.venv/bin/pytest)
(cd frontend && npm run typecheck && npm run lint && npm run test:api-url && npm run test:report-parser && npm run test:scenario-parser && npm run build)
```

## 기준 문서

- [프로젝트 운영 규칙](AGENTS.md)
- [제품 요구사항](docs/prd/README.md)
- [서비스 설계](docs/service-design/README.md)
- [기술 설계](docs/tech-design/README.md)
- [UX 설계](docs/ux-design/README.md)
- [현재 프로젝트 상태](memory/project.md)
- [현재 아키텍처](memory/architecture.md)
- [공개 API 계약](backend/API_CONTRACT.md)

데이터베이스 스키마, 외부 의존성, 인프라, 배포, 운영 데이터 쓰기, 문구 정책을
변경하려면 `AGENTS.md`에 정의된 승인을 먼저 받아야 합니다.
