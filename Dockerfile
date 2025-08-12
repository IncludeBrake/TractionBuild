# Stage 1: Build the dependencies using uv
FROM python:3.12-slim AS builder
WORKDIR /app

# Install system dependencies needed for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc=4:12.2.0-3 \
    g++=4:12.2.0-3 \
    && rm -rf /var/lib/apt/lists/*

# Install uv with pinned version
RUN pip install --no-cache-dir uv==0.8.8

# Copy dependency files first for better layer caching
COPY requirements-docker.txt ./
COPY pyproject.toml ./
COPY README.md ./

# Create virtual environment
RUN uv venv

# Install core dependencies first (most cacheable layer) with BuildKit cache
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/root/.cache/pip \
    . .venv/bin/activate && \
    UV_CACHE_DIR=/root/.cache/uv \
    UV_CONCURRENT_DOWNLOADS=8 \
    UV_INDEX_STRATEGY=unsafe-best-match \
    uv pip install -r requirements-docker.txt

# Copy source and install package (changes more frequently)
COPY src/ ./src/
COPY main.py ./
COPY entrypoint.sh ./
RUN --mount=type=cache,target=/root/.cache/uv \
    . .venv/bin/activate && \
    UV_CACHE_DIR=/root/.cache/uv \
    UV_CONCURRENT_DOWNLOADS=8 \
    uv pip install --no-deps -e . && \
    python -m compileall /app/.venv/lib/python3.12/site-packages/ -q && \
    find /app/.venv -name "*.pyc" -delete && \
    find /app/.venv -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Stage 2: Build the final, lean production container
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl=7.88.1-10+deb12u12 \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN groupadd -r zerotoship && useradd -r -g zerotoship zerotoship

WORKDIR /app

# Copy the installed dependencies from the builder
COPY --from=builder /app/.venv ./.venv

# Copy application source code from builder
COPY --from=builder /app/src ./src
COPY --from=builder /app/main.py ./
COPY --from=builder /app/entrypoint.sh ./

# Copy configuration files
COPY config/ ./config

# Create necessary directories and set permissions
RUN mkdir -p /app/data /app/output /app/logs && \
    chown -R zerotoship:zerotoship /app && \
    chmod +x /app/entrypoint.sh

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"
ENV NEO4J_PASSWORD="test_password"
ENV NEO4J_URI="neo4j://host.docker.internal:7687"
ENV PROMETHEUS_PORT="8000"
ENV MEMORY_FILE_PATH="/app/output/project_memory.json"
ENV CREWAI_MEMORY_PATH="/app/output/crewai_memory"
ENV HOME="/app"

# Switch to non-root user
USER zerotoship

# Expose port for Prometheus metrics
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/metrics || exit 1

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# The command to run when the container starts
CMD ["python", "main.py", "--idea", "Default Production Idea", "--workflow", "validation_and_launch"]

# Alternative: Run as a web server for Kubernetes
# CMD ["uvicorn", "src.zerotoship.api.app:app", "--host", "0.0.0.0", "--port", "8000"]