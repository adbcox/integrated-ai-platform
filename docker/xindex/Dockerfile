FROM python:3.12-slim

RUN groupadd --system --gid 1000 svc \
 && useradd  --system --uid 1000 --gid 1000 --create-home --home-dir /home/svc svc \
 && mkdir -p /data \
 && chown svc:svc /data

WORKDIR /app

COPY app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app

USER svc

ENV XINDEX_DB=/data/xindex.db \
    XINDEX_DOCS_ROOT=/docs \
    PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=15s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3).status==200 else 1)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
