FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1     PYTHONDONTWRITEBYTECODE=1     PYTHONPATH=/app/src

RUN apt-get update   && apt-get install -y --no-install-recommends gcc libpq-dev   && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml /app/
COPY src /app/src
RUN pip install --no-cache-dir --upgrade pip   && pip install --no-cache-dir .

COPY . /app

RUN chmod +x /app/docker/web/entrypoint.sh
