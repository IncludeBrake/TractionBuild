"""
Integration test for the complete TractionBuild crew execution flow.
Tests standardized CrewResult outputs, artifact storage, and registry updates.
"""

from src.services.project_registry import ProjectRegistry
from src.services.artifact_store import ArtifactStore
from src.tractionbuild.crews.builder_crew import BuilderCrew
from src.tractionbuild.crews.validator_crew import ValidatorCrew
from src.core.types import CrewResult
import tempfile
import os

def test_complete_flow():
    """Test the complete flow: create project -> run crews -> store artifacts -> check registry"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize services
        registry = ProjectRegistry(temp_dir)
        store = ArtifactStore(temp_dir)

        project_id = "integration-test-project"
        idea_text = "Build a task management app"

        # 1. Create project
        registry.create_project(project_id, idea_text)

        # Verify project creation
        project_data = registry.get_project_data(project_id)
        assert project_data["project_id"] == project_id
        assert project_data["idea"] == idea_text
        assert "IDEA_VALIDATION" in project_data["states"]

        # 2. Run ValidatorCrew
        validator_crew = ValidatorCrew(project_data={"id": project_id})
        validator_result = validator_crew.run(project_id, {"idea": idea_text})

        # Verify validator result
        assert isinstance(validator_result, CrewResult)
        assert validator_result.crew_name == "ValidatorCrew"
        assert validator_result.ok is True
        assert len(validator_result.artifacts) == 2  # JSON + Markdown
        assert "tokens_in" in validator_result.stats

        # 3. Store validator artifacts and update registry
        registry.append_crew_result(project_id, validator_result)

        # 4. Run BuilderCrew
        builder_crew = BuilderCrew(project_data={"id": project_id})
        builder_result = builder_crew.run(project_id, {"validated_idea": idea_text})

        # Verify builder result
        assert isinstance(builder_result, CrewResult)
        assert builder_result.crew_name == "BuilderCrew"
        assert builder_result.ok is True
        assert len(builder_result.artifacts) >= 1
        assert "tokens_in" in builder_result.stats

        # 5. Store builder artifacts and update registry
        registry.append_crew_result(project_id, builder_result)

        # 6. Verify final state
        final_data = registry.get_project_data(project_id)
        assert len(final_data["crews"]) == 2

        # Check validator crew entry
        validator_entry = next(c for c in final_data["crews"] if c["crew_name"] == "ValidatorCrew")
        assert validator_entry["ok"] is True
        assert len(validator_entry["artifact_paths"]) == 2

        # Check builder crew entry
        builder_entry = next(c for c in final_data["crews"] if c["crew_name"] == "BuilderCrew")
        assert builder_entry["ok"] is True
        assert len(builder_entry["artifact_paths"]) >= 1

        # 7. Verify artifacts exist on disk
        for crew_entry in final_data["crews"]:
            for artifact_path in crew_entry["artifact_paths"]:
                assert os.path.exists(artifact_path)
                # Check metadata file exists
                meta_path = artifact_path + ".meta.json"
                assert os.path.exists(meta_path)

        # 8. Test artifact loading
        validator_artifacts = store.load_artifacts(project_id, "ValidatorCrew")
        assert len(validator_artifacts) == 2

        builder_artifacts = store.load_artifacts(project_id, "BuilderCrew")
        assert len(builder_artifacts) >= 1

        print("✅ Complete integration flow test passed!")

def test_error_handling():
    """Test error handling in the flow"""
    with tempfile.TemporaryDirectory() as temp_dir:
        registry = ProjectRegistry(temp_dir)

        # Create project
        registry.create_project("error-test", "Test idea")

        # Simulate error result
        error_result = CrewResult(
            crew_name="ErrorCrew",
            ok=False,
            summary="Failed execution",
            artifacts=[],
            stats={"duration_ms": 100},
            errors=["Test error"]
        )

        # Store error result
        registry.append_crew_result("error-test", error_result)

        # Verify error is recorded
        data = registry.get_project_data("error-test")
        error_entry = data["crews"][0]
        assert error_entry["ok"] is False
        assert len(error_entry["errors"]) == 1
        assert error_entry["errors"][0] == "Test error"

        print("✅ Error handling test passed!")

if __name__ == "__main__":
    test_complete_flow()
    test_error_handling()
    print("🎉 All integration tests passed!")
