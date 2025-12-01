# src/tractionbuild/adapters/crew_adapters.py
"""
Real crew adapters that bridge FastAPI workflow engine to CrewAI implementations.
Replaces the mock adapters with actual crew execution.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from functools import wraps

# Import your actual crew implementations
from ..crews.validator_crew import ValidatorCrew
from ..crews.advisory_board_crew import AdvisoryBoardCrew
from ..crews.builder_crew import BuilderCrew
from ..crews.marketing_crew import MarketingCrew
from ..crews.feedback_crew import FeedbackCrew

logger = logging.getLogger(__name__)

def guard(op_name: str):
    """Decorator for error handling and monitoring."""
    def deco(fn):
        @wraps(fn)
        async def wrapped(*args, **kwargs):
            try:
                result = await fn(*args, **kwargs)
                logger.info(f"✅ {op_name} completed successfully")
                return result
            except Exception as e:
                logger.error(f"❌ {op_name} failed: {str(e)}")
                raise
        return wrapped
    return deco

class ValidatorAdapter:
    """Adapter for ValidatorCrew - handles market validation and idea analysis."""
    
    def __init__(self):
        self.crew = ValidatorCrew()
    
    @guard("validator.execute")
    async def run(self, project_ctx: Dict[str, Any]) -> Dict[str, Any]:
        """Run validation crew and return structured results."""
        logger.info(f"🔍 Starting validation for project: {project_ctx['project']['name']}")
        
        # Prepare inputs for the crew
        crew_inputs = {
            'project_name': project_ctx['project']['name'],
            'description': project_ctx['project']['description'],
            'hypothesis': project_ctx['project']['hypothesis'],
            'target_avatars': project_ctx['project'].get('target_avatars', [])
        }
        
        # Execute the crew in a thread pool since CrewAI is synchronous
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            lambda: self.crew.run(crew_inputs)
        )
        
        # Transform crew output to expected format
        return self._transform_validator_output(result)
    
    def _transform_validator_output(self, crew_result: Any) -> Dict[str, Any]:
        """Transform crew output to standardized validation format."""
        # Handle different possible crew output formats
        if hasattr(crew_result, 'raw'):
            output = crew_result.raw
        elif isinstance(crew_result, dict):
            output = crew_result
        else:
            output = str(crew_result)
        
        # Extract or generate validation metrics
        # This would parse the crew's natural language output
        # and extract structured data
        
        return {
            "go_recommendation": self._extract_go_decision(output),
            "confidence": self._extract_confidence(output),
            "avatars": self._extract_validated_avatars(output),
            "mvp_features": self._extract_mvp_features(output),
            "risks": self._extract_risks(output),
            "findings": self._extract_findings(output),
            "raw_output": output
        }
    
    def _extract_go_decision(self, output: str) -> bool:
        """Extract go/no-go decision from crew output."""
        output_lower = str(output).lower()
        go_indicators = ['recommend', 'proceed', 'go ahead', 'viable', 'promising']
        stop_indicators = ['not recommended', 'pivot', 'stop', 'risky', 'not viable']
        
        go_score = sum(1 for indicator in go_indicators if indicator in output_lower)
        stop_score = sum(1 for indicator in stop_indicators if indicator in output_lower)
        
        return go_score > stop_score
    
    def _extract_confidence(self, output: str) -> float:
        """Extract confidence score from crew output."""
        # Look for percentage patterns or confidence keywords
        import re
        
        # Look for explicit percentages
        percentage_match = re.search(r'(\d+(?:\.\d+)?)%', str(output))
        if percentage_match:
            return float(percentage_match.group(1)) / 100
        
        # Look for confidence keywords
        confidence_keywords = {
            'very confident': 0.9,
            'highly confident': 0.85,
            'confident': 0.8,
            'moderately confident': 0.7,
            'somewhat confident': 0.6,
            'low confidence': 0.4,
            'uncertain': 0.3
        }
        
        output_lower = str(output).lower()
        for keyword, score in confidence_keywords.items():
            if keyword in output_lower:
                return score
        
        return 0.75  # Default moderate confidence

    def _extract_validated_avatars(self, output: str) -> list:
        """Extract validated avatar types from output."""
        # This would parse the output for avatar mentions
        avatars = []
        avatar_types = ['startup_entrepreneur', 'sme', 'investor_incubator', 'corporate_innovation_lab']
        
        output_lower = str(output).lower()
        for avatar in avatar_types:
            if avatar.replace('_', ' ') in output_lower or avatar in output_lower:
                avatars.append(avatar)
        
        return avatars
    
    def _extract_mvp_features(self, output: str) -> list:
        """Extract MVP features from crew analysis."""
        # Parse output for feature mentions
        # This is a simplified version - could be more sophisticated
        lines = str(output).split('\n')
        features = []
        
        for line in lines:
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in ['feature', 'functionality', 'capability', 'component']):
                features.append(line.strip())
        
        return features[:5]  # Limit to top 5
    
    def _extract_risks(self, output: str) -> list:
        """Extract identified risks from crew analysis."""
        lines = str(output).split('\n')
        risks = []
        
        for line in lines:
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in ['risk', 'concern', 'challenge', 'issue', 'problem']):
                risks.append(line.strip())
        
        return risks[:5]  # Limit to top 5
    
    def _extract_findings(self, output: str) -> list:
        """Extract key findings from crew analysis."""
        # Extract key insights and findings
        lines = str(output).split('\n')
        findings = []
        
        for line in lines:
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in ['finding', 'insight', 'analysis', 'conclusion']):
                findings.append(line.strip())
        
        return findings


class AdvisoryAdapter:
    """Adapter for AdvisoryBoardCrew - handles strategic decisions and recommendations."""
    
    def __init__(self):
        self.crew = AdvisoryBoardCrew()
    
    @guard("advisory.execute")
    async def run(self, project_ctx: Dict[str, Any]) -> Dict[str, Any]:
        """Run advisory board crew and return strategic recommendations."""
        logger.info(f"🏛️ Starting advisory board for project: {project_ctx['project']['name']}")
        
        # Include validation results in advisory inputs
        crew_inputs = {
            'project_name': project_ctx['project']['name'],
            'description': project_ctx['project']['description'],
            'hypothesis': project_ctx['project']['hypothesis'],
            'validation_results': project_ctx.get('artifacts', {}).get('validator', {}),
            'target_avatars': project_ctx['project'].get('target_avatars', [])
        }
        
        # Execute the crew
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            lambda: self.crew.run(crew_inputs)
        )
        
        return self._transform_advisory_output(result)
    
    def _transform_advisory_output(self, crew_result: Any) -> Dict[str, Any]:
        """Transform crew output to standardized advisory format."""
        if hasattr(crew_result, 'raw'):
            output = crew_result.raw
        elif isinstance(crew_result, dict):
            output = crew_result
        else:
            output = str(crew_result)
        
        return {
            "approved": self._extract_approval_decision(output),
            "rationale": self._extract_rationale(output),
            "must_haves": self._extract_must_haves(output),
            "cut_scope": self._extract_cut_scope(output),
            "kpis": self._extract_kpis(output),
            "raw_output": output
        }
    
    def _extract_approval_decision(self, output: str) -> bool:
        """Extract approval decision from advisory output."""
        output_lower = str(output).lower()
        approve_indicators = ['approved', 'recommend', 'proceed', 'green light', 'go ahead']
        reject_indicators = ['rejected', 'not approved', 'decline', 'red light', 'pivot']
        
        approve_score = sum(1 for indicator in approve_indicators if indicator in output_lower)
        reject_score = sum(1 for indicator in reject_indicators if indicator in output_lower)
        
        return approve_score > reject_score
    
    def _extract_rationale(self, output: str) -> str:
        """Extract decision rationale from output."""
        # Look for rationale sections or extract first substantial paragraph
        lines = str(output).split('\n')
        rationale_lines = []
        
        for line in lines:
            if line.strip() and len(line.strip()) > 50:  # Substantial content
                rationale_lines.append(line.strip())
                if len(rationale_lines) >= 3:  # Enough for rationale
                    break
        
        return ' '.join(rationale_lines) if rationale_lines else "Decision rationale provided by advisory board."
    
    def _extract_must_haves(self, output: str) -> list:
        """Extract must-have requirements from advisory output."""
        lines = str(output).split('\n')
        must_haves = []
        
        for line in lines:
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in ['must have', 'required', 'essential', 'critical']):
                must_haves.append(line.strip())
        
        return must_haves[:5]
    
    def _extract_cut_scope(self, output: str) -> list:
        """Extract scope reduction recommendations."""
        lines = str(output).split('\n')
        cuts = []
        
        for line in lines:
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in ['cut', 'remove', 'eliminate', 'reduce', 'defer']):
                cuts.append(line.strip())
        
        return cuts[:5]
    
    def _extract_kpis(self, output: str) -> Dict[str, Any]:
        """Extract KPIs and metrics from advisory recommendations."""
        import re
        
        kpis = {}
        output_str = str(output)
        
        # Look for revenue targets
        revenue_match = re.search(r'\$?([\d,]+).*revenue', output_str, re.IGNORECASE)
        if revenue_match:
            kpis['target_revenue'] = int(revenue_match.group(1).replace(',', ''))
        
        # Look for user targets
        users_match = re.search(r'(\d+).*users?', output_str, re.IGNORECASE)
        if users_match:
            kpis['target_users'] = int(users_match.group(1))
        
        # Look for timeframe
        time_match = re.search(r'(\d+).*months?', output_str, re.IGNORECASE)
        if time_match:
            kpis['timeframe_months'] = int(time_match.group(1))
        
        # Default KPIs if none found
        if not kpis:
            kpis = {
                'target_revenue': 100000,
                'target_users': 1000,
                'timeframe_months': 12
            }
        
        return kpis


# Factory function to create the right adapters
def create_crew_registry() -> Dict[str, Any]:
    """Create registry of real crew adapters."""
    return {
        "validator": ValidatorAdapter(),
        "advisory": AdvisoryAdapter(),
        # Add other crews as needed
        # "builder": BuilderAdapter(),
        # "marketing": MarketingAdapter(),
        # "feedback": FeedbackAdapter(),
    }