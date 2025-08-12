# Docker Requirements Documentation

This document explains the different requirements files available for Docker deployments of ZeroToShip.

## 📦 Requirements Files Overview

### 1. `requirements-docker.txt` (Full Development)
**Purpose**: Complete development environment with all dependencies
**Use Case**: Local development, testing, and full feature development
**Size**: ~500MB+ (includes all ML libraries, visualization tools, etc.)

**Includes**:
- All core AI/ML dependencies
- Visualization libraries (matplotlib, seaborn)
- Development tools (pytest, black, mypy)
- Monitoring and observability tools
- Security libraries

### 2. `requirements-docker-prod.txt` (Production Optimized)
**Purpose**: Minimal production deployment
**Use Case**: Production Kubernetes/Docker deployments
**Size**: ~200MB (optimized for speed and security)

**Includes**:
- Core AI framework (CrewAI, LangChain)
- Essential web framework (FastAPI, Uvicorn)
- Database connectivity (Neo4j)
- Basic monitoring (Prometheus)
- Security essentials

### 3. `requirements-docker-dev.txt` (Development Tools)
**Purpose**: Development environment with debugging tools
**Use Case**: Development containers, debugging sessions
**Size**: ~600MB+ (includes debugging and profiling tools)

**Includes**:
- All production requirements
- Debugging tools (debugpy, memory-profiler)
- Code quality tools (black, flake8, mypy)
- Jupyter notebooks for interactive development

## 🚀 Usage Examples

### Production Docker Build
```dockerfile
# Use production requirements for smaller, faster builds
COPY requirements-docker-prod.txt ./requirements.txt
RUN pip install -r requirements.txt
```

### Development Docker Build
```dockerfile
# Use full requirements for development
COPY requirements-docker-dev.txt ./requirements.txt
RUN pip install -r requirements.txt
```

### Multi-stage Build (Recommended)
```dockerfile
# Build stage with full requirements
FROM python:3.12-slim AS builder
COPY requirements-docker.txt ./
RUN pip install -r requirements-docker.txt

# Production stage with minimal requirements
FROM python:3.12-slim AS production
COPY requirements-docker-prod.txt ./
RUN pip install -r requirements-docker-prod.txt
```

## 🔧 Environment-Specific Considerations

### Kubernetes Deployment
- Use `requirements-docker-prod.txt` for smaller image sizes
- Faster pod startup times
- Reduced resource consumption

### Local Development
- Use `requirements-docker-dev.txt` for full development experience
- Includes debugging and profiling tools
- Better for troubleshooting and development

### CI/CD Pipeline
- Use `requirements-docker.txt` for comprehensive testing
- Ensures all dependencies are available for tests
- Catches dependency-related issues early

## 📊 Size Comparison

| Requirements File | Base Size | With Dependencies | Use Case |
|------------------|-----------|-------------------|----------|
| `requirements-docker-prod.txt` | ~50MB | ~200MB | Production |
| `requirements-docker.txt` | ~50MB | ~500MB | Development |
| `requirements-docker-dev.txt` | ~50MB | ~600MB | Debugging |

## 🛠️ Customization

### Adding New Dependencies
1. **Production**: Add to `requirements-docker-prod.txt`
2. **Development**: Add to `requirements-docker-dev.txt`
3. **All Environments**: Add to `requirements-docker.txt`

### Removing Dependencies
- Remove from the appropriate requirements file
- Test thoroughly to ensure no breaking changes
- Update documentation if needed

## 🔍 Troubleshooting

### Common Issues

1. **Build Timeouts**
   - Use `requirements-docker-prod.txt` for faster builds
   - Consider multi-stage builds

2. **Memory Issues**
   - Reduce concurrent downloads in pip
   - Use `--no-cache-dir` for temporary builds

3. **Dependency Conflicts**
   - Pin specific versions in requirements files
   - Use virtual environments for isolation

### Performance Optimization

1. **Layer Caching**
   ```dockerfile
   # Copy requirements first for better caching
   COPY requirements-docker-prod.txt ./
   RUN pip install -r requirements-docker-prod.txt
   COPY . .
   ```

2. **Multi-stage Builds**
   ```dockerfile
   FROM python:3.12-slim AS builder
   # Install all dependencies
   
   FROM python:3.12-slim AS production
   # Copy only runtime dependencies
   ```

## 📝 Best Practices

1. **Always specify versions** in requirements files
2. **Use production requirements** for deployment
3. **Test with production requirements** before deployment
4. **Keep requirements files updated** with security patches
5. **Document any custom dependencies** added

## 🔗 Related Files

- `Dockerfile` - Main container definition
- `docker-compose.yml` - Local development setup
- `k8s/` - Kubernetes deployment manifests
- `entrypoint.sh` - Container startup script
