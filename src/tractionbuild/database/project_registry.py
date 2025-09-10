import logging
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ProjectRegistry:
    def __init__(self, neo4j_uri: str, neo4j_user: str = "neo4j"):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.storage_path = Path("runs")
        self.storage_path.mkdir(exist_ok=True)
        logger.info(f"ProjectRegistry initialized with URI: {neo4j_uri}")

    async def __aenter__(self):
        logger.info("ProjectRegistry context manager entered")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        logger.info("ProjectRegistry context manager exited")

    async def save_project_state(self, project_data: Dict[str, Any]) -> None:
        """Save project state to file-based storage."""
        project_id = project_data.get('id', 'unknown')
        logger.info(f"Saving project state for {project_id}")

        try:
            # Create project directory
            project_dir = self.storage_path / project_id
            project_dir.mkdir(exist_ok=True)

            # Save project data
            project_file = project_dir / "project.json"
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, default=str)

            # Save artifacts separately if they exist
            if 'artifacts' in project_data and project_data['artifacts']:
                artifacts_file = project_dir / "artifacts.json"
                with open(artifacts_file, 'w', encoding='utf-8') as f:
                    json.dump(project_data['artifacts'], f, indent=2, default=str)

            # Save events log
            events_file = project_dir / "events.jsonl"
            timestamp = datetime.utcnow().isoformat()

            event_data = {
                'timestamp': timestamp,
                'event_type': 'state_saved',
                'project_id': project_id,
                'state': project_data.get('state'),
                'artifacts_count': len(project_data.get('artifacts', {}))
            }

            with open(events_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event_data, default=str) + '\n')

            logger.info(f"Successfully saved project state for {project_id}")

        except Exception as e:
            logger.error(f"Failed to save project state for {project_id}: {e}")
            raise

    async def load_project_state(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Load project state from storage."""
        try:
            project_file = self.storage_path / project_id / "project.json"
            if project_file.exists():
                with open(project_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"Failed to load project state for {project_id}: {e}")
            return None

    async def rollback_state(self, project_id: str) -> None:
        """Rollback project state (mock implementation)."""
        logger.warning(f"Rollback requested for {project_id} - not implemented yet")
        # TODO: Implement rollback logic
        pass