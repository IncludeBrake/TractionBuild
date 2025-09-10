"""
Project registry service for TractionBuild.
Maintains structured project state and crew execution history.
"""

import json
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from filelock import FileLock

from ..core.types import CrewResult

class ProjectRegistry:
    """Thread-safe project registry with structured state management."""

    def __init__(self, base_path: Path = None):
        self.base_path = base_path or Path("runs")
        self._locks: Dict[str, FileLock] = {}
        self._lock = threading.Lock()

    def _get_registry_path(self, project_id: str) -> Path:
        """Get the registry file path for a project."""
        return self.base_path / project_id / "registry.json"

    def _get_lock(self, project_id: str) -> FileLock:
        """Get or create a file lock for a project."""
        with self._lock:
            if project_id not in self._locks:
                registry_path = self._get_registry_path(project_id)
                registry_path.parent.mkdir(parents=True, exist_ok=True)
                self._locks[project_id] = FileLock(str(registry_path) + ".lock")
            return self._locks[project_id]

    def _load_registry(self, project_id: str) -> Dict[str, Any]:
        """Load project registry from disk."""
        registry_path = self._get_registry_path(project_id)

        if not registry_path.exists():
            # Initialize empty registry
            return {
                "project": {"id": project_id},
                "states": [],
                "crews": {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # Return fresh registry if corrupted
            return {
                "project": {"id": project_id},
                "states": [],
                "crews": {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

    def _save_registry(self, project_id: str, registry: Dict[str, Any]) -> None:
        """Save project registry to disk atomically."""
        registry_path = self._get_registry_path(project_id)
        registry["updated_at"] = datetime.now().isoformat()

        # Write to temporary file first
        temp_path = registry_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(registry, f, indent=2, default=str)
                f.flush()

            # Atomic rename
            temp_path.replace(registry_path)
        except Exception:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise

    def initialize_project(self, project_id: str, project_data: Dict[str, Any]) -> None:
        """Initialize a new project in the registry."""
        lock = self._get_lock(project_id)

        with lock:
            registry = self._load_registry(project_id)
            registry["project"] = project_data
            registry["states"] = [project_data.get("state", "START")]
            registry["created_at"] = datetime.now().isoformat()
            self._save_registry(project_id, registry)

    def update_project_state(self, project_id: str, new_state: str) -> None:
        """Update the current state of a project."""
        lock = self._get_lock(project_id)

        with lock:
            registry = self._load_registry(project_id)

            # Add new state to history if different from last
            if not registry["states"] or registry["states"][-1] != new_state:
                registry["states"].append(new_state)

            # Update project state
            registry["project"]["state"] = new_state
            self._save_registry(project_id, registry)

    def append_crew_result(self, project_id: str, result: CrewResult) -> None:
        """Append a crew execution result to the project registry."""
        lock = self._get_lock(project_id)

        with lock:
            registry = self._load_registry(project_id)

            # Initialize crew entry if not exists
            if result.crew_name not in registry["crews"]:
                registry["crews"][result.crew_name] = []

            # Create crew run entry
            run_entry = {
                "id": f"{result.crew_name}_{len(registry['crews'][result.crew_name])}",
                "summary": result.summary,
                "ok": result.ok,
                "artifacts": [
                    {
                        "id": art.id,
                        "type": art.type,
                        "path": f"artifacts/{result.crew_name}/{art.id}.{self._get_extension(art.type)}"
                    }
                    for art in result.artifacts
                ],
                "stats": result.stats,
                "warnings": result.warnings,
                "errors": result.errors,
                "ts": datetime.now().isoformat()
            }

            registry["crews"][result.crew_name].append(run_entry)
            self._save_registry(project_id, registry)

    def _get_extension(self, artifact_type: str) -> str:
        """Get file extension for artifact type."""
        ext_map = {
            "text": "txt",
            "json": "json",
            "markdown": "md",
            "file": "bin",
            "image": "png",
            "log": "log"
        }
        return ext_map.get(artifact_type, "bin")

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project data from registry."""
        lock = self._get_lock(project_id)

        with lock:
            registry = self._load_registry(project_id)
            return registry.get("project")

    def get_crew_history(self, project_id: str, crew_name: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get crew execution history for a project."""
        lock = self._get_lock(project_id)

        with lock:
            registry = self._load_registry(project_id)

            if crew_name:
                return {crew_name: registry["crews"].get(crew_name, [])}
            else:
                return registry["crews"].copy()

    def get_project_states(self, project_id: str) -> List[str]:
        """Get the state history for a project."""
        lock = self._get_lock(project_id)

        with lock:
            registry = self._load_registry(project_id)
            return registry["states"].copy()

    def get_project_summary(self, project_id: str) -> Dict[str, Any]:
        """Get a summary of project status and recent activity."""
        lock = self._get_lock(project_id)

        with lock:
            registry = self._load_registry(project_id)

            # Count artifacts across all crews
            total_artifacts = 0
            latest_runs = {}

            for crew_name, runs in registry["crews"].items():
                if runs:
                    latest_runs[crew_name] = runs[-1]  # Most recent run
                    total_artifacts += len(runs[-1]["artifacts"])

            return {
                "project_id": project_id,
                "current_state": registry["states"][-1] if registry["states"] else "UNKNOWN",
                "total_states": len(registry["states"]),
                "crews_executed": list(registry["crews"].keys()),
                "total_artifacts": total_artifacts,
                "latest_runs": latest_runs,
                "created_at": registry["created_at"],
                "updated_at": registry["updated_at"]
            }

    def cleanup_old_runs(self, project_id: str, keep_last: int = 5) -> int:
        """Clean up old crew runs, keeping only the most recent N runs per crew."""
        lock = self._get_lock(project_id)

        with lock:
            registry = self._load_registry(project_id)
            cleaned_count = 0

            for crew_name, runs in registry["crews"].items():
                if len(runs) > keep_last:
                    # Keep only the last N runs
                    registry["crews"][crew_name] = runs[-keep_last:]
                    cleaned_count += len(runs) - keep_last

            if cleaned_count > 0:
                self._save_registry(project_id, registry)

            return cleaned_count
