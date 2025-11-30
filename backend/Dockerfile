# Multi-stage Dockerfile for DF HealthBench Backend
# Stage 1: Builder - Install dependencies with Poetry
# Stage 2: Runtime - Copy venv and run application

# ============================================================================
# Stage 1: Builder
# ============================================================================
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=2.1.3
ENV POETRY_HOME=/opt/poetry
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_IN_PROJECT=1
ENV POETRY_VIRTUALENVS_CREATE=1
ENV PATH="$POETRY_HOME/bin:$PATH"

RUN curl -sSL https://install.python-poetry.org | python3 -

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (excluding dev dependencies)
# Using --only main to install only production dependencies
RUN poetry install --only main --no-root --no-directory

# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY ./app ./app
COPY ./pyproject.toml ./poetry.lock ./

# Create non-root user for security
RUN useradd -m -u 1000 dfuser && \
    chown -R dfuser:dfuser /app

# Switch to non-root user
USER dfuser

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application with uvicorn
# Using 4 workers for production
# Binding to 0.0.0.0 to accept connections from outside container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

