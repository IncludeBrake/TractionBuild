# Stage 1: Build the dependencies using uv
FROM python:3.12-slim AS builder
WORKDIR /app

# Install system dependencies needed for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./
COPY README.md ./

# Create a virtual environment and install dependencies
RUN uv venv && . .venv/bin/activate && uv pip install .

# Stage 2: Build the final, lean production container
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN groupadd -r zerotoship && useradd -r -g zerotoship zerotoship

WORKDIR /app

# Copy the installed dependencies from the builder
COPY --from=builder /app/.venv ./.venv

# Copy application source code
COPY src/ ./src
COPY main.py ./

# Copy configuration files
COPY config/ ./config

# Copy entrypoint script
COPY entrypoint.sh ./entrypoint.sh

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