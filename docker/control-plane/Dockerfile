FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends wget restic ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Build context is the repo root (compose: context: ../..) so the
# Dockerfile can COPY scripts/cmdb_source.py alongside the control-plane
# app code. Block 4.C C5.2c — registry module reads CMDB via the shared
# loader so it can dispatch on $CMDB_SOURCE.
COPY docker/control-plane/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY docker/control-plane/app /app/app
COPY scripts/cmdb_source.py /app/cmdb_source.py

# Bundle htmx so the runtime image has no external CDN dependency.
RUN wget -qO /app/app/static/htmx.min.js \
    https://unpkg.com/htmx.org@2.0.4/dist/htmx.min.js \
 && test -s /app/app/static/htmx.min.js

EXPOSE 8086

# Entrypoint wrapper is supplied via compose so the canonical sidecar
# pattern can source /vault/secrets/credentials.env. The image-default
# CMD below is a no-credential fallback for image testing only.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8086"]
