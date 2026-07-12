# Frontend — Outlook Signals

React + Vite + TypeScript + Tailwind CSS + Recharts.

## Setup

```bash
cd frontend
npm install
```

## Run

```bash
npm run dev
```

Open `http://127.0.0.1:5173`. The development server proxies `/api` to the
Backend at `http://localhost:8000`.

Leave `VITE_API_BASE_URL` empty for this local proxy flow. For a separately
hosted Backend, the Frontend accepts an approved absolute HTTP(S) origin such
as `https://api.example.com`; REST and SSE requests use that same origin. The
Backend must separately allow the deployed Frontend origin through its CORS
policy before split-origin hosting can work. That environment and CORS change
is infrastructure work and is not applied by the Frontend setup.

## Commands

```bash
npm run typecheck
npm run lint
npm run test:api-url
npm run test:report-parser
npm run build
npm run format
npm run preview
```

`npm run format` writes formatting changes; the other verification commands do
not intentionally modify source files. Deployment requires separate approval
under the project constitution.
