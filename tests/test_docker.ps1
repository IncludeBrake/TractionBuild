# PowerShell script to test TractionBuild Docker Container

Write-Host "🐳 Testing TractionBuild Docker Container" -ForegroundColor Green

# Build the image
Write-Host "📦 Building Docker image..." -ForegroundColor Yellow
docker build -t TractionBuild-test .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Docker build successful" -ForegroundColor Green

# Test basic container startup
Write-Host "🚀 Testing container startup..." -ForegroundColor Yellow
docker run --rm -d --name TractionBuild-test-container TractionBuild-test

# Wait a moment for the container to start
Start-Sleep -Seconds 5

# Check if container is running
$containerRunning = docker ps | Select-String "TractionBuild-test-container"

if ($containerRunning) {
    Write-Host "✅ Container started successfully" -ForegroundColor Green
    
    # Check container logs
    Write-Host "📋 Container logs:" -ForegroundColor Yellow
    docker logs TractionBuild-test-container
    
    # Stop the container
    docker stop TractionBuild-test-container
    Write-Host "✅ Container stopped successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Container failed to start" -ForegroundColor Red
    docker logs TractionBuild-test-container
    exit 1
}

Write-Host "🎉 All tests passed!" -ForegroundColor Green
