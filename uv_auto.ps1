# Enhanced uv_auto.ps1 script with clean functionality
# Usage: .\uv_auto.ps1 [clean]

param(
    [string]$Action = "setup"
)

# Define the name for the virtual environment directory
$VENV_NAME = ".venv"

# --- Function Definition ---
# Must be defined *before* it is called
function Clean-Venv {
    if (Test-Path $VENV_NAME) {
        Write-Host "🧹 Deleting the virtual environment: $VENV_NAME" -ForegroundColor Yellow
        Remove-Item -Recurse -Force $VENV_NAME
        Write-Host "✅ Virtual environment deleted successfully." -ForegroundColor Green
    } else {
        Write-Host "ℹ️  No virtual environment found to delete." -ForegroundColor Blue
    }
}

# --- Action Handler ---

# 1. Check if clean command is provided
if ($Action -eq "clean") {
    Clean-Venv
    exit 0
}

# 2. Check if uv is installed
try {
    $null = Get-Command uv -ErrorAction Stop
} catch {
    Write-Host "❌ Error: uv is not installed or not in PATH" -ForegroundColor Red
    Write-Host "📦 Install uv with: pipx install uv" -ForegroundColor Yellow
    exit 1
}

Write-Host "🚀 Starting uv_auto.ps1..." -ForegroundColor Cyan

# 3. Create or Activate Venv
Write-Host "🔨 Creating/re-creating fresh virtual environment with Python 3.12..." -ForegroundColor Yellow

# We must clean first to prevent errors
Clean-Venv
# Now, create the venv using Python's standard library
py -3.12 -m venv $VENV_NAME

# Check if venv creation was successful
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Failed to create venv with 'py -3.12 -m venv'. Make sure Python 3.12 is installed." -ForegroundColor Red
    exit 1
}
& "$VENV_NAME\Scripts\Activate.ps1"


# 4. Install dependencies (*** MODIFIED TO USE requirements.txt ***)
# --- SET YOUR REQUIREMENTS FILE NAME HERE ---
$ReqFile = "requirements.txt"

if (Test-Path $ReqFile) {
    Write-Host "📋 $ReqFile found. Installing dependencies..." -ForegroundColor Green
    
    # We use pip and --trusted-host to handle the network proxy
    Write-Host "Running: pip install -r $ReqFile --no-cache --index-url https://pypi.org/simple --trusted-host pypi.org"
    pip install -r $ReqFile --no-cache --index-url https://pypi.org/simple --trusted-host pypi.org
    
    # Check the exit code of the last command
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error: Dependency installation failed. See output above." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "⚠️  No $ReqFile found. Cannot install dependencies." -ForegroundColor Yellow
}

Write-Host "✅ Setup complete! Virtual environment is active." -ForegroundColor Green
Write-Host "💡 To clean the environment, run: .\uv_auto.ps1 clean" -ForegroundColor Cyan
Write-Host "💡 To deactivate, run: deactivate" -ForegroundColor Cyan