from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Literal
from uuid import uuid4

ArtifactType = Literal["text", "json", "markdown", "file", "image", "log"]

@dataclass
class Artifact:
    type: ArtifactType
    id: str = None
    path: Optional[str] = None
    data: Optional[Any] = None
    meta: Dict[str, Any] = None

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid4())
        if self.meta is None:
            self.meta = {}

@dataclass
class CrewResult:
    crew_name: str
    ok: bool
    summary: str
    artifacts: List[Artifact]
    stats: Dict[str, Any]  # e.g., {"tokens_in": 100, "tokens_out": 200, "cost_usd": 0.01, "duration_ms": 500}
    warnings: List[str] = None
    errors: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []

# Utility functions for result creation
def create_success_result(crew_name: str, summary: str, artifacts: List[Artifact] = None, **stats) -> CrewResult:
    """Create a successful crew result."""
    return CrewResult(
        crew_name=crew_name,
        ok=True,
        summary=summary,
        artifacts=artifacts or [],
        stats=stats,
        warnings=[],
        errors=[]
    )

def create_error_result(crew_name: str, error_msg: str, warnings: List[str] = None) -> CrewResult:
    """Create an error crew result."""
    return CrewResult(
        crew_name=crew_name,
        ok=False,
        summary=f"Error: {error_msg}",
        artifacts=[],
        stats={},
        warnings=warnings or [],
        errors=[error_msg]
    )
