#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -e

echo "🚀 Starting ZeroToShip container setup..."

# 1. Activate Python virtual environment
source /app/.venv/bin/activate

# 2. Set default environment variables for CrewAI if not already set
export HOME="/app"
export CREWAI_MEMORY_PATH="${CREWAI_MEMORY_PATH:-/app/output/crewai_memory}"

# 3. Create required directories
mkdir -p /app/output/logs /app/data "$CREWAI_MEMORY_PATH"

echo "✅ Environment setup complete."
echo "-----------------------------------------"

# 4. Execute the command passed from docker-compose.yml (CMD)
# The "$@" passes all arguments from the 'command:' directive.
exec "$@"