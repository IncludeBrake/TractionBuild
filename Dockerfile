# Stage 1: Build the dependencies using uv
FROM python:3.12-slim AS builder
WORKDIR /app

# Install system dependencies needed for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc=4:14.2.0-1 \
    g++=4:14.2.0-1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files first for better caching
COPY pyproject.toml ./
COPY README.md ./

# Create a virtual environment and install dependencies
# Use --no-deps to avoid duplicate installs and speed up builds
RUN uv venv && . .venv/bin/activate && uv pip install --no-cache-dir .

# Stage 2: Build the final, lean production container
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl=8.14.1-2 \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN groupadd -r zerotoship && useradd -r -g zerotoship zerotoship

WORKDIR /app

# Copy the installed dependencies from the builder
COPY --from=builder /app/.venv ./.venv

# Copy application source code
COPY src/ ./src/
COPY main.py chat_ui.py ./

# Copy the configuration directory. The config_generator ensures this always exists.
COPY --chown=zerotoship:zerotoship config/ ./config/
# Copy entrypoint script
COPY entrypoint.sh ./entrypoint.sh

# Create necessary directories and set permissions
RUN mkdir -p /app/data /app/output /app/logs && \
    chown -R zerotoship:zerotoship /app && \
    chmod +x /app/entrypoint.sh

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"
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