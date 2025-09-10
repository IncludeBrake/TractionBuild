# test_tractionbuild.ps1
# PowerShell script to test TractionBuild functionality with Salem AI

param(
    [string]$ProjectId = "",
    [switch]$CreateNew,
    [switch]$Status,
    [switch]$Health,
    [switch]$List,
    [switch]$SalemTest,
    [switch]$WorkflowTest
)

$baseUrl = "http://localhost:8000"

function Test-ServerConnection {
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/health" -TimeoutSec 5
        Write-Host "✅ Server is running" -ForegroundColor Green
        Write-Host "System: $($response.system)" -ForegroundColor Cyan
        Write-Host "Database: $($response.database)" -ForegroundColor Cyan
        return $true
    } catch {
        Write-Host "ERROR - Server is not responding. Run start_tractionbuild.ps1 first" -ForegroundColor Red
        return $false
    }
}

function New-TestProject {
    param([string]$Workflow = "default_software_build")

    $projectData = @{
        name = "Test Project $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
        description = "Automated test project to verify system functionality with Salem AI"
        hypothesis = "The TractionBuild system will execute and capture artifacts including Salem marketing assets"
        target_avatars = @("startup_entrepreneur", "tech_founder")
        workflow = $Workflow
    }

    $jsonData = $projectData | ConvertTo-Json

    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/projects" -Method Post -ContentType "application/json" -Body $jsonData
        Write-Host "✅ Project created successfully" -ForegroundColor Green
        Write-Host "Project ID: $($response.project_id)" -ForegroundColor Yellow
        Write-Host "Workflow: $Workflow" -ForegroundColor Cyan
        return $response.project_id
    } catch {
        Write-Host "ERROR - Failed to create project - $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

function New-SalemMarketingTest {
    $projectData = @{
        name = "Salem Marketing Test $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
        description = "Testing Salem AI marketing asset generation capabilities"
        hypothesis = "Salem will generate comprehensive marketing assets automatically"
        target_avatars = @("tech_startup_founder", "product_manager")
        workflow = "default_software_build"
    }

    $jsonData = $projectData | ConvertTo-Json

    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/projects" -Method Post -ContentType "application/json" -Body $jsonData
        Write-Host "🤖 Salem Marketing Test Project Created!" -ForegroundColor Magenta
        Write-Host "Project ID: $($response.project_id)" -ForegroundColor Yellow
        Write-Host "🎯 This project will test Salem AI marketing asset generation" -ForegroundColor Cyan
        return $response.project_id
    } catch {
        Write-Host "ERROR - Failed to create Salem test project - $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

function Get-ProjectStatus {
    param([string]$Id)
    
    try {
        $status = Invoke-RestMethod -Uri "$baseUrl/api/v1/projects/$Id/status"
        Write-Host "STATUS - Project Status for $Id" -ForegroundColor Blue
        Write-Host "State: $($status.state)" -ForegroundColor Cyan
        Write-Host "Progress: $($status.progress)%" -ForegroundColor Cyan
        Write-Host "Current Step: $($status.current_step)" -ForegroundColor Cyan
        Write-Host "Artifacts: $($status.artifacts_count)" -ForegroundColor Cyan
        Write-Host "Has Error: $($status.has_error)" -ForegroundColor Cyan
        return $status
    } catch {
        Write-Host "ERROR - Failed to get project status - $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

function Get-ProjectDetails {
    param([string]$Id)
    
    try {
        $project = Invoke-RestMethod -Uri "$baseUrl/api/v1/projects/$Id"
        Write-Host "DETAILS - Project Details for $Id" -ForegroundColor Blue
        Write-Host "Project Data:" -ForegroundColor Cyan
        $project.project | ConvertTo-Json -Depth 3 | Write-Host
        Write-Host "`nArtifacts:" -ForegroundColor Cyan
        $project.artifacts | ConvertTo-Json -Depth 3 | Write-Host
        if ($project.error) {
            Write-Host "`nError:" -ForegroundColor Red
            Write-Host $project.error
        }
        return $project
    } catch {
        Write-Host "ERROR - Failed to get project details - $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

function Show-RunsDirectory {
    $runsPath = "C:\Users\jthri\Dev\MySauce\TractionBuild\runs"
    if (Test-Path $runsPath) {
        Write-Host "RUNS - Runs Directory Contents:" -ForegroundColor Blue
        Get-ChildItem $runsPath | ForEach-Object {
            Write-Host "  $($_.Name)" -ForegroundColor Cyan
            if ($_.PSIsContainer) {
                $eventsFile = Join-Path $_.FullName "events.jsonl"
                if (Test-Path $eventsFile) {
                    $eventCount = (Get-Content $eventsFile | Measure-Object -Line).Lines
                    Write-Host "    --- events.jsonl ($($eventCount) events)" -ForegroundColor Gray
                }
            }
        }
    } else {
        Write-Host 'ERROR - Runs directory not found' -ForegroundColor Red
    }
}

# Main script logic
if (-not (Test-ServerConnection)) {
    exit 1
}

if ($Health) {
    # Health check already done in Test-ServerConnection
    exit 0
}

if ($SalemTest) {
    Write-Host "SALEM - Testing Salem AI Marketing Integration..." -ForegroundColor Magenta
    Write-Host "============================================" -ForegroundColor Cyan

    $salemProjectId = New-SalemMarketingTest
    if ($salemProjectId) {
        Write-Host "`nMONITOR - Monitoring Salem workflow progress..." -ForegroundColor Yellow
        Write-Host "TARGET - Salem will generate marketing assets in MARKETING_PREPARATION phase" -ForegroundColor Cyan

        # Monitor workflow progress
        for ($i = 0; $i -lt 10; $i++) {
            Start-Sleep -Seconds 10
            try {
                $statusResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/projects/$salemProjectId/status"
                Write-Host "STATUS - Project Status for $salemProjectId" -ForegroundColor Blue
                Write-Host "State: $($statusResponse.state)" -ForegroundColor Cyan
                Write-Host "Progress: $($statusResponse.progress)%" -ForegroundColor Cyan

                if ($statusResponse.state -eq "MARKETING_PREPARATION") {
                    Write-Host "SUCCESS - Salem Marketing Phase Reached!" -ForegroundColor Magenta
                    Write-Host "SALEM - Salem AI is generating marketing assets..." -ForegroundColor Cyan
                    break
                } elseif ($statusResponse.state -eq "COMPLETED") {
                    Write-Host "SUCCESS - Workflow completed! Check artifacts for Salem marketing assets." -ForegroundColor Green
                    break
                } elseif ($statusResponse.has_error) {
                    Write-Host "ERROR - Workflow encountered an error" -ForegroundColor Red
                    break
                }
            } catch {
                Write-Host "ERROR - Failed to get status - $($_.Exception.Message)" -ForegroundColor Red
                break
            }
        }
        Show-RunsDirectory
    }
    exit 0
}

if ($WorkflowTest) {
    Write-Host "WORKFLOW - Testing Complete Workflow with Salem..." -ForegroundColor Blue
    Write-Host "==========================================" -ForegroundColor Cyan

    $workflowProjectId = New-TestProject -Workflow "validation_and_launch"
    if ($workflowProjectId) {
        Write-Host "`nMONITOR - Monitoring full workflow progress..." -ForegroundColor Yellow
        Write-Host "PHASES - Phases: IDEA_VALIDATION -> TASK_EXECUTION -> MARKETING_PREPARATION -> FEEDBACK_COLLECTION" -ForegroundColor Cyan

        # Monitor full workflow
        $lastState = ""
        for ($i = 0; $i -lt 20; $i++) {
            Start-Sleep -Seconds 15
            $status = Get-ProjectStatus -Id $workflowProjectId
            if ($status) {
                if ($status.state -ne $lastState) {
                    Write-Host "ADVANCE - Advanced to: $($status.state) ($($status.progress)% complete)" -ForegroundColor Yellow
                    $lastState = $status.state
                }

                if ($status.state -eq "COMPLETED") {
                    Write-Host "SUCCESS - Full workflow completed successfully!" -ForegroundColor Green
                    Write-Host "STATUS - Final status: $($status.progress)% complete" -ForegroundColor Cyan
                    break
                } elseif ($status.has_error) {
                    Write-Host "ERROR - Workflow encountered an error in $($status.state)" -ForegroundColor Red
                    break
                }
            }
        }
        Show-RunsDirectory
    }
    exit 0
}

if ($CreateNew) {
    $newProjectId = New-TestProject
    if ($newProjectId) {
        Write-Host "`nWAIT - Waiting 5 seconds for workflow to start..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        Get-ProjectStatus -Id $newProjectId
        Show-RunsDirectory
    }
    exit 0
}

if ($Status -and $ProjectId) {
    Get-ProjectStatus -Id $ProjectId
    Get-ProjectDetails -Id $ProjectId
    exit 0
}

if ($List) {
    Show-RunsDirectory
    exit 0
}

if ($ProjectId) {
    Get-ProjectDetails -Id $ProjectId
    exit 0
}

# Default: Show usage
Write-Host "🚀 TractionBuild Test Script with Salem AI" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Usage:" -ForegroundColor White
Write-Host "  .\test_tractionbuild.ps1 -Health                    # Check server health"
Write-Host "  .\test_tractionbuild.ps1 -CreateNew                 # Create new test project"
Write-Host "  .\test_tractionbuild.ps1 -SalemTest                 # Test Salem marketing integration"
Write-Host "  .\test_tractionbuild.ps1 -WorkflowTest              # Test complete workflow"
Write-Host "  .\test_tractionbuild.ps1 -ProjectId <id> -Status    # Get project status"
Write-Host "  .\test_tractionbuild.ps1 -ProjectId <id>            # Get full project details"
Write-Host "  .\test_tractionbuild.ps1 -List                      # Show runs directory"
Write-Host ""
Write-Host "SALEM - Salem AI Testing" -ForegroundColor Magenta
Write-Host "  -SalemTest: Creates project and monitors Salem marketing asset generation"
Write-Host "  -WorkflowTest: Tests full workflow including Salem MARKETING_PREPARATION phase"
Write-Host ""
Write-Host "Examples:" -ForegroundColor Yellow
Write-Host "  .\test_tractionbuild.ps1 -Health"
Write-Host "  .\test_tractionbuild.ps1 -CreateNew"
Write-Host "  .\test_tractionbuild.ps1 -SalemTest"
Write-Host "  .\test_tractionbuild.ps1 -WorkflowTest"
Write-Host "  .\test_tractionbuild.ps1 -ProjectId 57489656-8f98-4114-ac8d-4a00c6f76f76 -Status"
Write-Host ""
Write-Host "🎯 Quick Start:" -ForegroundColor Green
Write-Host "  1. .\start_tractionbuild.ps1          # Start server"
Write-Host "  2. .\test_tractionbuild.ps1 -SalemTest # Test Salem AI"
Write-Host "  3. .\test_tractionbuild.ps1 -List     # Check results"