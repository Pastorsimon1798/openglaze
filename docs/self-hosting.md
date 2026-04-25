# Self-Hosting Guide

OpenGlaze is currently optimized for a small-studio or personal self-hosted deployment: one Flask container, SQLite in a writable Docker volume, and local uploads in a second volume.

## Quick start

```bash
git clone https://github.com/Pastorsimon1798/openglaze.git
cd openglaze
cp .env.example .env
# Edit SECRET_KEY before exposing the app publicly
docker compose up -d
curl http://localhost:8768/health
```

Open <http://localhost:8768>.

## Supported production shape today

```text
Browser -> OpenGlaze Flask container :8768
              |-> /data/glaze.db              (openglaze_data volume)
              |-> /app/frontend/uploads       (openglaze_uploads volume)
```

This keeps setup simple and matches the current code. PostgreSQL and Ory Kratos are present as experimental services, but they are not the supported default until the data layer is migrated away from SQLite-only connections.

## Environment

Use `.env.example` as the source of truth. Minimum public deployment settings:

```bash
OPENGLAZE_MODE=personal
BASE_URL=https://openglaze.yourdomain.com
FLASK_HOST=0.0.0.0
FLASK_PORT=8768
DATABASE_PATH=/data/glaze.db
SECRET_KEY=<32+ random bytes, e.g. openssl rand -hex 32>
```

## Reverse proxy

The repo includes a minimal `nginx.conf` for the compose `prod` profile. For TLS, place certificates under `./certs` or terminate TLS with Caddy/Traefik/Cloudflare in front of the app.

```bash
docker compose --profile prod up -d
```

For Caddy, a minimal external proxy is:

```caddyfile
openglaze.yourdomain.com {
  reverse_proxy localhost:8768
}
```

## Backups

Inside a manual checkout:

```bash
DATABASE_PATH=glaze.db UPLOAD_DIR=frontend/uploads scripts/backup.sh
```

Inside Docker:

```bash
docker compose exec openglaze sh -lc 'DATABASE_PATH=/data/glaze.db UPLOAD_DIR=/app/frontend/uploads scripts/backup.sh'
```

For production, also snapshot Docker volumes:

- `openglaze_data`
- `openglaze_uploads`

## Updates

```bash
git pull
docker compose down
docker compose up -d --build
curl http://localhost:8768/health
```

## Security checklist

- [ ] Set a strong `SECRET_KEY`; do not use the example value.
- [ ] Put the app behind HTTPS before sharing outside a trusted LAN.
- [ ] Back up `openglaze_data` and `openglaze_uploads`.
- [ ] Keep Docker host patched.
- [ ] Treat simple-auth as lightweight studio identity, not enterprise SSO.

## Current limits

- PostgreSQL is not wired into application managers yet.
- Simple-auth sessions are in memory and reset on process restart.
- Multi-worker deployments need durable auth/session storage first.
- Uploads are local files; object storage/CDN is future work.
