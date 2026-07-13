# 프런트엔드 — Outlook Signals

React 18, Vite, TypeScript, Tailwind CSS, Recharts로 구성된 웹 애플리케이션입니다.

## 설치

```bash
cd frontend
npm install
```

## 실행

```bash
npm run dev
```

브라우저에서 `http://127.0.0.1:5173`을 엽니다. 개발 서버는 `/api` 요청을
`http://localhost:8000`으로 전달합니다.

로컬 프록시를 사용할 때는 `VITE_API_BASE_URL`을 비워 둡니다. 백엔드를 별도
호스트에서 제공할 때는 `https://api.example.com`처럼 승인된 HTTP(S) 절대
출처를 지정할 수 있습니다. REST와 SSE 요청은 같은 출처를 사용합니다. 이 경우
백엔드 CORS 정책에도 배포된 프런트엔드 출처를 별도로 허용해야 합니다.

시나리오 대화 화면은 프런트엔드에 포함되어 있지만, 실제 세션 생성과 응답 처리는
백엔드의 `SCENARIO_CONVERSATION_ENABLED` 설정과 작업자 실행 조건을 따릅니다.

## 명령어

```bash
npm run typecheck
npm run lint
npm run test:api-url
npm run test:report-parser
npm run test:scenario-parser
npm run build
npm run format
npm run preview
```

`npm run format`은 소스 파일을 수정합니다. 나머지 검증 명령은 의도적으로 소스
파일을 변경하지 않습니다. 배포와 CORS 변경에는 프로젝트 운영 규칙에 따른 별도
승인이 필요합니다.
