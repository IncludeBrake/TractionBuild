"""
Observability Crew for tractionbuild.
Provides real-time monitoring, anomaly detection, and continuous improvement recommendations.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import redis
import numpy as np
from scipy import stats

from crewai import Agent, Task, Crew, Process
from pydantic import BaseModel, Field

from .base_crew import BaseCrew
from ..tools.market_oracle_tool import MarketOracleTool
from ..tools.sustainability_tool import SustainabilityTrackerTool
from ..tools.compliance_tool import ComplianceCheckerTool
from ..tools.summarization_tool import SummarizationTool
from ..utils.llm_factory import get_llm

logger = logging.getLogger(__name__)


class ObservabilityMetrics(BaseModel):
    """Metrics collected by the ObservabilityCrew."""
    
    quality_score: float = Field(..., description="Overall quality score (0-1)")
    cost_per_1k_tokens: float = Field(..., description="Cost per 1K tokens")
    drift_score: float = Field(..., description="Model drift score (0-1)")
    time_to_value: float = Field(..., description="Time to value in minutes")
    error_rate: float = Field(..., description="Error rate percentage")
    carbon_footprint: float = Field(..., description="CO2 emissions in kg")
    compliance_score: float = Field(..., description="Compliance score (0-1)")


class ObservabilityCrew(BaseCrew):
    """Crew responsible for monitoring, analyzing, and improving tractionbuild performance."""
    
    def __init__(self, project_data: Dict[str, Any]):
        super().__init__(project_data)
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.metrics_history = []
        
    def _create_crew(self) -> Crew:
        """Create the Observability Crew with specialized agents."""
        
        # Get LLM from the factory
        llm = get_llm()
        
        # Define specialized agents
        metrics_collector = Agent(
            role="Metrics Collection Specialist",
            goal="Collect and aggregate real-time metrics from all tractionbuild components",
            backstory="You are a data engineering expert who specializes in collecting and processing observability data from distributed systems.",
            verbose=True,
            tools=[SustainabilityTrackerTool()],
            llm=llm
        )
        
        anomaly_detector = Agent(
            role="Anomaly Detection Expert",
            goal="Detect anomalies in system performance, quality, and cost metrics",
            backstory="You are a machine learning specialist who uses statistical analysis to identify unusual patterns and potential issues.",
            verbose=True,
            tools=[MarketOracleTool()],
            llm=llm
        )
        
        quality_analyst = Agent(
            role="Quality Assurance Specialist",
            goal="Analyze output quality, detect hallucinations, and assess confidence scores",
            backstory="You are a quality assurance expert who specializes in evaluating AI-generated content and detecting inconsistencies.",
            verbose=True,
            tools=[SummarizationTool(), ComplianceCheckerTool()],
            llm=llm
        )
        
        cost_optimizer = Agent(
            role="Cost Optimization Specialist",
            goal="Monitor and optimize operational costs including LLM API usage and carbon footprint",
            backstory="You are a financial analyst who specializes in cost optimization and sustainability metrics.",
            verbose=True,
            tools=[SustainabilityTrackerTool()],
            llm=llm
        )
        
        improvement_recommender = Agent(
            role="Continuous Improvement Specialist",
            goal="Generate actionable recommendations for system improvements based on collected metrics",
            backstory="You are a process improvement expert who analyzes data to suggest optimizations and enhancements.",
            verbose=True,
            tools=[MarketOracleTool()],
            llm=llm
        )
        
        # Create tasks
        tasks = [
            Task(
                description="Collect current metrics from all tractionbuild components including workflow execution times, error rates, API usage, and carbon footprint",
                agent=metrics_collector,
                expected_output="Comprehensive metrics report with current system performance data"
            ),
            
            Task(
                description="Analyze collected metrics for anomalies using statistical methods. Focus on quality scores, cost trends, and performance degradation",
                agent=anomaly_detector,
                expected_output="Anomaly detection report with identified issues and severity levels"
            ),
            
            Task(
                description="Evaluate output quality by analyzing confidence scores, detecting potential hallucinations, and assessing consistency across crews",
                agent=quality_analyst,
                expected_output="Quality assessment report with specific issues and improvement areas"
            ),
            
            Task(
                description="Analyze cost metrics including LLM API usage, compute costs, and carbon footprint. Identify optimization opportunities",
                agent=cost_optimizer,
                expected_output="Cost analysis report with optimization recommendations"
            ),
            
            Task(
                description="Based on all collected data, generate specific, actionable recommendations for improving tractionbuild performance, quality, and efficiency",
                agent=improvement_recommender,
                expected_output="Prioritized list of improvement recommendations with implementation steps"
            )
        ]
        
        return Crew(
            agents=[metrics_collector, anomaly_detector, quality_analyst, cost_optimizer, improvement_recommender],
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )
    
    async def collect_metrics(self) -> ObservabilityMetrics:
        """Collect real-time metrics from the system."""
        
        try:
            # Collect metrics from various sources
            metrics = {
                "quality_score": await self._get_quality_score(),
                "cost_per_1k_tokens": await self._get_cost_metrics(),
                "drift_score": await self._get_drift_score(),
                "time_to_value": await self._get_time_to_value(),
                "error_rate": await self._get_error_rate(),
                "carbon_footprint": await self._get_carbon_footprint(),
                "compliance_score": await self._get_compliance_score()
            }
            
            # Store in Redis for real-time access
            self.redis_client.setex(
                f"metrics:{self.project_data.get('id', 'current')}",
                300,  # 5 minute TTL
                json.dumps(metrics)
            )
            
            # Add to history for trend analysis
            self.metrics_history.append({
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics
            })
            
            # Keep only last 100 entries
            if len(self.metrics_history) > 100:
                self.metrics_history = self.metrics_history[-100:]
            
            return ObservabilityMetrics(**metrics)
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return ObservabilityMetrics(
                quality_score=0.0,
                cost_per_1k_tokens=0.0,
                drift_score=0.0,
                time_to_value=0.0,
                error_rate=1.0,
                carbon_footprint=0.0,
                compliance_score=0.0
            )
    
    async def _get_quality_score(self) -> float:
        """Calculate overall quality score from crew outputs."""
        try:
            # Get recent crew outputs from Neo4j or Redis
            outputs = self.redis_client.lrange("crew_outputs", 0, 9)  # Last 10 outputs
            
            if not outputs:
                return 0.8  # Default score
            
            confidence_scores = []
            for output in outputs:
                data = json.loads(output)
                if "confidence_score" in data:
                    confidence_scores.append(data["confidence_score"])
            
            return np.mean(confidence_scores) if confidence_scores else 0.8
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 0.8
    
    async def _get_cost_metrics(self) -> float:
        """Calculate cost per 1K tokens."""
        try:
            # This would integrate with actual API usage tracking
            # For now, return a simulated value
            return 0.002  # $0.002 per 1K tokens
            
        except Exception as e:
            logger.error(f"Error calculating cost metrics: {e}")
            return 0.0
    
    async def _get_drift_score(self) -> float:
        """Calculate model drift score using statistical methods."""
        try:
            if len(self.metrics_history) < 10:
                return 0.0  # Not enough data
            
            # Calculate drift in quality scores over time
            quality_scores = [entry["metrics"]["quality_score"] for entry in self.metrics_history[-20:]]
            
            if len(quality_scores) < 5:
                return 0.0
            
            # Use coefficient of variation as drift indicator
            mean_score = np.mean(quality_scores)
            std_score = np.std(quality_scores)
            
            if mean_score == 0:
                return 0.0
            
            drift_score = std_score / mean_score
            return min(drift_score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Error calculating drift score: {e}")
            return 0.0
    
    async def _get_time_to_value(self) -> float:
        """Calculate average time to value."""
        try:
            # Get recent project completion times
            recent_projects = self.redis_client.lrange("project_completions", 0, 9)
            
            if not recent_projects:
                return 120.0  # Default 2 hours
            
            completion_times = []
            for project in recent_projects:
                data = json.loads(project)
                if "duration_minutes" in data:
                    completion_times.append(data["duration_minutes"])
            
            return np.mean(completion_times) if completion_times else 120.0
            
        except Exception as e:
            logger.error(f"Error calculating time to value: {e}")
            return 120.0
    
    async def _get_error_rate(self) -> float:
        """Calculate current error rate."""
        try:
            # Get recent error counts
            recent_errors = self.redis_client.get("error_count_24h")
            recent_total = self.redis_client.get("total_operations_24h")
            
            if recent_errors and recent_total:
                error_count = int(recent_errors)
                total_ops = int(recent_total)
                
                if total_ops > 0:
                    return error_count / total_ops
            
            return 0.05  # Default 5% error rate
            
        except Exception as e:
            logger.error(f"Error calculating error rate: {e}")
            return 0.05
    
    async def _get_carbon_footprint(self) -> float:
        """Get current carbon footprint."""
        try:
            # This would integrate with SustainabilityTrackerTool
            # For now, return a simulated value
            return 0.5  # 0.5 kg CO2
            
        except Exception as e:
            logger.error(f"Error calculating carbon footprint: {e}")
            return 0.0
    
    async def _get_compliance_score(self) -> float:
        """Calculate compliance score."""
        try:
            # This would integrate with ComplianceCheckerTool
            # For now, return a simulated value
            return 0.95  # 95% compliance
            
        except Exception as e:
            logger.error(f"Error calculating compliance score: {e}")
            return 0.95
    
    async def detect_anomalies(self, metrics: ObservabilityMetrics) -> List[Dict[str, Any]]:
        """Detect anomalies in the current metrics."""
        
        anomalies = []
        
        # Quality score anomaly
        if metrics.quality_score < 0.7:
            anomalies.append({
                "type": "quality_degradation",
                "severity": "high",
                "description": f"Quality score ({metrics.quality_score:.2f}) is below threshold (0.7)",
                "recommendation": "Review recent crew outputs and consider retraining models"
            })
        
        # Cost anomaly
        if metrics.cost_per_1k_tokens > 0.005:
            anomalies.append({
                "type": "cost_spike",
                "severity": "medium",
                "description": f"Cost per 1K tokens ({metrics.cost_per_1k_tokens:.4f}) is above normal",
                "recommendation": "Consider switching to local models for non-critical tasks"
            })
        
        # Drift anomaly
        if metrics.drift_score > 0.2:
            anomalies.append({
                "type": "model_drift",
                "severity": "high",
                "description": f"Model drift detected (score: {metrics.drift_score:.2f})",
                "recommendation": "Trigger model retraining and validation"
            })
        
        # Error rate anomaly
        if metrics.error_rate > 0.1:
            anomalies.append({
                "type": "high_error_rate",
                "severity": "critical",
                "description": f"Error rate ({metrics.error_rate:.2%}) is above acceptable threshold",
                "recommendation": "Immediate investigation required - check logs and system health"
            })
        
        return anomalies
    
    async def generate_recommendations(self, metrics: ObservabilityMetrics, anomalies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate improvement recommendations based on metrics and anomalies."""
        
        recommendations = []
        
        # Quality improvements
        if metrics.quality_score < 0.8:
            recommendations.append({
                "priority": "high",
                "category": "quality",
                "title": "Improve Output Quality",
                "description": "Implement additional validation steps and enhance model training",
                "actions": [
                    "Add output validation in all crews",
                    "Implement confidence score thresholds",
                    "Enhance training data quality"
                ]
            })
        
        # Cost optimization
        if metrics.cost_per_1k_tokens > 0.003:
            recommendations.append({
                "priority": "medium",
                "category": "cost",
                "title": "Optimize API Usage",
                "description": "Reduce costs by implementing smart model selection",
                "actions": [
                    "Use local models for initial validation",
                    "Implement request batching",
                    "Add cost-aware routing"
                ]
            })
        
        # Performance improvements
        if metrics.time_to_value > 180:  # More than 3 hours
            recommendations.append({
                "priority": "high",
                "category": "performance",
                "title": "Reduce Time to Value",
                "description": "Optimize workflow execution for faster delivery",
                "actions": [
                    "Parallelize independent tasks",
                    "Optimize crew execution order",
                    "Implement caching for repeated operations"
                ]
            })
        
        # Sustainability improvements
        if metrics.carbon_footprint > 1.0:
            recommendations.append({
                "priority": "medium",
                "category": "sustainability",
                "title": "Reduce Carbon Footprint",
                "description": "Optimize compute usage for environmental impact",
                "actions": [
                    "Use more efficient models",
                    "Implement compute scheduling",
                    "Optimize batch processing"
                ]
            })
        
        return recommendations
    
    async def _execute_crew(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the crew for detailed analysis."""
        try:
            # Create and run the crew
            crew = self._create_crew()
            result = await crew.kickoff()
            
            # Parse the result
            if hasattr(result, 'raw') and result.raw:
                return {"crew_output": result.raw}
            elif hasattr(result, 'result') and result.result:
                return {"crew_output": result.result}
            else:
                return {"crew_output": str(result)}
                
        except Exception as e:
            logger.error(f"Error executing crew: {e}")
            return {"crew_output": f"Error: {str(e)}"}

    async def run_async(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the observability analysis."""
        
        try:
            # Collect current metrics
            metrics = await self.collect_metrics()
            
            # Detect anomalies
            anomalies = await self.detect_anomalies(metrics)
            
            # Generate recommendations
            recommendations = await self.generate_recommendations(metrics, anomalies)
            
            # Run the crew for detailed analysis
            crew_result = await self._execute_crew(project_data)
            
            # Combine results
            result = {
                "metrics": metrics.model_dump(),
                "anomalies": anomalies,
                "recommendations": recommendations,
                "crew_analysis": crew_result,
                "timestamp": datetime.now().isoformat(),
                "project_id": project_data.get("id", "unknown")
            }
            
            # Store results in Redis for dashboard access
            self.redis_client.setex(
                f"observability:{project_data.get('id', 'current')}",
                600,  # 10 minute TTL
                json.dumps(result)
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in observability analysis: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "project_id": project_data.get("id", "unknown")
            }
