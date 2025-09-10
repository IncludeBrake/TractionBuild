from src.services.project_registry import ProjectRegistry
from src.core.types import CrewResult, Artifact
import tempfile

def test_project_registry():
    with tempfile.TemporaryDirectory() as temp_dir:
        registry = ProjectRegistry(temp_dir)

        # Test project creation
        registry.create_project("test-project", "Test idea")
        data = registry.get_project_data("test-project")

        assert data["project_id"] == "test-project"
        assert data["idea"] == "Test idea"
        assert "IDEA_VALIDATION" in data["states"]

def test_append_crew_result():
    with tempfile.TemporaryDirectory() as temp_dir:
        registry = ProjectRegistry(temp_dir)

        # Create project
        registry.create_project("test-project", "Test idea")

        # Create crew result
        result = CrewResult(
            crew_name="TestCrew",
            ok=True,
            summary="Test completed",
            artifacts=[Artifact(type="text", data="Test artifact")],
            stats={"tokens_in": 100, "tokens_out": 50}
        )

        # Append result
        registry.append_crew_result("test-project", result)

        # Check data
        data = registry.get_project_data("test-project")
        assert len(data["crews"]) == 1
        assert data["crews"][0]["crew_name"] == "TestCrew"
        assert data["crews"][0]["ok"] is True
        assert len(data["crews"][0]["artifact_paths"]) == 1

def test_get_crew_results():
    with tempfile.TemporaryDirectory() as temp_dir:
        registry = ProjectRegistry(temp_dir)

        # Create project and add results
        registry.create_project("test-project", "Test idea")

        result1 = CrewResult(
            crew_name="Crew1",
            ok=True,
            summary="Test 1",
            artifacts=[],
            stats={}
        )

        result2 = CrewResult(
            crew_name="Crew2",
            ok=False,
            summary="Test 2",
            artifacts=[],
            stats={}
        )

        registry.append_crew_result("test-project", result1)
        registry.append_crew_result("test-project", result2)

        # Test getting all results
        all_results = registry.get_crew_results("test-project")
        assert len(all_results) == 2

        # Test getting specific crew results
        crew1_results = registry.get_crew_results("test-project", "Crew1")
        assert len(crew1_results) == 1
        assert crew1_results[0]["crew_name"] == "Crew1"
