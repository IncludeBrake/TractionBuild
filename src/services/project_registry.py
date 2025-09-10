from typing import Dict, Any, List
from src.core.types import CrewResult
from src.services.artifact_store import ArtifactStore
import json
from pathlib import Path
from datetime import datetime

class ProjectRegistry:
    def __init__(self, base_path: str = "runs"):
        self.base_path = Path(base_path)
        self.store = ArtifactStore(base_path)

    def create_project(self, project_id: str, idea_text: str):
        registry_path = self.base_path / project_id / "registry.json"
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "project_id": project_id,
            "idea": idea_text,
            "crews": [],
            "states": ["IDEA_VALIDATION"],
            "updated_at": datetime.utcnow().isoformat()
        }
        with registry_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def append_crew_result(self, project_id: str, result: CrewResult):
        registry_path = self.base_path / project_id / "registry.json"

        # Load existing data or create new
        if registry_path.exists():
            with registry_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {
                "project_id": project_id,
                "crews": [],
                "states": ["IDEA_VALIDATION"]
            }

        # Save artifacts and get paths
        artifact_paths = self.store.save_artifacts(project_id, result)

        # Append crew result
        crew_entry = {
            "crew_name": result.crew_name,
            "ok": result.ok,
            "summary": result.summary,
            "artifact_paths": artifact_paths,
            "stats": result.stats,
            "warnings": result.warnings,
            "errors": result.errors,
            "timestamp": datetime.utcnow().isoformat()
        }

        data["crews"].append(crew_entry)
        data["updated_at"] = datetime.utcnow().isoformat()

        # Save updated registry
        with registry_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_project_data(self, project_id: str) -> Dict[str, Any]:
        """Get project data from registry."""
        registry_path = self.base_path / project_id / "registry.json"

        if not registry_path.exists():
            return {"project_id": project_id, "crews": [], "states": ["IDEA_VALIDATION"]}

        try:
            with registry_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"project_id": project_id, "crews": [], "states": ["IDEA_VALIDATION"]}

    def get_crew_results(self, project_id: str, crew_name: str = None) -> List[Dict[str, Any]]:
        """Get crew results for a project, optionally filtered by crew name."""
        data = self.get_project_data(project_id)
        crews = data.get("crews", [])

        if crew_name:
            return [crew for crew in crews if crew.get("crew_name") == crew_name]
        else:
            return crews
