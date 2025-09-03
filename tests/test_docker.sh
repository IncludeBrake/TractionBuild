#!/bin/bash

echo "🐳 Testing tractionbuild Docker Container"

# Build the image
echo "📦 Building Docker image..."
docker build -t tractionbuild-test .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

echo "✅ Docker build successful"

# Test basic container startup
echo "🚀 Testing container startup..."
docker run --rm -d --name tractionbuild-test-container tractionbuild-test

# Wait a moment for the container to start
sleep 5

# Check if container is running
if docker ps | grep -q tractionbuild-test-container; then
    echo "✅ Container started successfully"
    
    # Check container logs
    echo "📋 Container logs:"
    docker logs tractionbuild-test-container
    
    # Stop the container
    docker stop tractionbuild-test-container
    echo "✅ Container stopped successfully"
else
    echo "❌ Container failed to start"
    docker logs tractionbuild-test-container
    exit 1
fi

echo "🎉 All tests passed!"
