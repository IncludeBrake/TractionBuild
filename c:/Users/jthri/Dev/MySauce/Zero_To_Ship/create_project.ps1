# PowerShell script to create a ZeroToShip project
# Usage: .\create_project.ps1

param(
    [string]$Name = "chat-session-$(Get-Date -Format 'yyyyMMdd-HHmmss')",
    [string]$Description = "From chat_ui",
    [string]$Hypothesis = "AI team for solopreneurs",
    [string[]]$TargetAvatars = @("startup_entrepreneur"),
    [string]$Workflow = "validation_and_launch"
)

# API Configuration
$API_BASE = "http://localhost:8000"

# Create request body
$body = @{
    name = $Name
    description = $Description
    hypothesis = $Hypothesis
    target_avatars = $TargetAvatars
    workflow = $Workflow
} | ConvertTo-Json -Depth 5

Write-Host "🚀 Creating ZeroToShip project..." -ForegroundColor Green
Write-Host "Name: $Name" -ForegroundColor Yellow
Write-Host "Description: $Description" -ForegroundColor Yellow
Write-Host "Hypothesis: $Hypothesis" -ForegroundColor Yellow
Write-Host "Target Avatars: $($TargetAvatars -join ', ')" -ForegroundColor Yellow
Write-Host ""

try {
    # Create project
    $response = Invoke-RestMethod -Uri "$API_BASE/api/v1/projects" -Method Post -ContentType 'application/json' -Body $body
    $projectId = $response.project_id
    
    Write-Host "✅ Project created successfully!" -ForegroundColor Green
    Write-Host "Project ID: $projectId" -ForegroundColor Cyan
    Write-Host ""
    
    # Check initial status
    Write-Host "📊 Checking project status..." -ForegroundColor Blue
    $status = Invoke-RestMethod -Uri "$API_BASE/api/v1/projects/$projectId/status" -Method Get
    Write-Host "Status: $($status.state)" -ForegroundColor Yellow
    Write-Host "Progress: $($status.progress)%" -ForegroundColor Yellow
    Write-Host ""
    
    # Monitor progress
    Write-Host "🔄 Monitoring progress..." -ForegroundColor Blue
    $maxWait = 60  # 60 seconds timeout
    $startTime = Get-Date
    
    while (((Get-Date) - $startTime).TotalSeconds -lt $maxWait) {
        Start-Sleep -Seconds 3
        
        try {
            $status = Invoke-RestMethod -Uri "$API_BASE/api/v1/projects/$projectId/status" -Method Get
            Write-Host "Status: $($status.state), Progress: $($status.progress)%" -ForegroundColor Yellow
            
            if ($status.state -eq "COMPLETED") {
                Write-Host "🎉 Project completed successfully!" -ForegroundColor Green
                break
            }
            elseif ($status.state -eq "ERROR") {
                Write-Host "❌ Project failed!" -ForegroundColor Red
                break
            }
        }
        catch {
            Write-Host "⚠️ Error checking status: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    # Get final results
    Write-Host ""
    Write-Host "📋 Getting final results..." -ForegroundColor Blue
    $project = Invoke-RestMethod -Uri "$API_BASE/api/v1/projects/$projectId" -Method Get
    
    Write-Host "✅ Final Results:" -ForegroundColor Green
    Write-Host "Project State: $($project.project.state)" -ForegroundColor Yellow
    Write-Host "Artifacts: $($project.artifacts.Keys -join ', ')" -ForegroundColor Yellow
    
    # Display artifacts
    if ($project.artifacts.validator) {
        Write-Host ""
        Write-Host "🎯 Validation Results:" -ForegroundColor Cyan
        Write-Host "Go Recommendation: $($project.artifacts.validator.go_recommendation)" -ForegroundColor Yellow
        Write-Host "Confidence: $([math]::Round($project.artifacts.validator.confidence * 100, 1))%" -ForegroundColor Yellow
    }
    
    if ($project.artifacts.advisory) {
        Write-Host ""
        Write-Host "📋 Advisory Results:" -ForegroundColor Cyan
        Write-Host "Approved: $($project.artifacts.advisory.approved)" -ForegroundColor Yellow
        Write-Host "Rationale: $($project.artifacts.advisory.rationale)" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "🔗 WebSocket URL: ws://localhost:8000/ws/projects/$projectId" -ForegroundColor Magenta
    Write-Host "📊 Status URL: $API_BASE/api/v1/projects/$projectId/status" -ForegroundColor Magenta
}
catch {
    Write-Host "❌ Error creating project: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Make sure the ZeroToShip API is running on $API_BASE" -ForegroundColor Yellow
}