# Optimized Docker build script for Windows with performance monitoring

Write-Host "🚀 Starting optimized Docker build..." -ForegroundColor Green
Write-Host "📊 Monitoring build performance..." -ForegroundColor Yellow

# Enable BuildKit for caching support
$env:DOCKER_BUILDKIT = "1"

# Build with resource optimization and cache
$buildStart = Get-Date
try {
    docker buildx build `
        --progress=plain `
        --no-cache-filter="" `
        --memory=8g `
        --cpus=4 `
        --build-arg BUILDKIT_INLINE_CACHE=1 `
        --tag zerotoship:latest `
        --tag "zerotoship:$(Get-Date -Format 'yyyyMMdd-HHmmss')" `
        .
    
    $buildEnd = Get-Date
    $buildDuration = $buildEnd - $buildStart
    
    Write-Host "✅ Build completed in $($buildDuration.TotalMinutes.ToString('F2')) minutes!" -ForegroundColor Green
    Write-Host "📈 Build statistics:" -ForegroundColor Cyan
    docker images zerotoship:latest --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    
    Write-Host ""
    Write-Host "💡 Quick build tips:" -ForegroundColor Yellow
    Write-Host "   - Next build will be much faster due to cache layers" -ForegroundColor Gray
    Write-Host "   - Use 'docker system prune -a' if you need to clear build cache" -ForegroundColor Gray
    Write-Host "   - Run with '--cpus=8 --memory=16g' if you have more resources" -ForegroundColor Gray
}
catch {
    Write-Host "❌ Build failed: $_" -ForegroundColor Red
    exit 1
}