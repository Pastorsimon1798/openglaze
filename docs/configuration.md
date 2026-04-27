# Configuration Guide

## Supported mode

`OPENGLAZE_MODE=personal` is the supported launch mode today. It uses SQLite and local file uploads.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `OPENGLAZE_MODE` | `personal` | Runtime mode. `cloud` is experimental. |
| `BASE_URL` | `http://localhost:8768` in Docker | Public URL of your instance. |
| `DATABASE_PATH` | `glaze.db` or `/data/glaze.db` in Docker | SQLite database path. |
| `SECRET_KEY` | generated if missing | Required for stable sessions; set explicitly in production. |
| `FLASK_HOST` | `127.0.0.1` locally, `0.0.0.0` in Docker | Bind address. |
| `FLASK_PORT` | `8767` locally, `8768` in Docker | Bind port. |
| `RATELIMIT_PER_MINUTE` | `60` | In-memory per-IP rate limit. |
| `OLLAMA_API` | `http://localhost:11434/api/chat` | Optional local AI endpoint. |
| `OLLAMA_MODEL` | `kimi-k2.5:cloud` | Optional local AI model name. |

## Health checks

```bash
curl http://localhost:8768/health
curl http://localhost:8768/api/health
```

There are no separate `/health/db` or `/health/ai` endpoints in the current app.

## Docker volumes

Default compose uses:

- `openglaze_data:/data`
- `openglaze_uploads:/app/frontend/uploads`

## Experimental cloud variables

`POSTGRES_PASSWORD`, `KRATOS_PUBLIC_URL`, `KRATOS_ADMIN_URL`, and `KRATOS_HOOK_KEY` are retained for the experimental cloud profile. They are not required for the supported default Docker launch.
