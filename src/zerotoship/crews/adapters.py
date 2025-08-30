from typing import Dict, Any
from ..schemas import ValidationOutput, AdvisoryDecision

class ValidatorAdapter:
    def __init__(self, validator_crew):
        self.crew = validator_crew
    
    async def run(self, project_ctx: Dict[str, Any]) -> Dict[str, Any]:
        """Run validator crew and enforce ValidationOutput schema."""
        raw = await self.crew.run(project_ctx)
        return ValidationOutput(**raw).model_dump()

class AdvisoryAdapter:
    def __init__(self, advisory_crew):
        self.crew = advisory_crew
    
    async def run(self, project_ctx: Dict[str, Any]) -> Dict[str, Any]:
        """Run advisory crew and enforce AdvisoryDecision schema."""
        raw = await self.crew.run(project_ctx)
        return AdvisoryDecision(**raw).model_dump()
