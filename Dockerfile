FROM python:3.13-slim

WORKDIR /app

# Install system dependencies including debugger support
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependencies specification
COPY pyproject.toml uv.lock README.md ./

# Install Python dependencies including dev dependencies
RUN uv export --dev > requirements-all.txt && \
    uv pip install --system --no-cache -r requirements-all.txt

# Copy application code
COPY app/ ./app/
COPY src/ ./src/
COPY tests/ ./tests/

# Expose ports
EXPOSE 8000 5678

# Run with reload by default
CMD ["python", "-m", "uvicorn", "app.presentation.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]