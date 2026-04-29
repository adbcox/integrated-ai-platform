FROM python:3.12-alpine
RUN pip install --no-cache-dir pyyaml==6.0.1 \
    && adduser -D -u 1000 svc
USER svc
WORKDIR /app
# Build context is the repo root (compose: context: ../..) so paths
# below are repo-root-relative. Block 4.C C5.2b — needed so the
# Dockerfile can also pull in scripts/cmdb_source.py.
COPY docker/topology-api/server.py /app/server.py
COPY scripts/cmdb_source.py /app/cmdb_source.py
EXPOSE 8300
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- http://localhost:8300/health || exit 1
ENTRYPOINT ["python", "/app/server.py"]
