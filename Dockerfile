# --- Stage 1: Builder ---
# This stage builds your application and its dependencies.
FROM python:3.12-slim AS builder
WORKDIR /app

# Install system dependencies needed for building some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip==23.3.2 && \
    pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY src/ ./src/


# --- Stage 2: Final Production Image ---
# This stage creates a lean final image with only what's needed to run.
FROM python:3.12-slim
RUN groupadd -r zerotoship && useradd --no-log-init -r -g zerotoship zerotoship

# Install only the necessary runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the installed Python packages from the builder stage
COPY --from=builder --chown=zerotoship:zerotoship /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
# Copy the application source code from the builder stage
COPY --from=builder --chown=zerotoship:zerotoship /app/src ./src

# Copy all other necessary application files
COPY --chown=zerotoship:zerotoship config/ ./config/
COPY --chown=zerotoship:zerotoship runs/ ./runs/
COPY --chown=zerotoship:zerotoship chat_ui.py ./
COPY --chown=zerotoship:zerotoship entrypoint.sh ./
RUN chmod +x /app/entrypoint.sh

# The PATH is now clean as packages are in the system Python path
ENV PYTHONPATH="/app/src"

USER zerotoship
EXPOSE 8000 8501
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["--help"]