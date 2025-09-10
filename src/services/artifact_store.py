from pathlib import Path
from typing import List
from src.core.types import Artifact, CrewResult
from src.security.redact import redact_pii
import json
import hashlib
from uuid import uuid4

class ArtifactStore:
    def __init__(self, base_path: str = "runs"):
        self.base_path = Path(base_path)

    def save_artifacts(self, project_id: str, result: CrewResult) -> List[str]:
        paths = []
        crew_dir = self.base_path / project_id / "artifacts" / result.crew_name
        crew_dir.mkdir(parents=True, exist_ok=True)

        for artifact in result.artifacts:
            ext = artifact.type if artifact.type != "file" else "bin"
            artifact_id = artifact.id or str(uuid4())
            path = crew_dir / f"{artifact_id}.{ext}"
            tmp_path = crew_dir / f"{artifact_id}.{ext}.tmp"

            if artifact.data:
                data = redact_pii(json.dumps(artifact.data) if artifact.type == "json" else str(artifact.data))
                with tmp_path.open("w", encoding="utf-8") as f:
                    f.write(data)
                tmp_path.rename(path)
            elif artifact.path:
                source_path = Path(artifact.path)
                if source_path.exists():
                    with source_path.open("rb") as src, tmp_path.open("wb") as dst:
                        dst.write(src.read())
                    tmp_path.rename(path)

            # Create metadata with SHA256
            meta = {**artifact.meta, "sha256": self.compute_sha256(path), "type": artifact.type}
            meta_path = crew_dir / f"{artifact_id}.meta.json"
            with meta_path.open("w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

            paths.append(str(path))

        return paths

    def compute_sha256(self, path: Path) -> str:
        hash_sha256 = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def load_artifacts(self, project_id: str, crew_name: str) -> List[Artifact]:
        crew_dir = self.base_path / project_id / "artifacts" / crew_name
        artifacts = []

        if not crew_dir.exists():
            return artifacts

        for meta_file in crew_dir.glob("*.meta.json"):
            try:
                with meta_file.open(encoding="utf-8") as f:
                    meta = json.load(f)

                artifact_id = meta_file.stem
                artifact_type = meta.get("type", "file")
                ext = artifact_type if artifact_type != "file" else "bin"
                path = crew_dir / f"{artifact_id}.{ext}"

                if path.exists():
                    artifacts.append(Artifact(
                        id=artifact_id,
                        type=artifact_type,
                        path=str(path),
                        meta=meta
                    ))
            except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
                print(f"Failed to load artifact metadata {meta_file}: {e}")
                continue

        return artifacts
