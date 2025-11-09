# Multi-stage Dockerfile for CloudOps Central Backend

# ============================================
# Stage 1: Base Python image with dependencies
# ============================================
FROM python:3.14-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ============================================
# Stage 2: Development image
# ============================================
FROM base as development

# Install development dependencies
RUN pip install \
    debugpy==1.8.0 \
    watchdog==3.0.0

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose ports
EXPOSE 8000
EXPOSE 5678

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ============================================
# Stage 3: Production image
# ============================================
FROM base as production

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Create directory for static files if needed
RUN mkdir -p /app/static && \
    chown -R appuser:appuser /app/static

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use gunicorn for production
CMD ["gunicorn", "main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]

# ============================================
# Stage 4: Celery Worker
# ============================================
FROM base as celery-worker

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check (check if celery worker is responding)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD celery -A app.core.celery inspect ping -d celery@$HOSTNAME || exit 1

# Default command for celery worker
CMD ["celery", "-A", "app.core.celery", "worker", "--loglevel=info", "--concurrency=4"]

# ============================================
# Stage 5: Celery Beat (Scheduler)
# ============================================
FROM base as celery-beat

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Create directory for celery beat schedule file
RUN mkdir -p /app/celerybeat-schedule && \
    chown -R appuser:appuser /app/celerybeat-schedule

# Default command for celery beat
CMD ["celery", "-A", "app.core.celery", "beat", "--loglevel=info", "--schedule=/app/celerybeat-schedule/schedule.db"]
