#!/bin/bash
# Optimized Docker build script with performance monitoring

set -e

echo "🚀 Starting optimized Docker build..."
echo "📊 Monitoring build performance..."

# Enable BuildKit for caching support
export DOCKER_BUILDKIT=1

# Build with resource optimization and cache
time docker buildx build \
    --progress=plain \
    --no-cache-filter="" \
    --memory=8g \
    --cpus=4 \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --tag zerotoship:latest \
    --tag zerotoship:$(date +%Y%m%d-%H%M%S) \
    .

echo "✅ Build completed!"
echo "📈 Build statistics:"
docker images zerotoship:latest --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

echo ""
echo "💡 Quick build tips:"
echo "   - Next build will be much faster due to cache layers"
echo "   - Use 'docker system prune -a' if you need to clear build cache"
echo "   - Run with '--cpus=8 --memory=16g' if you have more resources"