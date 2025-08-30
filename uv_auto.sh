#!/bin/bash

# Enhanced uv_auto.sh script with clean functionality
# Usage: ./uv_auto.sh [clean]

# Define the name for the virtual environment directory
VENV_NAME=".venv"

# Function to clean virtual environment
clean_venv() {
    if [ -d "$VENV_NAME" ]; then
        echo "🧹 Deleting the virtual environment: $VENV_NAME"
        rm -rf "$VENV_NAME"
        echo "✅ Virtual environment deleted successfully."
    else
        echo "ℹ️  No virtual environment found to delete."
    fi
}

# Check if clean command is provided
if [ "$1" = "clean" ]; then
    clean_venv
    exit 0
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed or not in PATH"
    echo "📦 Install uv with: pipx install uv"
    exit 1
fi

echo "🚀 Starting uv_auto.sh..."

# Check if the virtual environment directory exists
if [ -d "$VENV_NAME" ]; then
    echo "✅ Virtual environment already exists. Activating..."
    source "$VENV_NAME/bin/activate"
else
    echo "🔨 Virtual environment not found. Creating and activating..."
    uv venv
    source "$VENV_NAME/bin/activate"
fi

# Check for a pyproject.toml file to install dependencies
if [ -f "pyproject.toml" ]; then
    echo "📋 pyproject.toml found. Syncing dependencies with uv sync..."
    uv sync
elif [ -f "requirements.txt" ]; then
    echo "📋 requirements.txt found. Installing dependencies with uv pip install..."
    uv pip install -r requirements.txt
else
    echo "⚠️  No pyproject.toml or requirements.txt found. Skipping dependency installation."
fi

echo "✅ Setup complete! Virtual environment is active."
echo "💡 To clean the environment, run: ./uv_auto.sh clean"
echo "💡 To deactivate, run: deactivate"

# Script will continue to run in the active shell.