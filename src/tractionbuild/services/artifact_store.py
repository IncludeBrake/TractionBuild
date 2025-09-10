"""
Deterministic artifact storage service for TractionBuild.
Provides atomic writes, integrity verification, and structured storage.
"""

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..core.types import Artifact, CrewResult, ArtifactType

class ArtifactStore:
    """Service for deterministic artifact storage with integrity verification."""

    def __init__(self, base_path: Path = None):
        self.base_path = base_path or Path("runs")

    def _get_artifact_path(self, project_id: str, crew_name: str, artifact_id: str, artifact_type: ArtifactType) -> Path:
        """Get the storage path for an artifact."""
        # Create directory structure
        dir_path = self.base_path / project_id / "artifacts" / crew_name
        dir_path.mkdir(parents=True, exist_ok=True)

        # Determine file extension based on type
        ext_map = {
            "text": "txt",
            "json": "json",
            "markdown": "md",
            "file": "bin",
            "image": "png",
            "log": "log"
        }
        ext = ext_map.get(artifact_type, "bin")

        return dir_path / f"{artifact_id}.{ext}"

    def _get_meta_path(self, artifact_path: Path) -> Path:
        """Get the metadata sidecar path for an artifact."""
        return artifact_path.with_suffix(f"{artifact_path.suffix}.meta.json")

    def sha256_of(self, path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        hash_sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _write_atomic(self, path: Path, data: bytes) -> None:
        """Write data atomically using temporary file."""
        # Write to temporary file first
        temp_path = path.with_suffix(f"{path.suffix}.tmp")
        try:
            with open(temp_path, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk

            # Atomic rename
            temp_path.replace(path)
        except Exception:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise

    def _write_text_atomic(self, path: Path, content: str, encoding: str = "utf-8") -> None:
        """Write text content atomically."""
        data = content.encode(encoding)
        self._write_atomic(path, data)

    def _write_json_atomic(self, path: Path, data: Dict[str, Any]) -> None:
        """Write JSON data atomically."""
        content = json.dumps(data, indent=2, default=str)
        self._write_text_atomic(path, content)

    def save_artifact(self, project_id: str, crew_name: str, artifact: Artifact) -> str:
        """Save a single artifact and return its path."""
        artifact_path = self._get_artifact_path(project_id, crew_name, artifact.id, artifact.type)
        meta_path = self._get_meta_path(artifact_path)

        # Save artifact data
        if artifact.data is not None:
            # Inline data - save as text/JSON/markdown
            if artifact.type in ["text", "markdown"]:
                self._write_text_atomic(artifact_path, str(artifact.data))
            elif artifact.type == "json":
                if isinstance(artifact.data, (dict, list)):
                    self._write_json_atomic(artifact_path, artifact.data)
                else:
                    self._write_text_atomic(artifact_path, str(artifact.data))
            else:
                # For other types, save as JSON representation
                self._write_json_atomic(artifact_path, {"data": artifact.data})
        elif artifact.path:
            # External file - copy to storage
            source_path = Path(artifact.path)
            if source_path.exists():
                with open(source_path, "rb") as src, open(artifact_path, "wb") as dst:
                    dst.write(src.read())
            else:
                raise FileNotFoundError(f"Source file not found: {artifact.path}")

        # Create metadata sidecar
        metadata = {
            "artifact_id": artifact.id,
            "type": artifact.type,
            "size": artifact_path.stat().st_size if artifact_path.exists() else 0,
            "sha256": self.sha256_of(artifact_path) if artifact_path.exists() else "",
            "created_at": datetime.now().isoformat(),
            "meta": artifact.meta
        }

        self._write_json_atomic(meta_path, metadata)

        return str(artifact_path.relative_to(self.base_path))

    def save_artifacts(self, project_id: str, result: CrewResult) -> List[str]:
        """Save all artifacts from a crew result and return their paths."""
        saved_paths = []

        for artifact in result.artifacts:
            try:
                path = self.save_artifact(project_id, result.crew_name, artifact)
                saved_paths.append(path)
            except Exception as e:
                # Log error but continue with other artifacts
                print(f"Failed to save artifact {artifact.id}: {e}")
                continue

        return saved_paths

    def load_artifact(self, project_id: str, crew_name: str, artifact_id: str) -> Optional[Artifact]:
        """Load an artifact by ID."""
        # Try different extensions
        extensions = ["txt", "json", "md", "bin", "png", "log"]

        for ext in extensions:
            artifact_path = self.base_path / project_id / "artifacts" / crew_name / f"{artifact_id}.{ext}"
            meta_path = self._get_meta_path(artifact_path)

            if artifact_path.exists() and meta_path.exists():
                # Load metadata
                with open(meta_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

                # Load artifact data
                if metadata["type"] in ["text", "markdown"]:
                    with open(artifact_path, "r", encoding="utf-8") as f:
                        data = f.read()
                elif metadata["type"] == "json":
                    with open(artifact_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                else:
                    # For binary files, store path
                    data = None

                return Artifact(
                    id=artifact_id,
                    type=metadata["type"],
                    path=str(artifact_path) if metadata["type"] in ["file", "image"] else None,
                    data=data,
                    meta=metadata.get("meta", {})
                )

        return None

    def list_artifacts(self, project_id: str, crew_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all artifacts for a project, optionally filtered by crew."""
        artifacts_dir = self.base_path / project_id / "artifacts"

        if not artifacts_dir.exists():
            return []

        artifacts = []

        if crew_name:
            crew_dirs = [artifacts_dir / crew_name]
        else:
            crew_dirs = [d for d in artifacts_dir.iterdir() if d.is_dir()]

        for crew_dir in crew_dirs:
            if not crew_dir.exists():
                continue

            for meta_file in crew_dir.glob("*.meta.json"):
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        metadata = json.load(f)

                    artifacts.append({
                        "crew_name": crew_dir.name,
                        "artifact_id": metadata["artifact_id"],
                        "type": metadata["type"],
                        "size": metadata["size"],
                        "sha256": metadata["sha256"],
                        "created_at": metadata["created_at"],
                        "path": str(meta_file.parent / f"{metadata['artifact_id']}.{metadata['type']}"),
                        "meta": metadata.get("meta", {})
                    })
                except Exception as e:
                    print(f"Failed to load metadata {meta_file}: {e}")
                    continue

        return artifacts

    def verify_integrity(self, project_id: str) -> Dict[str, Any]:
        """Verify integrity of all artifacts in a project."""
        artifacts = self.list_artifacts(project_id)
        results = {
            "total": len(artifacts),
            "verified": 0,
            "corrupted": 0,
            "missing": 0,
            "details": []
        }

        for art in artifacts:
            artifact_path = Path(art["path"])

            if not artifact_path.exists():
                results["missing"] += 1
                results["details"].append({
                    "artifact_id": art["artifact_id"],
                    "status": "missing",
                    "expected_path": str(artifact_path)
                })
                continue

            current_sha256 = self.sha256_of(artifact_path)
            expected_sha256 = art["sha256"]

            if current_sha256 == expected_sha256:
                results["verified"] += 1
            else:
                results["corrupted"] += 1
                results["details"].append({
                    "artifact_id": art["artifact_id"],
                    "status": "corrupted",
                    "expected_sha256": expected_sha256,
                    "actual_sha256": current_sha256
                })

        return results
