"""
Canonical types for TractionBuild crew outputs and artifacts.
Eliminates ambiguity in result schemas and provides deterministic artifact storage.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime
import json

ArtifactType = Literal["text", "json", "markdown", "file", "image", "log"]

@dataclass
class Artifact:
    """Standardized artifact representation."""
    id: str
    type: ArtifactType
    path: Optional[str] = None  # for file/image artifacts
    data: Optional[Any] = None  # inline payload for small text/json/md
    meta: Dict[str, Any] = None

    def __post_init__(self):
        if self.meta is None:
            self.meta = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        # Handle datetime serialization
        if 'created_at' in self.meta and isinstance(self.meta['created_at'], datetime):
            result['meta']['created_at'] = self.meta['created_at'].isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Artifact':
        """Create from dictionary."""
        return cls(**data)

@dataclass
class CrewResult:
    """Standardized crew execution result."""
    crew_name: str
    ok: bool
    summary: str
    artifacts: List[Artifact]
    stats: Dict[str, Any]  # tokens_in, tokens_out, cost_usd, duration_ms
    warnings: List[str]
    errors: List[str]

    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []
        if self.stats is None:
            self.stats = {}
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        # Convert artifacts to dicts
        result['artifacts'] = [artifact.to_dict() for artifact in self.artifacts]
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CrewResult':
        """Create from dictionary."""
        # Convert artifact dicts back to Artifact objects
        artifacts = [Artifact.from_dict(art) for art in data.get('artifacts', [])]
        data_copy = data.copy()
        data_copy['artifacts'] = artifacts
        return cls(**data_copy)

    def add_artifact(self, artifact: Artifact) -> None:
        """Add an artifact to the result."""
        self.artifacts.append(artifact)

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)

    def set_stats(self, **kwargs) -> None:
        """Set statistics."""
        self.stats.update(kwargs)

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
