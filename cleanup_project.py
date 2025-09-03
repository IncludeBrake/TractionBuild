#!/usr/bin/env python3
"""
tractionbuild Project Cleanup Script
=================================

This script performs comprehensive cleanup of the tractionbuild project:
- Removes temporary files and build artifacts
- Cleans up test outputs and logs
- Organizes project structure
- Validates dependencies
- Generates project health report

Usage:
    python cleanup_project.py [--dry-run] [--verbose] [--force]
"""

import os
import sys
import shutil
import json
import glob
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Set
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cleanup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class tractionbuildCleanup:
    """Comprehensive cleanup utility for tractionbuild project."""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False, force: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.force = force
        self.project_root = Path.cwd()
        self.cleanup_report = {
            "timestamp": datetime.now().isoformat(),
            "files_removed": [],
            "directories_removed": [],
            "files_organized": [],
            "errors": [],
            "warnings": [],
            "summary": {}
        }
        
        # Define cleanup patterns
        self.temp_patterns = [
            "__pycache__",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            "*.so",
            "*.dll",
            "*.dylib",
            "*.log",
            "*.tmp",
            "*.bak",
            "*.swp",
            "*.swo",
            "*~",
            ".DS_Store",
            "Thumbs.db"
        ]
        
        self.test_artifacts = [
            "output/test_results/*",
            "output/logs/*",
            "output/crewai_memory/*",
            "output/workflows/*",
            "output/diagrams/*",
            "*.coverage",
            "htmlcov/",
            ".pytest_cache/",
            ".coverage",
            "coverage.xml"
        ]
        
        self.build_artifacts = [
            "build/",
            "dist/",
            "*.egg-info/",
            "*.egg",
            "node_modules/",
            ".venv/",
            "venv/"
        ]
        
        self.temp_files = [
            "test_*.py",  # Root level test files
            "test_neo4j_connection.py",
            "test_advisory_board.py", 
            "test_state_fix.py",
            "test_docker.ps1",
            "test_docker.sh",
            "tractionbuild-job.yaml",
            "service.yaml",
            "deployment.yaml"
        ]

    def log_action(self, action: str, path: str, success: bool = True, error: str = None):
        """Log cleanup actions."""
        if self.verbose:
            if success:
                logger.info(f"{action}: {path}")
            else:
                logger.error(f"Failed {action}: {path} - {error}")
        
        if not success and error:
            self.cleanup_report["errors"].append(f"{action}: {path} - {error}")

    def remove_file(self, file_path: Path) -> bool:
        """Remove a single file."""
        try:
            if file_path.exists():
                if not self.dry_run:
                    file_path.unlink()
                self.cleanup_report["files_removed"].append(str(file_path))
                self.log_action("REMOVED FILE", str(file_path))
                return True
        except Exception as e:
            self.log_action("REMOVE FILE", str(file_path), False, str(e))
            return False
        return False

    def remove_directory(self, dir_path: Path) -> bool:
        """Remove a directory and its contents."""
        try:
            if dir_path.exists() and dir_path.is_dir():
                if not self.dry_run:
                    shutil.rmtree(dir_path)
                self.cleanup_report["directories_removed"].append(str(dir_path))
                self.log_action("REMOVED DIRECTORY", str(dir_path))
                return True
        except Exception as e:
            self.log_action("REMOVE DIRECTORY", str(dir_path), False, str(e))
            return False
        return False

    def clean_temp_files(self):
        """Remove temporary files and directories."""
        logger.info("Cleaning temporary files...")
        
        for pattern in self.temp_patterns:
            for file_path in self.project_root.rglob(pattern):
                if file_path.is_file():
                    self.remove_file(file_path)
                elif file_path.is_dir():
                    self.remove_directory(file_path)

    def clean_test_artifacts(self):
        """Clean up test artifacts and outputs."""
        logger.info("Cleaning test artifacts...")
        
        for pattern in self.test_artifacts:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    self.remove_file(file_path)
                elif file_path.is_dir():
                    self.remove_directory(file_path)

    def clean_build_artifacts(self):
        """Clean up build artifacts."""
        logger.info("Cleaning build artifacts...")
        
        for pattern in self.build_artifacts:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    self.remove_file(file_path)
                elif file_path.is_dir():
                    self.remove_directory(file_path)

    def clean_temp_test_files(self):
        """Clean up temporary test files in root directory."""
        logger.info("Cleaning temporary test files...")
        
        for pattern in self.temp_files:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    self.remove_file(file_path)

    def organize_output_directory(self):
        """Organize the output directory structure."""
        logger.info("Organizing output directory...")
        
        output_dir = self.project_root / "output"
        if not output_dir.exists():
            return
        
        # Create organized structure
        organized_dirs = [
            "output/projects",
            "output/logs",
            "output/test_results", 
            "output/diagrams",
            "output/workflows",
            "output/crewai_memory"
        ]
        
        for dir_path in organized_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                if not self.dry_run:
                    full_path.mkdir(parents=True, exist_ok=True)
                self.log_action("CREATED DIRECTORY", str(full_path))

    def validate_dependencies(self):
        """Validate project dependencies."""
        logger.info("Validating dependencies...")
        
        try:
            # Check if virtual environment is active
            if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
                self.cleanup_report["warnings"].append("Virtual environment not detected")
            
            # Check key dependencies
            key_deps = [
                "crewai",
                "streamlit", 
                "openai",
                "pydantic",
                "fastapi",
                "uvicorn"
            ]
            
            missing_deps = []
            for dep in key_deps:
                try:
                    __import__(dep)
                except ImportError:
                    missing_deps.append(dep)
            
            if missing_deps:
                self.cleanup_report["warnings"].append(f"Missing dependencies: {', '.join(missing_deps)}")
            else:
                logger.info("All key dependencies are available")
                
        except Exception as e:
            self.cleanup_report["errors"].append(f"Dependency validation failed: {str(e)}")

    def check_project_structure(self):
        """Validate project structure integrity."""
        logger.info("Checking project structure...")
        
        required_dirs = [
            "src/tractionbuild",
            "src/tractionbuild/agents",
            "src/tractionbuild/crews", 
            "src/tractionbuild/tools",
            "src/tractionbuild/core",
            "tests",
            "docs",
            "config"
        ]
        
        missing_dirs = []
        for dir_path in required_dirs:
            if not (self.project_root / dir_path).exists():
                missing_dirs.append(dir_path)
        
        if missing_dirs:
            self.cleanup_report["warnings"].append(f"Missing directories: {', '.join(missing_dirs)}")
        else:
            logger.info("Project structure is intact")

    def generate_health_report(self):
        """Generate project health report."""
        logger.info("Generating health report...")
        
        # Count files by type
        file_counts = {
            "python_files": len(list(self.project_root.rglob("*.py"))),
            "test_files": len(list(self.project_root.rglob("test_*.py"))),
            "config_files": len(list(self.project_root.rglob("*.yaml")) + list(self.project_root.rglob("*.yml"))),
            "markdown_files": len(list(self.project_root.rglob("*.md"))),
            "json_files": len(list(self.project_root.rglob("*.json")))
        }
        
        # Calculate cleanup summary
        total_files_removed = len(self.cleanup_report["files_removed"])
        total_dirs_removed = len(self.cleanup_report["directories_removed"])
        total_errors = len(self.cleanup_report["errors"])
        total_warnings = len(self.cleanup_report["warnings"])
        
        self.cleanup_report["summary"] = {
            "file_counts": file_counts,
            "total_files_removed": total_files_removed,
            "total_directories_removed": total_dirs_removed,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "cleanup_success": total_errors == 0
        }
        
        logger.info(f"Cleanup Summary:")
        logger.info(f"  Files removed: {total_files_removed}")
        logger.info(f"  Directories removed: {total_dirs_removed}")
        logger.info(f"  Errors: {total_errors}")
        logger.info(f"  Warnings: {total_warnings}")

    def save_report(self):
        """Save cleanup report to file."""
        report_file = self.project_root / "cleanup_report.json"
        
        if not self.dry_run:
            with open(report_file, 'w') as f:
                json.dump(self.cleanup_report, f, indent=2)
            logger.info(f"Cleanup report saved to: {report_file}")
        else:
            logger.info("DRY RUN: Would save cleanup report")

    def run_cleanup(self):
        """Run the complete cleanup process."""
        logger.info("Starting tractionbuild project cleanup...")
        logger.info(f"Project root: {self.project_root}")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info(f"Verbose: {self.verbose}")
        
        try:
            # Perform cleanup tasks
            self.clean_temp_files()
            self.clean_test_artifacts()
            self.clean_build_artifacts()
            self.clean_temp_test_files()
            self.organize_output_directory()
            
            # Validation tasks
            self.validate_dependencies()
            self.check_project_structure()
            
            # Generate report
            self.generate_health_report()
            self.save_report()
            
            logger.info("Cleanup completed successfully!")
            
            if self.cleanup_report["summary"]["total_errors"] > 0:
                logger.warning("Cleanup completed with errors. Check the report for details.")
                return False
            else:
                return True
                
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            self.cleanup_report["errors"].append(f"Cleanup failed: {str(e)}")
            return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="tractionbuild Project Cleanup Script")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be cleaned without actually doing it")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--force", action="store_true", help="Force cleanup without confirmation")
    
    args = parser.parse_args()
    
    if not args.force and not args.dry_run:
        response = input("This will clean up temporary files and test artifacts. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Cleanup cancelled.")
            return
    
    cleanup = tractionbuildCleanup(
        dry_run=args.dry_run,
        verbose=args.verbose,
        force=args.force
    )
    
    success = cleanup.run_cleanup()
    
    if success:
        print("\n✅ Cleanup completed successfully!")
        print("📊 Check cleanup_report.json for detailed results.")
    else:
        print("\n❌ Cleanup completed with errors.")
        print("📊 Check cleanup_report.json for error details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
