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
Value: REDACTED_DEPLOY_IP
Proxy: DNS only (recommended for initial certificate issuance)
TTL: Auto
```

No application secret is required for the timestamped sample-data mode.

## Optional live-data value

Copy `.env.example` to `.env` and set `DATABASE_URL` plus an approved
OpenAI-compatible provider key when the target PostgreSQL database with
migrations 001-006 is ready. Production Compose enables the scenario feature
and starts the guarded on-demand workers; keep the provider key only in the
untracked `.env` file.

## Commands

```bash
docker compose -f deploy/compose.yml up -d --build
curl -fsS http://127.0.0.1:8600/api/health
```

When an approved live database is ready, create `deploy/.env` from the example
and add `--env-file deploy/.env` to the Compose command.

The Caddy site block is recorded in `deploy/osignal.gilgop.cloud.caddy`.
