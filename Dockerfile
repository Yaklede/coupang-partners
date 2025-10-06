FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Seoul

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates tzdata && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Only copy dependency file first to leverage Docker layer caching
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy source
COPY coupang_partners ./coupang_partners
COPY config.example.yaml README.md AGENTS.md .env.example ./
COPY docs ./docs

# Non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["python", "-m", "coupang_partners.cli"]
CMD ["--help"]

