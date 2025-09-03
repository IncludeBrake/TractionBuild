from typing import Dict, Any
from ..schemas.core import ValidationOutput, AdvisoryDecision

class ValidatorAdapter:
    def __init__(self, validator_crew):
        self.crew = validator_crew
    async def run(self, project_ctx: Dict[str, Any]) -> Dict[str, Any]:
        raw = await self.crew.run(project_ctx)      # use your crew's implementation
        return ValidationOutput(**raw).model_dump() # enforce schema

class AdvisoryAdapter:
    def __init__(self, advisory_crew):
        self.crew = advisory_crew
    async def run(self, project_ctx: Dict[str, Any]) -> Dict[str, Any]:
        raw = await self.crew.run(project_ctx)
        return AdvisoryDecision(**raw).model_dump()
