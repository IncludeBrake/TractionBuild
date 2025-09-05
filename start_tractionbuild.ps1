# start_tractionbuild.ps1
# PowerShell script to start TractionBuild server with Salem AI integration

param(
    [switch]$Force,
    [switch]$Background
)

Write-Host "🚀 Starting TractionBuild with Salem AI..." -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan

# Set working directory
$tractionBuildPath = "C:\Users\jthri\Dev\MySauce\TractionBuild"
Set-Location $tractionBuildPath

# Activate virtual environment
Write-Host "📦 Activating virtual environment..." -ForegroundColor Blue
& "$tractionBuildPath\.venv\Scripts\Activate.ps1"

# Check if server is already running
$serverRunning = $false
if (-not $Force) {
    try {
        Write-Host "🔍 Checking if server is already running..." -ForegroundColor Blue
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 3 -ErrorAction Stop
        Write-Host "✅ Server already running on port 8000" -ForegroundColor Yellow
        $serverRunning = $true
    } catch {
        Write-Host "📡 Server not running, starting..." -ForegroundColor Blue
    }
}

if (-not $serverRunning -or $Force) {
    # Kill any existing Python processes
    if ($Force) {
        Write-Host "🛑 Killing existing Python processes..." -ForegroundColor Red
        Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }

    # Start the server
    Write-Host "🎯 Starting TractionBuild API server..." -ForegroundColor Green
    Write-Host "🌐 Server will be available at: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "🤖 Salem AI marketing automation ready!" -ForegroundColor Magenta
    Write-Host "" -ForegroundColor White

    if ($Background) {
        # Start in background
        $job = Start-Job -ScriptBlock {
            Set-Location "C:\Users\jthri\Dev\MySauce\TractionBuild"
            & "C:\Users\jthri\Dev\MySauce\TractionBuild\.venv\Scripts\Activate.ps1"
            python app_v1_real_integration.py
        }
        Write-Host "✅ Server started in background (Job ID: $($job.Id))" -ForegroundColor Green
    } else {
        # Start in foreground
        python app_v1_real_integration.py
    }
} else {
    Write-Host "ℹ️  Server is already running. Use -Force to restart." -ForegroundColor Yellow
    Write-Host "🌐 Access at: http://localhost:8000" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "🎯 Quick Commands:" -ForegroundColor White
Write-Host "  • Test: .\test_tractionbuild.ps1" -ForegroundColor Gray
Write-Host "  • Health: Invoke-RestMethod -Uri ""http://localhost:8000/health""" -ForegroundColor Gray
Write-Host "  • Create project: See test script examples" -ForegroundColor Gray
Write-Host ""
Write-Host "✨ Salem AI Marketing Automation Ready!" -ForegroundColor Magenta