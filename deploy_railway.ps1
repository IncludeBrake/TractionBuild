# Railway Deployment Script for TractionBuild
# This script helps deploy TractionBuild to Railway

param(
    [switch]$Init,
    [switch]$Deploy,
    [switch]$SetupDatabase,
    [switch]$Test
)

    Write-Host "TractionBuild Railway Deployment" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Cyan

function Initialize-Railway {
    Write-Host "Initializing Railway project..." -ForegroundColor Blue

    # Check if Railway CLI is installed
    try {
        $railwayVersion = railway --version 2>$null
        Write-Host "Railway CLI found: $railwayVersion" -ForegroundColor Green
    } catch {
        Write-Host "Railway CLI not found. Installing..." -ForegroundColor Yellow
        npm install -g @railway/cli
    }

    # Login to Railway
    Write-Host "Logging into Railway..." -ForegroundColor Blue
    railway login

    # Initialize project
    Write-Host "Creating Railway project..." -ForegroundColor Blue
    railway init tractionbuild

    # Set up environment
    Write-Host "Setting up production environment..." -ForegroundColor Blue
    railway environment production

    # Add Neo4j service
    Write-Host "Adding Neo4j database..." -ForegroundColor Blue
    railway add neo4j

    # Add Redis (optional)
    Write-Host "Adding Redis (optional caching)..." -ForegroundColor Blue
    railway add redis
}

function Deploy-Application {
    Write-Host "Deploying TractionBuild application..." -ForegroundColor Blue

    # Set environment variables
    Write-Host "Configuring environment variables..." -ForegroundColor Blue

    $envVars = @(
        "OPENAI_API_KEY",
        "XAI_API_KEY",
        "ENVIRONMENT=production",
        "DEBUG=false",
        "LOG_LEVEL=INFO",
        "PROJECT_NAME=tractionbuild"
    )

    foreach ($envVar in $envVars) {
        if ($envVar -like "*=") {
            $key, $value = $envVar -split "=", 2
            railway variables set $key $value
        } else {
            # Prompt for API keys
            $value = Read-Host "Enter $envVar"
            railway variables set $envVar $value
        }
    }

    # Deploy
    Write-Host "Starting deployment..." -ForegroundColor Green
    railway up

    # Get deployment URL
    Write-Host "Getting deployment URL..." -ForegroundColor Blue
    $deploymentUrl = railway domain
    Write-Host "Deployment complete!" -ForegroundColor Green
    Write-Host "Application URL: $deploymentUrl" -ForegroundColor Cyan
    Write-Host "API Health Check: $deploymentUrl/health" -ForegroundColor Cyan
}

function Setup-Database {
    Write-Host "Setting up Neo4j database..." -ForegroundColor Blue

    # Get database credentials from Railway
    Write-Host "Getting database credentials..." -ForegroundColor Blue

    try {
        $neo4jUrl = railway variables get NEO4J_URL
        $neo4jUser = railway variables get NEO4J_USER
        $neo4jPassword = railway variables get NEO4J_PASSWORD

        Write-Host "✅ Database configured:" -ForegroundColor Green
        Write-Host "  URL: $neo4jUrl" -ForegroundColor Gray
        Write-Host "  User: $neo4jUser" -ForegroundColor Gray
        Write-Host "  Password: [HIDDEN]" -ForegroundColor Gray

    } catch {
        Write-Host "❌ Failed to get database credentials" -ForegroundColor Red
        Write-Host "Make sure Neo4j service is added to your Railway project" -ForegroundColor Yellow
    }
}

function Test-Deployment {
    Write-Host "Testing deployment..." -ForegroundColor Blue

    # Get deployment URL
    try {
        $deploymentUrl = railway domain
        Write-Host "Testing deployment at: $deploymentUrl" -ForegroundColor Cyan

        # Test health endpoint
        Write-Host "Testing health endpoint..." -ForegroundColor Blue
        $healthResponse = Invoke-RestMethod -Uri "$deploymentUrl/health" -TimeoutSec 30
        Write-Host "Health check passed!" -ForegroundColor Green
        Write-Host "System: $($healthResponse.system)" -ForegroundColor Gray
        Write-Host "Database: $($healthResponse.database)" -ForegroundColor Gray

        # Test API endpoints
        Write-Host "Testing API endpoints..." -ForegroundColor Blue
        $apiResponse = Invoke-WebRequest -Uri "$deploymentUrl/docs" -TimeoutSec 30
        Write-Host "API documentation accessible" -ForegroundColor Green

    } catch {
        Write-Host "Deployment test failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Check Railway logs: railway logs" -ForegroundColor Yellow
    }
}

# Main execution
if ($Init) {
    Initialize-Railway
} elseif ($Deploy) {
    Deploy-Application
} elseif ($SetupDatabase) {
    Setup-Database
} elseif ($Test) {
    Test-Deployment
} else {
    # Show usage
    Write-Host "TractionBuild Railway Deployment Script" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor White
    Write-Host "  .\deploy_railway.ps1 -Init           # Initialize Railway project"
    Write-Host "  .\deploy_railway.ps1 -Deploy         # Deploy application"
    Write-Host "  .\deploy_railway.ps1 -SetupDatabase  # Setup Neo4j database"
    Write-Host "  .\deploy_railway.ps1 -Test           # Test deployment"
    Write-Host ""
    Write-Host "Complete deployment flow:" -ForegroundColor Yellow
    Write-Host "  1. .\deploy_railway.ps1 -Init"
    Write-Host "  2. .\deploy_railway.ps1 -SetupDatabase"
    Write-Host "  3. .\deploy_railway.ps1 -Deploy"
    Write-Host "  4. .\deploy_railway.ps1 -Test"
    Write-Host ""
    Write-Host "Prerequisites:" -ForegroundColor Cyan
    Write-Host "  • Railway CLI: npm install -g @railway/cli"
    Write-Host "  • Railway account: https://railway.app"
    Write-Host "  • API Keys: OpenAI and xAI"
}
