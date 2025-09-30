# Multi-stage build for optimized production image
FROM python:3.11-slim as builder

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

RUN groupadd -r finance && useradd -r -g finance finance

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY . .

RUN chown -R finance:finance /app

USER finance

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
   CMD curl -f http://localhost:8000/health || exit 1

CMD ["gunicorn", "--config", "gunicorn_config.py", "controller:app"]
