"""
Market data models for ZeroToShip.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class CompetitionLevel(str, Enum):
    """Competition level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Recommendation(str, Enum):
    """Recommendation enumeration."""
    GO = "go"
    NO_GO = "no_go"
    PIVOT = "pivot"
    FURTHER_RESEARCH = "further_research"


class MarketData(BaseModel):
    """Market data model."""
    
    market_size: str = Field(description="Estimated market size")
    growth_rate: str = Field(description="Market growth rate")
    key_players: List[str] = Field(default_factory=list, description="Key market players")
    trends: List[str] = Field(default_factory=list, description="Market trends")
    opportunities: List[str] = Field(default_factory=list, description="Market opportunities")
    threats: List[str] = Field(default_factory=list, description="Market threats")
    barriers_to_entry: List[str] = Field(default_factory=list, description="Barriers to entry")
    regulatory_environment: str = Field(description="Regulatory environment description")


class ValidationResult(BaseModel):
    """Result of idea validation."""
    
    idea: str = Field(description="The validated idea")
    market_size: str = Field(description="Estimated market size")
    competition_level: CompetitionLevel = Field(description="Level of competition")
    target_audience: str = Field(description="Target audience description")
    mvp_scope: str = Field(description="MVP scope definition")
    risks: str = Field(description="Identified risks")
    recommendation: Recommendation = Field(description="Go/no-go recommendation")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence score (0-1)")
    reasoning: str = Field(description="Detailed reasoning for recommendation")
    next_steps: List[str] = Field(default_factory=list, description="Recommended next steps")
    estimated_timeline: str = Field(description="Estimated timeline for MVP")
    estimated_budget: str = Field(description="Estimated budget for MVP")
    success_metrics: List[str] = Field(default_factory=list, description="Success metrics")


class CompetitorAnalysis(BaseModel):
    """Competitor analysis model."""
    
    competitor_name: str = Field(description="Competitor name")
    market_position: str = Field(description="Market position")
    strengths: List[str] = Field(default_factory=list, description="Competitor strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Competitor weaknesses")
    pricing_strategy: str = Field(description="Pricing strategy")
    target_audience: str = Field(description="Target audience")
    unique_selling_proposition: str = Field(description="Unique selling proposition")
    market_share: Optional[str] = Field(description="Market share")


class MVPScope(BaseModel):
    """MVP scope definition."""
    
    core_features: List[str] = Field(default_factory=list, description="Core MVP features")
    timeline: str = Field(description="Development timeline")
    budget: str = Field(description="Estimated budget")
    team_size: str = Field(description="Required team size")
    success_metrics: List[str] = Field(default_factory=list, description="Success metrics")
    technical_stack: List[str] = Field(default_factory=list, description="Technical stack")
    dependencies: List[str] = Field(default_factory=list, description="External dependencies")
    assumptions: List[str] = Field(default_factory=list, description="Key assumptions") 