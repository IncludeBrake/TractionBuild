#!/usr/bin/env python3
"""
Environment setup script for ZeroToShip tool ecosystem.
Automates the setup of all dependencies and infrastructure.
"""

import os
import sys
import subprocess
import json
import platform
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnvironmentSetup:
    """Handles the complete environment setup for ZeroToShip."""
    
    def __init__(self):
        """Initialize the setup process."""
        self.project_root = Path(__file__).parent.parent
        self.is_windows = platform.system() == "Windows"
        self.is_mac = platform.system() == "Darwin"
        self.is_linux = platform.system() == "Linux"
        
    def run_command(self, command: str, check: bool = True) -> bool:
        """Run a shell command and handle errors."""
        try:
            logger.info(f"Running: {command}")
            result = subprocess.run(
                command,
                shell=True,
                check=check,
                capture_output=True,
                text=True
            )
            if result.stdout:
                logger.info(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            if e.stderr:
                logger.error(f"Error output: {e.stderr}")
            return False
    
    def check_docker(self) -> bool:
        """Check if Docker is installed and running."""
        logger.info("Checking Docker installation...")
        
        if not self.run_command("docker --version", check=False):
            logger.error("Docker is not installed. Please install Docker first.")
            logger.info("Visit: https://docs.docker.com/get-docker/")
            return False
        
        if not self.run_command("docker ps", check=False):
            logger.error("Docker is not running. Please start Docker.")
            return False
        
        logger.info("✅ Docker is installed and running")
        return True
    
    def setup_docker_services(self) -> bool:
        """Set up Docker services (Redis, Ollama)."""
        logger.info("Setting up Docker services...")
        
        # Stop existing containers
        self.run_command("docker stop zerotoship-redis zerotoship-ollama 2>/dev/null || true", check=False)
        self.run_command("docker rm zerotoship-redis zerotoship-ollama 2>/dev/null || true", check=False)
        
        # Start Redis
        if not self.run_command(
            "docker run -d -p 6379:6379 --name zerotoship-redis redis:latest"
        ):
            logger.error("Failed to start Redis container")
            return False
        
        # Start Ollama
        if not self.run_command(
            "docker run -d -v ollama:/root/.ollama -p 11434:11434 --name zerotoship-ollama ollama/ollama:latest"
        ):
            logger.error("Failed to start Ollama container")
            return False
        
        # Wait for Ollama to be ready
        logger.info("Waiting for Ollama to be ready...")
        import time
        time.sleep(10)
        
        # Pull Llama 3.1 model
        logger.info("Pulling Llama 3.1 8B model...")
        if not self.run_command("docker exec -it zerotoship-ollama ollama pull llama3.1:8b"):
            logger.warning("Failed to pull Llama model. You can do this manually later.")
        
        logger.info("✅ Docker services are running")
        return True
    
    def create_env_file(self) -> bool:
        """Create .env file with default configuration."""
        logger.info("Creating .env file...")
        
        env_content = """# ZeroToShip Environment Configuration

# API Keys
OPENAI_API_KEY="your_openai_api_key_here"
X_API_KEY="your_x_api_key_here"
X_API_SECRET="your_x_api_secret_here"
X_BEARER_TOKEN="your_x_bearer_token_here"

# Infrastructure URLs
REDIS_URL="redis://localhost:6379/0"
OLLAMA_URL="http://localhost:11434"

# Model Paths
ANOMALY_MODEL_PATH="./models/latency_anomaly_model.h5"

# CodeCarbon Configuration
CODECARBON_MODE="offline"
CODECARBON_OUTPUT_DIR="./emissions_data"

# Logging
LOG_LEVEL="INFO"

# Development
DEBUG="true"
"""
        
        env_file = self.project_root / ".env"
        if not env_file.exists():
            with open(env_file, 'w') as f:
                f.write(env_content)
            logger.info("✅ Created .env file")
            logger.warning("⚠️  Please update the API keys in .env file")
        else:
            logger.info("✅ .env file already exists")
        
        return True
    
    def install_python_dependencies(self) -> bool:
        """Install Python dependencies using uv."""
        logger.info("Installing Python dependencies...")
        
        # Check if uv is installed
        if not self.run_command("uv --version", check=False):
            logger.info("Installing uv...")
            if self.is_windows:
                self.run_command("powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"")
            else:
                self.run_command("curl -LsSf https://astral.sh/uv/install.sh | sh")
        
        # Install dependencies
        if not self.run_command("uv pip install -e ."):
            logger.error("Failed to install Python dependencies")
            return False
        
        # Install additional dependencies for tools
        additional_deps = [
            "crewai-tools",
            "presidio-analyzer",
            "presidio-anonymizer", 
            "codecarbon",
            "nltk",
            "transformers",
            "torch",
            "unsloth",
            "datasets",
            "trl"
        ]
        
        for dep in additional_deps:
            if not self.run_command(f"uv pip install {dep}"):
                logger.warning(f"Failed to install {dep}")
        
        logger.info("✅ Python dependencies installed")
        return True
    
    def setup_nltk_data(self) -> bool:
        """Download required NLTK data."""
        logger.info("Setting up NLTK data...")
        
        try:
            import nltk
            nltk.download('punkt')
            nltk.download('averaged_perceptron_tagger')
            nltk.download('maxent_ne_chunker')
            nltk.download('words')
            logger.info("✅ NLTK data downloaded")
            return True
        except Exception as e:
            logger.error(f"Failed to download NLTK data: {e}")
            return False
    
    def create_directories(self) -> bool:
        """Create necessary directories."""
        logger.info("Creating directories...")
        
        directories = [
            "models",
            "models/fine_tuned_summarizer",
            "data",
            "emissions_data",
            "logs",
            "output",
            "output/diagrams",
            "output/logs",
            "output/workflows"
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("✅ Directories created")
        return True
    
    def run_tests(self) -> bool:
        """Run the test suite to verify installation."""
        logger.info("Running tests...")
        
        if not self.run_command("python -m pytest tests/test_tools.py -v"):
            logger.warning("Some tests failed. This might be expected if services are not fully configured.")
            return False
        
        logger.info("✅ Tests passed")
        return True
    
    def create_startup_script(self) -> bool:
        """Create startup scripts for easy launching."""
        logger.info("Creating startup scripts...")
        
        # Create startup script for Windows
        if self.is_windows:
            startup_script = """@echo off
echo Starting ZeroToShip services...

REM Start Docker services
docker start zerotoship-redis zerotoship-ollama

REM Start the API server
python -m uvicorn zerotoship.api.app:app --host 0.0.0.0 --port 8000 --reload

pause
"""
            with open(self.project_root / "start_zerotoship.bat", 'w') as f:
                f.write(startup_script)
        
        # Create startup script for Unix-like systems
        else:
            startup_script = """#!/bin/bash
echo "Starting ZeroToShip services..."

# Start Docker services
docker start zerotoship-redis zerotoship-ollama

# Start the API server
python -m uvicorn zerotoship.api.app:app --host 0.0.0.0 --port 8000 --reload
"""
            startup_file = self.project_root / "start_zerotoship.sh"
            with open(startup_file, 'w') as f:
                f.write(startup_script)
            
            # Make executable
            os.chmod(startup_file, 0o755)
        
        logger.info("✅ Startup scripts created")
        return True
    
    def print_next_steps(self):
        """Print next steps for the user."""
        logger.info("\n" + "="*60)
        logger.info("🎉 ZeroToShip Environment Setup Complete!")
        logger.info("="*60)
        
        logger.info("\n📋 Next Steps:")
        logger.info("1. Update API keys in .env file")
        logger.info("2. Start services: ./start_zerotoship.sh (or .bat on Windows)")
        logger.info("3. Test the chat UI: streamlit run chat_ui.py")
        logger.info("4. Run fine-tuning: python scripts/fine_tune_summarizer.py")
        
        logger.info("\n🔧 Available Tools:")
        logger.info("- SummarizationTool: Cost-effective text summarization")
        logger.info("- ComplianceCheckerTool: GDPR compliance and PII anonymization")
        logger.info("- SustainabilityTrackerTool: Carbon footprint tracking")
        logger.info("- CeleryExecutionTool: Distributed task execution")
        logger.info("- XSemanticSearchTool: Social media insights")
        logger.info("- MarketOracleTool: Real-time market data")
        
        logger.info("\n📚 Documentation:")
        logger.info("- Main guide: docs/ADVISORY_BOARD_GUIDE.md")
        logger.info("- API docs: docs/API_GUIDE.md")
        logger.info("- Troubleshooting: Check the logs in logs/ directory")
        
        logger.info("\n🚀 Happy building with ZeroToShip!")
    
    def setup(self) -> bool:
        """Run the complete setup process."""
        logger.info("🚀 Starting ZeroToShip Environment Setup")
        logger.info("="*50)
        
        steps = [
            ("Checking Docker", self.check_docker),
            ("Setting up Docker services", self.setup_docker_services),
            ("Creating .env file", self.create_env_file),
            ("Installing Python dependencies", self.install_python_dependencies),
            ("Setting up NLTK data", self.setup_nltk_data),
            ("Creating directories", self.create_directories),
            ("Creating startup scripts", self.create_startup_script),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n📦 {step_name}...")
            if not step_func():
                logger.error(f"❌ {step_name} failed")
                return False
        
        # Run tests (optional)
        logger.info("\n🧪 Running tests...")
        self.run_tests()
        
        # Print next steps
        self.print_next_steps()
        
        return True

def main():
    """Main function."""
    setup = EnvironmentSetup()
    success = setup.setup()
    
    if success:
        logger.info("\n✅ Setup completed successfully!")
        sys.exit(0)
    else:
        logger.error("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
