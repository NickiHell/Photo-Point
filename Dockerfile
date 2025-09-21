# Use Python 3.13 slim image to match our environment
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy requirements first for better layer caching
COPY requirements.txt pyproject.toml ./

# Install Python dependencies with uv
RUN uv pip install --system --no-cache -r requirements.txt

# Copy the application code
COPY app/ ./app/
COPY src/ ./src/

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Default command - use the API main module directly
CMD ["python", "-m", "uvicorn", "app.presentation.api.main:app", "--host", "0.0.0.0", "--port", "8000"]