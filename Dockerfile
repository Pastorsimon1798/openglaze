# OpenGlaze Dockerfile
# Single-user self-host image. Uses writable SQLite storage by default.

# =============================================================================
# BUILDER STAGE
# =============================================================================
FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# =============================================================================
# PRODUCTION STAGE
# =============================================================================
FROM python:3.11-slim as production

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    OPENGLAZE_MODE=personal \
    FLASK_HOST=0.0.0.0 \
    FLASK_PORT=8768 \
    DATABASE_PATH=/data/glaze.db \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --shell /bin/bash openglaze && \
    mkdir -p /data /app/frontend/uploads && \
    chown -R openglaze:openglaze /data /app

COPY --chown=openglaze:openglaze . .

USER openglaze

EXPOSE 8768
VOLUME ["/data", "/app/frontend/uploads"]

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8768/health || exit 1

CMD ["python", "server.py"]

# =============================================================================
# DEVELOPMENT STAGE
# =============================================================================
FROM production as development

USER root
RUN pip install --no-cache-dir watchfiles debugpy
USER openglaze

CMD ["watchfiles", "python server.py"]

# Default target for `docker build .`
FROM production as final
