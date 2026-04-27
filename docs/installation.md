# Installation Guide

OpenGlaze currently has one supported launch path: **single-user self-hosting with SQLite**. PostgreSQL/Ory services remain in the compose file under an experimental profile, but the application data layer is SQLite-backed today.

## Docker installation

Requirements:

- Docker 24+ with Compose v2
- 1 GB RAM minimum
- 10 GB disk

```bash
git clone https://github.com/Pastorsimon1798/openglaze.git
cd openglaze
cp .env.example .env

# Important before public use: set SECRET_KEY in .env
# openssl rand -hex 32

docker compose up -d
curl http://localhost:8768/health
```

Open <http://localhost:8768>.

### Persistent data

The default compose stack stores data in Docker volumes:

- `openglaze_data` mounted at `/data` for SQLite (`/data/glaze.db`)
- `openglaze_uploads` mounted at `/app/frontend/uploads` for uploaded images

Back up with:

```bash
docker compose exec openglaze sh -lc 'DATABASE_PATH=/data/glaze.db UPLOAD_DIR=/app/frontend/uploads scripts/backup.sh'
```

Or stop the stack and back up the named volumes with your normal Docker volume backup tooling.

## Manual local installation

Requirements:

- Python 3.11+

```bash
git clone https://github.com/Pastorsimon1798/openglaze.git
cd openglaze
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export OPENGLAZE_MODE=personal
export DATABASE_PATH=glaze.db
export SECRET_KEY=$(openssl rand -hex 32)
python server.py
```

Open <http://localhost:8767> unless you set `FLASK_PORT`.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `OPENGLAZE_MODE` | `personal` | Supported launch mode today |
| `DATABASE_PATH` | `glaze.db` locally, `/data/glaze.db` in Docker | SQLite database file |
| `FLASK_HOST` | `127.0.0.1` locally, `0.0.0.0` in Docker | Bind host |
| `FLASK_PORT` | `8767` locally, `8768` in Docker | Bind port |
| `BASE_URL` | `http://localhost:8768` in Docker | Public URL for links/docs |
| `SECRET_KEY` | generated per process if omitted | Set this for persistent sessions |
| `RATELIMIT_PER_MINUTE` | `60` | In-memory request rate limit |

## Experimental cloud profile

The compose file includes `postgres`, `kratos`, and `mailhog` under the `cloud` profile for future work:

```bash
docker compose --profile cloud up -d
```

This is **not** the supported launch path yet because application managers still use SQLite connections.

## Troubleshooting

```bash
docker compose ps
docker compose logs openglaze
curl -i http://localhost:8768/health
```

If Docker starts but data does not persist, verify that the `openglaze_data` volume exists and that `DATABASE_PATH=/data/glaze.db` is present in the app environment.
