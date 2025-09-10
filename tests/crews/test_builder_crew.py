from src.tractionbuild.crews.builder_crew import BuilderCrew
from src.core.types import CrewResult

def test_builder_crew():
    crew = BuilderCrew(project_data={"id": "test"})
    result = crew.run("test-project", {"result": "test"})

    assert result.ok is True
    assert len(result.artifacts) > 0
    assert result.stats["duration_ms"] > 0
    assert "tokens_in" in result.stats
    assert result.crew_name == "BuilderCrew"
    assert result.summary == "Built project components successfully"

def test_builder_crew_error_handling():
    crew = BuilderCrew(project_data={"id": "test"})

    # This should still work even with invalid input
    result = crew.run("test-project", {})

    assert result.ok is True  # Should handle gracefully
    assert len(result.artifacts) > 0
    assert result.crew_name == "BuilderCrew"
