# VPS deployment

The production baseline runs the Backend and built Frontend in an isolated
Docker Compose network. Only the Frontend gateway is published on the host at
`127.0.0.1:8600`; the host Caddy instance terminates TLS for
`osignal.gilgop.cloud`.

## Required external value

Create this DNS record before expecting HTTPS to become available:

```text
Type: A
Name: osignal
Value: 61.77.100.69
Proxy: DNS only (recommended for initial certificate issuance)
TTL: Auto
```

No application secret is required for the timestamped sample-data mode.

## Optional live-data value

Copy `.env.example` to `.env` and set `DATABASE_URL` only when an approved
PostgreSQL database with migrations 001-005 is ready. Do not enable the
scenario feature in production. AI provider keys are intentionally excluded:
the production API does not start the approved local/development-only workers.

## Commands

```bash
docker compose -f deploy/compose.yml up -d --build
curl -fsS http://127.0.0.1:8600/api/health
```

When an approved live database is ready, create `deploy/.env` from the example
and add `--env-file deploy/.env` to the Compose command.

The Caddy site block is recorded in `deploy/osignal.gilgop.cloud.caddy`.
