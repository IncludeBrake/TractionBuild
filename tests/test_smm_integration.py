"""
Integration tests for Synthetic Marketing Machine (SMM).
"""

import pytest
import json
import os
from src.smm.pipeline import SMM
from src.core.types import CrewResult
from src.services.project_registry import ProjectRegistry
from src.services.artifact_store import ArtifactStore
import tempfile

def test_smm_basic_functionality():
    """Test basic SMM functionality."""
    smm = SMM()

    # Test with a sample idea
    idea_text = "A task management app that uses AI to prioritize work"
    project_id = "test-smm-123"

    result = smm.run(project_id, idea_text)

    # Verify result structure
    assert isinstance(result, CrewResult)
    assert result.crew_name == "SMM"
    assert result.ok is True
    assert len(result.artifacts) >= 2  # Should have JSON and Markdown artifacts

    # Check artifacts
    json_artifact = next((a for a in result.artifacts if a.type == "json"), None)
    markdown_artifact = next((a for a in result.artifacts if a.type == "markdown"), None)

    assert json_artifact is not None
    assert markdown_artifact is not None
    assert isinstance(json_artifact.data, dict)
    assert isinstance(markdown_artifact.data, str)

    # Check stats
    assert "tokens_in" in result.stats
    assert "tokens_out" in result.stats
    assert "duration_ms" in result.stats

def test_smm_with_registry_integration():
    """Test SMM with full registry and artifact store integration."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup services
        registry = ProjectRegistry(temp_dir)
        store = ArtifactStore(temp_dir)

        # Create project
        project_id = "integration-test-456"
        idea_text = "An AI-powered code review tool for developers"
        registry.create_project(project_id, idea_text)

        # Run SMM
        smm = SMM()
        result = smm.run(project_id, idea_text)

        # Store results
        registry.append_crew_result(project_id, result)

        # Verify storage
        project_data = registry.get_project_data(project_id)
        assert len(project_data["crews"]) == 1

        smm_result = project_data["crews"][0]
        assert smm_result["crew_name"] == "SMM"
        assert smm_result["ok"] is True
        assert len(smm_result["artifact_paths"]) >= 2

        # Verify artifacts exist on disk
        for artifact_path in smm_result["artifact_paths"]:
            assert os.path.exists(artifact_path)

            # Check SHA256 hash
            meta_path = artifact_path + ".meta.json"
            assert os.path.exists(meta_path)

            with open(meta_path) as f:
                meta = json.load(f)
                assert "sha256" in meta
                assert len(meta["sha256"]) == 64  # SHA256 is 64 chars

def test_smm_cache_functionality():
    """Test SMM caching functionality."""
    smm = SMM()

    project_id = "cache-test-789"
    idea_text = "A mobile app for habit tracking with social features"

    # First run
    result1 = smm.run(project_id, idea_text)
    duration1 = result1.stats["duration_ms"]

    # Second run (should use cache)
    result2 = smm.run(project_id, idea_text)
    duration2 = result2.stats["duration_ms"]

    # Cache hit should be much faster
    assert duration2 < duration1  # Cache should be faster
    assert result2.stats.get("cache_hit") is True
    assert result1.stats.get("cache_hit") is False

    # Results should be identical
    assert result1.summary == result2.summary
    assert len(result1.artifacts) == len(result2.artifacts)

def test_smm_error_handling():
    """Test SMM error handling."""
    smm = SMM()

    # Test with empty idea
    result = smm.run("error-test", "")

    assert result.ok is False
    assert "error" in result.summary.lower()
    assert len(result.errors) > 0

def test_guardrails_integration():
    """Test that guardrails are applied to SMM results."""
    from src.smm.guardrails import check_consistency

    # Create a mock result with potential inconsistencies
    result = CrewResult(
        crew_name="SMM",
        ok=True,
        summary="Test analysis",
        artifacts=[],
        stats={}
    )

    # Apply guardrails
    checked_result = check_consistency(result)

    # Should have warnings about insufficient artifacts
    assert len(checked_result.warnings) > 0
    assert "Insufficient artifacts" in checked_result.warnings[0]

if __name__ == "__main__":
    pytest.main([__file__])
