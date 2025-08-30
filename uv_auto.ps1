# Enhanced uv_auto.ps1 script with clean functionality
# Usage: .\uv_auto.ps1 [clean]

param(
    [string]$Action = "setup"
)

# Define the name for the virtual environment directory
$VENV_NAME = ".venv"

# Function to clean virtual environment
function Clean-Venv {
    if (Test-Path $VENV_NAME) {
        Write-Host "🧹 Deleting the virtual environment: $VENV_NAME" -ForegroundColor Yellow
        Remove-Item -Recurse -Force $VENV_NAME
        Write-Host "✅ Virtual environment deleted successfully." -ForegroundColor Green
    } else {
        Write-Host "ℹ️  No virtual environment found to delete." -ForegroundColor Blue
    }
}

# Check if clean command is provided
if ($Action -eq "clean") {
    Clean-Venv
    exit 0
}

# Check if uv is installed
try {
    $null = Get-Command uv -ErrorAction Stop
} catch {
    Write-Host "❌ Error: uv is not installed or not in PATH" -ForegroundColor Red
    Write-Host "📦 Install uv with: pipx install uv" -ForegroundColor Yellow
    exit 1
}

Write-Host "🚀 Starting uv_auto.ps1..." -ForegroundColor Cyan

# Check if the virtual environment directory exists
if (Test-Path $VENV_NAME) {
    Write-Host "✅ Virtual environment already exists. Activating..." -ForegroundColor Green
    & "$VENV_NAME\Scripts\Activate.ps1"
} else {
    Write-Host "🔨 Virtual environment not found. Creating and activating..." -ForegroundColor Yellow
    uv venv
    & "$VENV_NAME\Scripts\Activate.ps1"
}

# Check for a pyproject.toml file to install dependencies
if (Test-Path "pyproject.toml") {
    Write-Host "📋 pyproject.toml found. Syncing dependencies with uv sync..." -ForegroundColor Green
    uv sync
} elseif (Test-Path "requirements.txt") {
    Write-Host "📋 requirements.txt found. Installing dependencies with uv pip install..." -ForegroundColor Green
    uv pip install -r requirements.txt
} else {
    Write-Host "⚠️  No pyproject.toml or requirements.txt found. Skipping dependency installation." -ForegroundColor Yellow
}

Write-Host "✅ Setup complete! Virtual environment is active." -ForegroundColor Green
Write-Host "💡 To clean the environment, run: .\uv_auto.ps1 clean" -ForegroundColor Cyan
Write-Host "💡 To deactivate, run: deactivate" -ForegroundColor Cyan

# Script will continue to run in the active shell.
