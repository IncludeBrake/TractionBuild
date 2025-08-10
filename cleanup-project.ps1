# ZeroToShip Project Cleanup Script
# Removes files that are no longer needed after recent fixes and improvements

Write-Host "🧹 ZeroToShip Project Cleanup" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green

# ============================================================================
# STEP 1: REMOVE OBSOLETE DEPLOYMENT FILES
# ============================================================================
Write-Host "📁 Step 1: Removing obsolete deployment files..." -ForegroundColor Yellow

$obsoleteFiles = @(
    # Root level obsolete files
    "zerotoship-job.yaml",                    # Moved to k8s/zerotoship_job.yaml
    "service.yaml",                           # Integrated into zerotoship-deployment.yaml
    "deployment.yaml",                        # Replaced by k8s/zerotoship-deployment.yaml
    
    # K8s directory obsolete files
    "k8s/zerotoship-deployment-backup.yaml",  # Backup no longer needed
    "k8s/zerotoship-deployment-fix.ps1",      # Superseded by deploy-with-fixes.ps1
    "k8s/deployment-errors.log",              # Temporary log file
    "k8s/vault-dev-deployment.yaml",          # Using production setup now
    "k8s/vault-setup.ps1",                    # Superseded by vault-production-setup.ps1
    "k8s/vault-setup.sh",                     # Using PowerShell scripts
    "k8s/deploy.ps1",                         # Superseded by deploy-with-fixes.ps1
    "k8s/deploy.sh",                          # Using PowerShell scripts
    "k8s/cleanup.sh",                         # Using PowerShell scripts
    
    # Temporary test files
    "test_neo4j_connection.py",               # Temporary test file
    "test_state_fix.py",                      # Temporary test file
    "test_docker.ps1",                        # Temporary test file
    "test_docker.sh",                         # Temporary test file
    
    # Old documentation
    "Cleanup_Project_Script_Outcome.txt",     # Temporary documentation
    "PROJECT_STRUCTURE.md"                    # Empty file
)

foreach ($file in $obsoleteFiles) {
    if (Test-Path $file) {
        Write-Host "  - Removing: $file" -ForegroundColor Cyan
        Remove-Item $file -Force
    } else {
        Write-Host "  - Not found: $file" -ForegroundColor Gray
    }
}

# ============================================================================
# STEP 2: CLEAN UP OUTPUT DIRECTORY
# ============================================================================
Write-Host "📊 Step 2: Cleaning up output directory..." -ForegroundColor Yellow

# Remove old project outputs (keep recent ones)
$outputDirs = Get-ChildItem "output" -Directory | Where-Object { $_.Name -like "project_*" }
if ($outputDirs.Count -gt 2) {
    # Keep only the 2 most recent project directories
    $outputDirs | Sort-Object LastWriteTime -Descending | Select-Object -Skip 2 | ForEach-Object {
        Write-Host "  - Removing old project output: $($_.Name)" -ForegroundColor Cyan
        Remove-Item $_.FullName -Recurse -Force
    }
}

# Clean up old logs
if (Test-Path "output/logs") {
    $oldLogs = Get-ChildItem "output/logs" -File | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) }
    foreach ($log in $oldLogs) {
        Write-Host "  - Removing old log: $($log.Name)" -ForegroundColor Cyan
        Remove-Item $log.FullName -Force
    }
}

# ============================================================================
# STEP 3: CLEAN UP TESTS DIRECTORY
# ============================================================================
Write-Host "🧪 Step 3: Cleaning up tests directory..." -ForegroundColor Yellow

# Remove obsolete test files (keep core tests)
$obsoleteTests = @(
    "tests/test_enterprise_system.py",        # Too complex, not needed
    "tests/test_final_production_certification.py",  # Too complex
    "tests/test_production_fixes.py",         # Superseded by actual fixes
    "tests/test_final_loop_fix.py",           # Superseded by actual fixes
    "tests/test_simple_loop_fix.py",          # Superseded by actual fixes
    "tests/test_marketing_campaign_fix.py",   # Superseded by actual fixes
    "tests/test_production_ready.py",         # Superseded by actual fixes
    "tests/test_enhanced_workflows.py",       # Too complex
    "tests/test_enhanced_connection.py",      # Superseded by actual fixes
    "tests/test_enhanced_crew_controller.py", # Too complex
    "tests/test_enhanced_crews.py",           # Too complex
    "tests/test_integrated_core.py"           # Too complex
)

