# --- Stage 1: Builder ---
FROM python:3.12-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv
COPY pyproject.toml ./
COPY requirements.txt ./
COPY src/ ./src/
RUN uv venv && . .venv/bin/activate && uv pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Final Production Image ---
FROM python:3.12-slim
RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser
WORKDIR /app

# Copy the pre-built virtual environment
COPY --from=builder --chown=appuser:appuser /app/.venv ./.venv

# Set the PATH to include the virtual environment's bin directory
ENV PATH="/app/.venv/bin:$PATH"

# Copy application files
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser config/ ./config/
COPY --chown=appuser:appuser main.py ./
COPY --chown=appuser:appuser entrypoint.sh ./
RUN chmod +x /app/entrypoint.sh

USER appuser
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["--help"]