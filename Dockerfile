# =====================================================
# CIH Veille IA — Backend API (Multi-Stage Production)
# =====================================================
FROM python:3.10-slim AS base

WORKDIR /app

# System dependencies for FAISS, torch, and Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libopenblas-dev \
    libomp-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy French model
RUN python -m spacy download fr_core_news_md || python -m spacy download fr_core_news_sm

# Install Playwright browsers for scraping
RUN playwright install --with-deps chromium

# --- Production Stage ---
FROM base AS production

WORKDIR /app

# Create non-root user for security
RUN groupadd -r veille && useradd -r -g veille -d /app -s /sbin/nologin veille

COPY . .

# Ensure directories exist and set permissions
RUN mkdir -p /app/vector_store /app/logs \
    && chown -R veille:veille /app

USER veille

# Environment defaults (overridden by .env / compose)
ENV PYTHONUNBUFFERED=1
ENV ENV=production

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Gunicorn for production (better process management than uvicorn alone)
CMD ["python", "-m", "uvicorn", "app.backend.api:app", \
    "--host", "0.0.0.0", "--port", "8000", \
    "--workers", "2", "--limit-concurrency", "100"]