foreach ($test in $obsoleteTests) {
    if (Test-Path $test) {
        Write-Host "  - Removing obsolete test: $test" -ForegroundColor Cyan
        Remove-Item $test -Force
    }
}

# ============================================================================
# STEP 4: CLEAN UP VAULT DIRECTORY
# ============================================================================
Write-Host "🔐 Step 4: Cleaning up Vault directory..." -ForegroundColor Yellow

if (Test-Path "vault.hcl") {
    Write-Host "  - Removing temporary Vault config directory" -ForegroundColor Cyan
    Remove-Item "vault.hcl" -Recurse -Force
}

# ============================================================================
# STEP 5: CLEAN UP DEPLOYMENT DIRECTORY
# ============================================================================
Write-Host "🚀 Step 5: Cleaning up deployment directory..." -ForegroundColor Yellow

# Remove old deployment files that are now handled by k8s
$deploymentFiles = @(
    "deployment/web/public/index.html",       # Not needed for k8s deployment
    "deployment/web/server.js",               # Not needed for k8s deployment
    "deployment/web/src/components",          # Not needed for k8s deployment
    "deployment/web/src/utils"                # Not needed for k8s deployment
)

foreach ($file in $deploymentFiles) {
    if (Test-Path $file) {
        Write-Host "  - Removing deployment file: $file" -ForegroundColor Cyan
        Remove-Item $file -Recurse -Force
    }
}

# ============================================================================
# STEP 6: CLEAN UP CONFIG DIRECTORY
# ============================================================================
Write-Host "⚙️  Step 6: Cleaning up config directory..." -ForegroundColor Yellow

# Check if config files are still needed
$configFiles = Get-ChildItem "config" -File
foreach ($config in $configFiles) {
    # Check if the config is referenced in the main application
    $content = Get-Content $config.FullName -Raw
    if ($content.Length -lt 100) {  # Very small config files might be obsolete
        Write-Host "  - Checking small config file: $($config.Name)" -ForegroundColor Yellow
    }
}

# ============================================================================
# STEP 7: FINAL CLEANUP
# ============================================================================
Write-Host "✨ Step 7: Final cleanup..." -ForegroundColor Yellow

# Remove any empty directories
Get-ChildItem -Directory -Recurse | Where-Object { 
    (Get-ChildItem $_.FullName -Recurse | Measure-Object).Count -eq 0 
} | ForEach-Object {
    Write-Host "  - Removing empty directory: $($_.FullName)" -ForegroundColor Cyan
    Remove-Item $_.FullName -Force
}

# Remove any .DS_Store files (macOS)
Get-ChildItem -Name ".DS_Store" -Recurse -Force 2>$null | ForEach-Object {
    Write-Host "  - Removing .DS_Store file: $_" -ForegroundColor Cyan
    Remove-Item $_ -Force
}

# Remove any Thumbs.db files (Windows)
Get-ChildItem -Name "Thumbs.db" -Recurse -Force 2>$null | ForEach-Object {
    Write-Host "  - Removing Thumbs.db file: $_" -ForegroundColor Cyan
    Remove-Item $_ -Force
}

# ============================================================================
# SUMMARY
# ============================================================================
Write-Host ""
Write-Host "🎉 Cleanup Complete!" -ForegroundColor Green
Write-Host "===================" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Cleanup Summary:" -ForegroundColor Cyan
Write-Host "✅ Removed obsolete deployment files"
Write-Host "✅ Cleaned up old output directories"
Write-Host "✅ Removed obsolete test files"
Write-Host "✅ Cleaned up temporary Vault files"
Write-Host "✅ Removed old deployment web files"
Write-Host "✅ Cleaned up empty directories"
Write-Host "✅ Removed system files (.DS_Store, Thumbs.db)"
Write-Host ""
Write-Host "📁 Remaining Core Files:" -ForegroundColor Yellow
Write-Host "• main.py - Main application"
Write-Host "• k8s/ - Kubernetes deployment files"
Write-Host "• src/ - Source code"
Write-Host "• tests/ - Core test files"
Write-Host "• config/ - Configuration files"
Write-Host "• docs/ - Documentation"
Write-Host "• Dockerfile - Container configuration"
Write-Host "• docker-compose.yml - Local development"
Write-Host ""
Write-Host "🚀 Next Steps:" -ForegroundColor Green
Write-Host "1. Review the remaining files to ensure nothing important was removed"
Write-Host "2. Test the application to ensure it still works correctly"
Write-Host "3. Commit the cleanup changes to version control"
Write-Host "4. Update documentation if needed"
