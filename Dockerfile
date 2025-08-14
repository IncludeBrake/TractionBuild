# --- Stage 1: Builder ---
# This stage installs dependencies and builds the Python virtual environment.
FROM python:3.12-slim AS builder
WORKDIR /app

# Install system dependencies needed for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
<<<<<<< Updated upstream
    gcc=4:12.2.0-3 \
    g++=4:12.2.0-3 \
    && rm -rf /var/lib/apt/lists/*

# Install uv with pinned version
RUN pip install --no-cache-dir uv==0.8.8

# Copy dependency files first for better layer caching
COPY requirements-docker.txt ./
=======
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install uv, our Python package manager
RUN pip install --no-cache-dir uv

# Copy dependency files first to leverage Docker's layer caching
>>>>>>> Stashed changes
COPY pyproject.toml ./

<<<<<<< Updated upstream
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
=======
# Create a virtual environment and install all dependencies from pyproject.toml
RUN uv venv && . .venv/bin/activate && uv pip install --no-cache-dir .
>>>>>>> Stashed changes

# --- Stage 2: Final Production Image ---
# This stage creates the final, lean image for production.
FROM python:3.12-slim

# Install only the necessary runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
<<<<<<< Updated upstream
    curl=7.88.1-10+deb12u12 \
=======
    curl \
>>>>>>> Stashed changes
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and group for better security
RUN groupadd -r zerotoship && useradd --no-log-init -r -g zerotoship zerotoship

WORKDIR /app

# Copy the pre-built virtual environment from the builder stage
COPY --from=builder --chown=zerotoship:zerotoship /app/.venv ./.venv

<<<<<<< Updated upstream
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
=======
# Copy all other necessary application files
COPY --chown=zerotoship:zerotoship src/ ./src/
COPY --chown=zerotoship:zerotoship config/ ./config/
COPY --chown=zerotoship:zerotoship runs/ ./runs/
COPY --chown=zerotoship:zerotoship chat_ui.py ./
COPY --chown=zerotoship:zerotoship entrypoint.sh ./
RUN chmod +x /app/entrypoint.sh
>>>>>>> Stashed changes

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"
<<<<<<< Updated upstream
ENV NEO4J_PASSWORD="test_password"
ENV NEO4J_URI="neo4j://host.docker.internal:7687"
ENV PROMETHEUS_PORT="8000"
ENV MEMORY_FILE_PATH="/app/output/project_memory.json"
ENV CREWAI_MEMORY_PATH="/app/output/crewai_memory"
ENV HOME="/app"
=======
# Note: Sensitive variables like passwords should be injected at runtime, not set here.
>>>>>>> Stashed changes

# Switch to the non-root user
USER zerotoship

# Expose the ports the services will run on
EXPOSE 8000
EXPOSE 8501

# The entrypoint script will run first
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command if none is provided in docker-compose.yml.
# This will be overridden by the 'command:' in your compose file.
CMD ["--help"]