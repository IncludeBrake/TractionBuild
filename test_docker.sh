#!/bin/bash

echo "🐳 Testing ZeroToShip Docker Container"

# Build the image
echo "📦 Building Docker image..."
docker build -t zerotoship-test .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

echo "✅ Docker build successful"

# Test basic container startup
echo "🚀 Testing container startup..."
docker run --rm -d --name zerotoship-test-container zerotoship-test

# Wait a moment for the container to start
sleep 5

# Check if container is running
if docker ps | grep -q zerotoship-test-container; then
    echo "✅ Container started successfully"
    
    # Check container logs
    echo "📋 Container logs:"
    docker logs zerotoship-test-container
    
    # Stop the container
    docker stop zerotoship-test-container
    echo "✅ Container stopped successfully"
else
    echo "❌ Container failed to start"
    docker logs zerotoship-test-container
    exit 1
fi

echo "🎉 All tests passed!"
