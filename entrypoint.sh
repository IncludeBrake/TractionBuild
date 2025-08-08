#!/bin/bash
set -e

echo "🚀 Starting ZeroToShip container..."

# Check if required arguments are provided
if [ -z "$IDEA" ] && [ -z "$WORKFLOW" ]; then
    echo "Using default arguments from CMD"
else
    echo "Using environment variables: IDEA=$IDEA, WORKFLOW=$WORKFLOW"
fi

# Activate virtual environment
source /app/.venv/bin/activate

# Check if config files exist
if [ ! -f "/app/config/workflows.yaml" ]; then
    echo "❌ Error: workflows.yaml not found in /app/config/"
    exit 1
fi

if [ ! -f "/app/config/agents.yaml" ]; then
    echo "❌ Error: agents.yaml not found in /app/config/"
    exit 1
fi

echo "✅ Configuration files found"

# Create output directories if they don't exist
mkdir -p /app/output/logs
mkdir -p /app/output/diagrams
mkdir -p /app/data
mkdir -p /app/output/crewai_memory

# Set proper permissions
chown -R zerotoship:zerotoship /app/output /app/data

# Set environment variables for CrewAI memory
export HOME="/app"
export CREWAI_MEMORY_PATH="/app/output/crewai_memory"

# Set Neo4j URI for Docker compatibility
if [ -z "$NEO4J_URI" ]; then
    export NEO4J_URI="neo4j://host.docker.internal:7687"
fi

# Run the application with error handling
echo "🎯 Executing ZeroToShip..."
if [ -n "$IDEA" ] && [ -n "$WORKFLOW" ]; then
    python main.py --idea "$IDEA" --workflow "$WORKFLOW"
else
    # Use the default CMD arguments
    exec "$@"
fi
