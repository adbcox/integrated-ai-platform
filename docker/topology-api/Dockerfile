FROM python:3.12-alpine
RUN pip install --no-cache-dir pyyaml==6.0.1 \
    && adduser -D -u 1000 svc
USER svc
WORKDIR /app
COPY server.py /app/server.py
EXPOSE 8300
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- http://localhost:8300/health || exit 1
ENTRYPOINT ["python", "/app/server.py"]
