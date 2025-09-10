from src.tractionbuild.crews.validator_crew import ValidatorCrew

def test_validator_crew():
    crew = ValidatorCrew(project_data={"id": "test"})
    result = crew.run("test-project", {})

    assert result.ok is True
    assert len(result.artifacts) == 2
    assert result.artifacts[0].type == "json"
    assert "confidence" in result.artifacts[0].meta
    assert result.artifacts[1].type == "markdown"
    assert result.artifacts[1].meta["report_type"] == "validation_summary"
    assert result.crew_name == "ValidatorCrew"
    assert result.summary == "Idea validation completed successfully"
    assert "tokens_in" in result.stats
    assert "duration_ms" in result.stats

def test_validator_crew_with_data():
    crew = ValidatorCrew(project_data={"id": "test"})
    result = crew.run("test-project", {"custom_data": "test"})

    assert result.ok is True
    assert len(result.artifacts) == 2
    assert result.crew_name == "ValidatorCrew"
