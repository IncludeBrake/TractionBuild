#!/usr/bin/env python3
import os
import sys
import json
import re
import argparse
from pathlib import Path

def write_file(filepath, content, force=False):
    """Writes content to a file, creating directories and optionally overwriting."""
    path = Path(filepath)
    # Ensure the parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check for existing file and force flag
    if path.exists() and not force:
        print(f"⏩ {filepath} already exists. Skipping. (Use --force to overwrite)")
        return
    
    if path.exists() and force:
        print(f"⚠️ Overwriting {filepath}...")
    
    with open(filepath, "w") as f:
        f.write(content.strip())
    print(f"✅ Wrote {filepath}")

def detect_project_type():
    """Detect the type of project based on files present."""
    files = [f.name for f in Path(".").iterdir() if f.is_file()]
    
    if "pyproject.toml" in files or "requirements.txt" in files:
        return "python"
    elif "package.json" in files:
        return "node"
    elif "go.mod" in files:
        return "go"
    elif "Cargo.toml" in files:
        return "rust"
    else:
        return "unknown"

def detect_port():
    """Detect the default port based on project type."""
    project_type = detect_project_type()
    
    if project_type == "python":
        # Check for common Python web frameworks
        try:
            with open("requirements.txt", "r") as f:
                requirements = f.read().lower()
                if "fastapi" in requirements or "uvicorn" in requirements:
                    return 8000
                elif "flask" in requirements:
                    return 5000
                elif "django" in requirements:
                    return 8000
                elif "streamlit" in requirements:
                    return 8501
        except FileNotFoundError:
            pass
        return 8000
    elif project_type == "node":
        return 3000
    elif project_type == "go":
        return 8080
    else:
        return 8000

def generate_dockerfile(project_type, port):
    """Generate Dockerfile content based on project type."""
    if project_type == "python":
        return f"""# --- Stage 1: Builder ---
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
EXPOSE {port}
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["--help"]"""
    
    elif project_type == "node":
        return f"""# --- Stage 1: Builder ---
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# --- Stage 2: Final Production Image ---
FROM node:18-alpine
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001
WORKDIR /app

# Copy built application
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules
COPY --chown=nodejs:nodejs . .

USER nodejs
EXPOSE {port}
CMD ["npm", "start"]"""
    
    else:
        return f"""# Generic Dockerfile
FROM ubuntu:22.04
WORKDIR /app
COPY . .
EXPOSE {port}
CMD ["echo", "Please customize this Dockerfile for your application"]"""

def generate_docker_compose(project_type, port):
    """Generate docker-compose.yml content."""
    if project_type == "python":
        return f"""version: '3.8'

services:
  app:
    build: .
    ports:
      - "{port}:{port}"
    environment:
      - PYTHONPATH=/app/src
    volumes:
      - ./src:/app/src
      - ./config:/app/config
    depends_on:
      - redis
      - neo4j

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  neo4j:
    image: neo4j:5
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/password
      - NEO4J_PLUGINS=["apoc"]
    volumes:
      - neo4j_data:/data

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

volumes:
  redis_data:
  neo4j_data:
  prometheus_data:"""
    
    else:
        return f"""version: '3.8'

services:
  app:
    build: .
    ports:
      - "{port}:{port}"
    volumes:
      - .:/app
      - /app/node_modules

volumes:
  app_data:"""

def generate_dockerignore(project_type):
    """Generate .dockerignore content."""
    base_ignore = """# Dependencies
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Runtime data
pids/
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/
*.lcov

# nyc test coverage
.nyc_output

# Dependency directories
jspm_packages/

# Optional npm cache directory
.npm

# Optional eslint cache
.eslintcache

# Microbundle cache
.rpt2_cache/
.rts2_cache_cjs/
.rts2_cache_es/
.rts2_cache_umd/

# Optional REPL history
.node_repl_history

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity

# dotenv environment variables file
.env
.env.test
.env.production

# parcel-bundler cache (https://parceljs.org/)
.cache
.parcel-cache

# Next.js build output
.next

# Nuxt.js build / generate output
.nuxt
dist

# Gatsby files
.cache/
public

# Storybook build outputs
.out
.storybook-out

# Temporary folders
tmp/
temp/

# Git
.git/
.gitignore

# Docker
Dockerfile
docker-compose.yml
.dockerignore

# Documentation
README.md
docs/

# Tests
tests/
test/
__tests__/
*.test.js
*.spec.js

# Build outputs
build/
dist/
out/

# Local development
.local/
"""
    
    if project_type == "python":
        return base_ignore + """
# Python specific
*.egg-info/
.pytest_cache/
.coverage
htmlcov/
.tox/
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
"""
    else:
        return base_ignore

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Generate Docker files for your project.")
    parser.add_argument("--type", help="Override detected project type.")
    parser.add_argument("--port", help="Override detected port.")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompts.")
    parser.add_argument("-f", "--force", action="store_true", help="Overwrite existing Docker files.")
    
    args = parser.parse_args()
    
    # Detect project type and port
    project_type = args.type or detect_project_type()
    port = args.port or detect_port()
    
    print(f"🔍 Detected project type: {project_type}")
    print(f"🔍 Detected port: {port}")
    
    if project_type == "unknown":
        print("❌ Could not detect project type. Please specify with --type")
        sys.exit(1)
    
    # Generate content
    dockerfile_content = generate_dockerfile(project_type, port)
    docker_compose_content = generate_docker_compose(project_type, port)
    dockerignore_content = generate_dockerignore(project_type)
    
    # Show what will be created
    print("\n📋 Files to be created:")
    print(f"  - Dockerfile (for {project_type} project)")
    print(f"  - docker-compose.yml (port {port})")
    print(f"  - .dockerignore")
    
    # Confirm unless --yes is used
    if not args.yes:
        response = input("\n🤔 Proceed? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("❌ Cancelled.")
            sys.exit(0)
    
    # Write files
    print("\n🚀 Creating Docker files...")
    write_file("Dockerfile", dockerfile_content, force=args.force)
    write_file("docker-compose.yml", docker_compose_content, force=args.force)
    write_file(".dockerignore", dockerignore_content, force=args.force)
    
    print(f"\n✅ Docker files created successfully!")
    print(f"📝 Next steps:")
    print(f"  1. Review the generated files")
    print(f"  2. Run: docker compose up --build")
    print(f"  3. Access your app at: http://localhost:{port}")

if __name__ == "__main__":
    main()

