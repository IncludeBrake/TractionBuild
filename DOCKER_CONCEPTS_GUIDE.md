# 🐳 Docker Concepts Guide for ZeroToShip

This guide explains the key Docker concepts you mentioned and how they apply to the ZeroToShip project.

## 🏗️ **Key Dockerfile Concepts**

### **1. Base Image**
```dockerfile
FROM python:3.12-slim
```
- **Purpose**: Foundation that provides OS and core tools
- **Why `slim`**: Lightweight (~50MB vs ~200MB for full image)
- **Trade-off**: May need extra packages (gcc, g++ for ML libraries)
- **Best Practice**: Use specific tags (e.g., `3.12.0-slim`) to avoid surprises

### **2. Instructions**
```dockerfile
# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy files
COPY requirements-docker.txt ./
COPY src/ ./src
COPY main.py ./

# Set environment variables
ENV PYTHONPATH="/app/src"
ENV NEO4J_URI="neo4j://host.docker.internal:7687"
```

### **3. Layers and Caching**
```dockerfile
# Layer 1: System dependencies (rarely changes)
RUN apt-get update && apt-get install -y gcc g++ curl

# Layer 2: Python dependencies (changes when requirements.txt changes)
COPY requirements-docker.txt ./
RUN pip install -r requirements-docker.txt

# Layer 3: Application code (changes frequently)
COPY src/ ./src
COPY main.py ./
```

**Key Insight**: Each instruction creates a cached layer. Changing `requirements-docker.txt` invalidates layers 2 and 3, but layer 1 is reused.

### **4. Entrypoint vs Command**
```dockerfile
# ENTRYPOINT: Main executable (always runs)
ENTRYPOINT ["/app/entrypoint.sh"]

# CMD: Default arguments (can be overridden)
CMD ["python", "main.py", "--idea", "Default Idea", "--workflow", "validation_and_launch"]
```

**Your Issue**: Missing `/app/entrypoint.sh` caused container startup failure.

## 🔧 **Basic Structure for ZeroToShip**

```dockerfile
# Start with optimized base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for ML libraries
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (for caching)
COPY requirements-docker.txt pyproject.toml ./

# Install Python dependencies
RUN pip install uv && \
    uv venv && \
    . .venv/bin/activate && \
    uv pip install -r requirements-docker.txt

# Copy application code
COPY src/ ./src
COPY main.py ./
COPY config/ ./config

# Ensure entrypoint script is present and executable
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

# Create necessary directories
RUN mkdir -p /app/output /app/data /app/logs

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"
ENV NEO4J_URI="neo4j://host.docker.internal:7687"

# Define how the container starts
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "main.py", "--idea", "Default Production Idea", "--workflow", "validation_and_launch"]
```

## 🚨 **Fixing Your Specific Issue**

### **Problem**: `/app/entrypoint.sh` not found

**Root Causes**:
1. **Missing File**: `entrypoint.sh` not in project directory
2. **Dockerignore**: File excluded by `.dockerignore`
3. **Copy Missing**: `COPY entrypoint.sh .` missing in Dockerfile
4. **Windows Issues**: Line endings (`\r\n` vs `\n`)

### **Solutions**:

#### **1. Verify File Exists**
```bash
# Check if entrypoint.sh exists
ls -la entrypoint.sh

# If missing, create it
touch entrypoint.sh
chmod +x entrypoint.sh
```

#### **2. Check .dockerignore**
```bash
# Ensure entrypoint.sh is not excluded
cat .dockerignore
# Should NOT contain: entrypoint.sh
```

#### **3. Fix Dockerfile**
```dockerfile
# Add this line to your Dockerfile
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh
```

#### **4. Fix Windows Line Endings**
```bash
# Convert to Unix line endings
dos2unix entrypoint.sh

# Or use VS Code: File > Save with Encoding > UTF-8
```

## 📝 **Example entrypoint.sh for ZeroToShip**

```bash
#!/bin/bash
set -e

echo "🚀 Starting ZeroToShip container..."

# Check if required arguments are provided
if [ -z "$IDEA" ] && [ -z "$WORKFLOW" ]; then
    echo "Using default arguments from CMD"
else
    echo "Using environment variables: IDEA=$IDEA, WORKFLOW=$WORKFLOW"
fi

# Activate virtual environment
source /app/.venv/bin/activate

# Check if config files exist
if [ ! -f "/app/config/workflows.yaml" ]; then
    echo "❌ Error: workflows.yaml not found in /app/config/"
    exit 1
fi

echo "✅ Configuration files found"

# Create output directories
mkdir -p /app/output/logs
mkdir -p /app/output/diagrams
mkdir -p /app/data

# Set environment variables
export HOME="/app"
export CREWAI_MEMORY_PATH="/app/output/crewai_memory"

# Run the application
echo "🎯 Executing ZeroToShip..."
if [ -n "$IDEA" ] && [ -n "$WORKFLOW" ]; then
    python main.py --idea "$IDEA" --workflow "$WORKFLOW"
else
    exec "$@"
fi
```

## 🏗️ **Writing Better Dockerfiles for AI Stack**

### **Optimize Caching**
```dockerfile
# ✅ Good: Dependencies first (rarely change)
COPY requirements-docker.txt pyproject.toml ./
RUN pip install -r requirements-docker.txt

# ✅ Good: Code last (changes frequently)
COPY src/ ./src
COPY main.py ./
```

### **Minimize Image Size**
```dockerfile
# ✅ Good: Clean up in same RUN layer
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# ❌ Bad: Separate layers create bloat
RUN apt-get update && apt-get install -y gcc g++
RUN rm -rf /var/lib/apt/lists/*
```

### **Multi-Stage Builds**
```dockerfile
# Stage 1: Build dependencies
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements-docker.txt ./
RUN pip install -r requirements-docker.txt

# Stage 2: Production image
FROM python:3.12-slim AS production
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY src/ ./src
COPY main.py ./
```

## 🔍 **Troubleshooting Common Issues**

### **1. Build Timeouts**
```dockerfile
# Use production requirements for faster builds
COPY requirements-docker-prod.txt ./requirements.txt
RUN pip install -r requirements.txt
```

### **2. Memory Issues**
```dockerfile
# Reduce concurrent downloads
RUN pip install --no-cache-dir -r requirements.txt
```

### **3. Permission Issues**
```dockerfile
# Create non-root user
RUN groupadd -r zerotoship && useradd -r -g zerotoship zerotoship
USER zerotoship
```

### **4. Network Issues**
```dockerfile
# Use host.docker.internal for host connectivity
ENV NEO4J_URI="neo4j://host.docker.internal:7687"
```

## 🚀 **Best Practices for ZeroToShip**

1. **Use Multi-Stage Builds**: Separate build and runtime environments
2. **Optimize Layer Caching**: Copy dependencies before code
3. **Minimize Image Size**: Use slim images and clean up caches
4. **Security**: Run as non-root user
5. **Health Checks**: Add container health monitoring
6. **Environment Variables**: Use for configuration
7. **Volume Mounts**: For persistent data

## 📊 **Performance Comparison**

| Approach | Build Time | Image Size | Security | Use Case |
|----------|------------|------------|----------|----------|
| Single Stage | 5-10 min | 500MB+ | Basic | Development |
| Multi-Stage | 3-5 min | 200MB | Good | Production |
| Alpine Base | 2-3 min | 150MB | Good | Minimal |

## 🔗 **Related Files**

- `Dockerfile` - Main container definition
- `entrypoint.sh` - Container startup script
- `requirements-docker.txt` - Python dependencies
- `docker-compose.yml` - Local development setup
- `.dockerignore` - Files to exclude from build
