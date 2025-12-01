"""
ValidationResult model for tractionbuild.
Represents the result of business idea validation.
"""

from typing import List, Optional, Any
from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """Result of business idea validation process."""
    
    idea: str = Field(..., description="The business idea that was validated")
    market_size: str = Field(..., description="Estimated market size (TAM/SAM/SOM)")
    competition_level: str = Field(..., description="Level of competition (low/medium/high)")
    target_audience: str = Field(..., description="Primary target audience description")
    mvp_scope: str = Field(..., description="Recommended MVP scope and features")
    risks: str = Field(..., description="Key risks and mitigation strategies")
    recommendation: str = Field(..., description="Go/no-go recommendation")
    confidence_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Confidence score for the recommendation (0-1)"
    )
    reasoning: str = Field(..., description="Reasoning behind the recommendation")
    estimated_timeline: str = Field(..., description="Estimated development timeline")
    estimated_budget: str = Field(..., description="Estimated budget requirements")
    
    # Optional additional fields
    market_trends: Optional[List[str]] = Field(
        default=None, 
        description="Key market trends identified"
    )
    competitive_advantages: Optional[List[str]] = Field(
        default=None,
        description="Potential competitive advantages"
    )
    success_metrics: Optional[List[str]] = Field(
        default=None,
        description="Key success metrics to track"
    )
    next_steps: Optional[List[str]] = Field(
        default=None,
        description="Recommended next steps"
    )
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            float: lambda v: round(v, 2)
        }
        schema_extra = {
            "example": {
                "idea": "AI-powered task management app",
                "market_size": "TAM: $50B, SAM: $5B, SOM: $100M",
                "competition_level": "high",
                "target_audience": "Knowledge workers and small teams",
                "mvp_scope": "Core task management with AI prioritization",
                "risks": "High competition, user adoption challenges",
                "recommendation": "go",
                "confidence_score": 0.75,
                "reasoning": "Strong market demand despite competition",
                "estimated_timeline": "6-12 months",
                "estimated_budget": "$500K - $1M",
                "market_trends": ["AI integration", "Remote work tools"],
                "competitive_advantages": ["AI-first approach", "Simplicity"],
                "success_metrics": ["User retention", "Task completion rate"],
                "next_steps": ["Build MVP", "Conduct user interviews"]
            }
        }

    def is_positive_recommendation(self) -> bool:
        """Check if the recommendation is positive (go)."""
        return self.recommendation.lower() == "go"
        
    def get_confidence_level(self) -> str:
        """Get confidence level as a string."""
        if self.confidence_score >= 0.8:
            return "high"
        elif self.confidence_score >= 0.6:
            return "medium"
        else:
            return "low"
            
    def get_risk_level(self) -> str:
        """Estimate risk level based on competition and confidence."""
        if self.competition_level.lower() == "high" and self.confidence_score < 0.7:
            return "high"
        elif self.competition_level.lower() == "medium" or self.confidence_score < 0.8:
            return "medium"
        else:
            return "low"