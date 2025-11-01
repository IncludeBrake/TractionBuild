# Repo Doctor - One-click diagnostics
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "`n=== REPO DOCTOR STARTING ===`n" -ForegroundColor Cyan

# Move to project root
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

# Create output directory
New-Item -ItemType Directory -Force -Path "repo-tools\out" | Out-Null

# Step 1: Python virtual environment
Write-Host "[1/6] Setting up Python environment..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
& ".\.venv\Scripts\pip.exe" install --quiet -r repo-tools\requirements.txt

# Step 2: Node packages (if needed)
if (Test-Path "package.json") {
    Write-Host "[2/6] Installing Node packages..." -ForegroundColor Yellow
    npm install --silent
} else {
    Write-Host "[2/6] Skipping Node (no package.json found)" -ForegroundColor Gray
}

# Step 3: Run Python diagnostics
Write-Host "[3/6] Running Python diagnostics..." -ForegroundColor Yellow
& ".\.venv\Scripts\python.exe" repo-tools\scripts\run_python_checks.py

# Step 4: Run JavaScript diagnostics (if applicable)
if (Test-Path "package.json") {
    Write-Host "[4/6] Running JavaScript diagnostics..." -ForegroundColor Yellow
    node repo-tools\scripts\run_js_checks.mjs
} else {
    Write-Host "[4/6] Skipping JavaScript diagnostics" -ForegroundColor Gray
}

# Step 5: (Optional) Capture runtime logs
# Uncomment if you have a start script you want to test:
# Write-Host "[5/6] Capturing runtime logs..." -ForegroundColor Yellow
# wsl bash repo-tools/scripts/collect_runtime_traces.sh
Write-Host "[5/6] Skipping runtime capture (not configured)" -ForegroundColor Gray

# Step 6: Create bundle
Write-Host "[6/6] Packaging bundle..." -ForegroundColor Yellow
& ".\.venv\Scripts\python.exe" repo-tools\scripts\make_bundle.py

Write-Host "`n=== REPO DOCTOR COMPLETE ===`n" -ForegroundColor Green
Write-Host "Bundle location: repo-tools\repo_doctor_bundle\repo_doctor.tar.gz" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Review artifacts in repo-tools\out\" -ForegroundColor White
Write-Host "  2. Upload the .tar.gz + PROMPT_repo_doctor.md to your AI" -ForegroundColor White
Write-Host "  3. Apply the patches it generates" -ForegroundColor White
Write-Host "  4. Re-run this script to verify fixes`n" -ForegroundColor White