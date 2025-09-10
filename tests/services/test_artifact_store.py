from src.services.artifact_store import ArtifactStore
from src.core.types import CrewResult, Artifact
from pathlib import Path
import tempfile
import os

def test_save_artifacts():
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        store = ArtifactStore(temp_dir)
        result = CrewResult(
            crew_name="test",
            ok=True,
            summary="Test",
            artifacts=[Artifact(type="text", data="Hello World")],
            stats={"test": "value"}
        )

        paths = store.save_artifacts("test-project", result)

        assert len(paths) == 1
        assert Path(paths[0]).exists()

        # Check metadata file exists
        meta_path = Path(paths[0]).with_suffix(f"{Path(paths[0]).suffix}.meta.json")
        assert meta_path.exists()

        # Check content
        with open(paths[0], "r") as f:
            content = f.read()
            assert content == "Hello World"

def test_load_artifacts():
    with tempfile.TemporaryDirectory() as temp_dir:
        store = ArtifactStore(temp_dir)

        # Create test artifact
        result = CrewResult(
            crew_name="test",
            ok=True,
            summary="Test",
            artifacts=[Artifact(id="test123", type="json", data={"key": "value"})],
            stats={}
        )

        paths = store.save_artifacts("test-project", result)
        artifacts = store.load_artifacts("test-project", "test")

        assert len(artifacts) == 1
        assert artifacts[0].id == "test123"
        assert artifacts[0].type == "json"
        assert artifacts[0].data == {"key": "value"}

def test_sha256_computation():
    with tempfile.TemporaryDirectory() as temp_dir:
        store = ArtifactStore(temp_dir)

        # Create a test file
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Hello World")

        sha256 = store.sha256_of(test_file)
        assert len(sha256) == 64  # SHA256 is 64 characters
        assert sha256.replace("a", "").replace("b", "").replace("c", "").replace("d", "").replace("e", "").replace("f", "").isalnum()
