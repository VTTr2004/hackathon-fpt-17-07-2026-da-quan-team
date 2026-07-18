FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=180 PIP_RETRIES=10
WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y libexpat1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY app ./app
COPY scripts ./scripts
# Retry/timeout make the install resilient to slow PyPI reads. [osm] adds osmium (Linux build ok).
RUN pip install --no-cache-dir --retries 10 --timeout 180 ".[osm]"

EXPOSE 10000
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

