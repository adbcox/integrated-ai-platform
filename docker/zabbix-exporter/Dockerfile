FROM python:3.12-alpine
WORKDIR /app
COPY exporter.py .
USER nobody
ENTRYPOINT ["python3", "exporter.py"]
