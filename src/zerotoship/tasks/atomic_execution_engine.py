"""
Atomic Execution Engine for ZeroToShip.
Handles task decomposition, atomic execution planning, and dependency mapping.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json

from pydantic import BaseModel, Field


@dataclass
class AtomicTask:
    """Represents an atomic task for execution."""
    id: str
    name: str
    description: str
    task_type: str  # validation, execution, build, marketing, feedback
    estimated_duration: int  # minutes
    complexity: str  # simple, medium, complex
    priority: str  # high, medium, low
    dependencies: List[str]
    resources: List[str]
    metadata: Dict[str, Any]


class TaskDecomposerConfig(BaseModel):
    """Configuration for the Task Decomposer."""
    
    max_task_duration: int = Field(default=480, description="Maximum task duration in minutes")
    enable_parallel_decomposition: bool = Field(default=True, description="Enable parallel task decomposition")
    enable_complexity_analysis: bool = Field(default=True, description="Enable complexity analysis")
    enable_resource_optimization: bool = Field(default=True, description="Enable resource optimization")
    enable_dependency_resolution: bool = Field(default=True, description="Enable dependency resolution")
    atomic_task_threshold: int = Field(default=60, description="Maximum atomic task duration in minutes")


class TaskDecomposer:
    """Atomic Execution Engine for task decomposition and planning."""
    
    def __init__(self, config: Optional[TaskDecomposerConfig] = None):
        """Initialize the Task Decomposer."""
        self.config = config or TaskDecomposerConfig()
        self.logger = logging.getLogger(__name__)
        self.decomposition_history: List[Dict[str, Any]] = []
        
    def decompose(self, idea: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Decompose an idea into atomic tasks.
        
        Args:
            idea: The idea to decompose
            metadata: Additional metadata for decomposition
            
        Returns:
            Task graph with atomic tasks and dependencies
        """
        self.logger.info(f"Decomposing idea: {idea[:100]}...")
        
        metadata = metadata or {}
        
        # Create initial task structure
        task_graph = {
            "nodes": [],
            "edges": [],
            "metadata": {
                "idea": idea,
                "created_at": datetime.now().isoformat(),
                "decomposition_config": self.config.dict(),
                "user_metadata": metadata
            }
        }
        
        # Generate atomic tasks based on idea type and metadata
        atomic_tasks = self._generate_atomic_tasks(idea, metadata)
        
        # Add tasks to graph
        for task in atomic_tasks:
            task_graph["nodes"].append({
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "type": task.task_type,
                "estimated_duration": task.estimated_duration,
                "complexity": task.complexity,
                "priority": task.priority,
                "dependencies": task.dependencies,
                "resources": task.resources,
                "metadata": task.metadata
            })
            
            # Add dependency edges
            for dep_id in task.dependencies:
                task_graph["edges"].append({
                    "from": dep_id,
                    "to": task.id,
                    "type": "dependency"
                })
        
        # Optimize task graph if enabled
        if self.config.enable_resource_optimization:
            task_graph = self._optimize_task_graph(task_graph)
        
        # Resolve dependencies if enabled
        if self.config.enable_dependency_resolution:
            task_graph = self._resolve_dependencies(task_graph)
        
        # Store decomposition history
        self.decomposition_history.append({
            "timestamp": datetime.now().isoformat(),
            "idea": idea,
            "task_count": len(task_graph["nodes"]),
            "metadata": metadata
        })
        
        self.logger.info(f"Decomposed idea into {len(task_graph['nodes'])} atomic tasks")
        return task_graph
    
    def _generate_atomic_tasks(self, idea: str, metadata: Dict[str, Any]) -> List[AtomicTask]:
        """Generate atomic tasks based on idea and metadata."""
        tasks = []
        task_id_counter = 0
        
        # Determine project type and complexity
        project_type = self._determine_project_type(idea, metadata)
        complexity = self._analyze_complexity(idea, metadata)
        
        # Generate validation tasks
        validation_tasks = self._generate_validation_tasks(idea, project_type, complexity)
        tasks.extend(validation_tasks)
        
        # Generate execution tasks
        execution_tasks = self._generate_execution_tasks(idea, project_type, complexity)
        tasks.extend(execution_tasks)
        
        # Generate build tasks
        build_tasks = self._generate_build_tasks(idea, project_type, complexity)
        tasks.extend(build_tasks)
        
        # Generate marketing tasks
        marketing_tasks = self._generate_marketing_tasks(idea, project_type, complexity)
        tasks.extend(marketing_tasks)
        
        # Generate feedback tasks
        feedback_tasks = self._generate_feedback_tasks(idea, project_type, complexity)
        tasks.extend(feedback_tasks)
        
        # Assign IDs and dependencies
        for i, task in enumerate(tasks):
            task.id = f"task_{i:03d}"
            task_id_counter = i + 1
        
        # Resolve dependencies between tasks
        self._resolve_task_dependencies(tasks)
        
        return tasks
    
    def _determine_project_type(self, idea: str, metadata: Dict[str, Any]) -> str:
        """Determine the type of project based on idea and metadata."""
        idea_lower = idea.lower()
        
        if any(word in idea_lower for word in ['web', 'app', 'platform', 'saas']):
            return 'web_application'
        elif any(word in idea_lower for word in ['mobile', 'app', 'ios', 'android']):
            return 'mobile_application'
        elif any(word in idea_lower for word in ['api', 'service', 'backend']):
            return 'api_service'
        elif any(word in idea_lower for word in ['ai', 'ml', 'machine learning']):
            return 'ai_ml_project'
        elif any(word in idea_lower for word in ['ecommerce', 'shop', 'store']):
            return 'ecommerce_platform'
        else:
            return 'general_project'
    
    def _analyze_complexity(self, idea: str, metadata: Dict[str, Any]) -> str:
        """Analyze the complexity of the project."""
        idea_length = len(idea.split())
        compliance_requirements = metadata.get('compliance', [])
        
        if idea_length > 100 or len(compliance_requirements) > 2:
            return 'complex'
        elif idea_length > 50 or len(compliance_requirements) > 0:
            return 'medium'
        else:
            return 'simple'
    
    def _generate_validation_tasks(self, idea: str, project_type: str, complexity: str) -> List[AtomicTask]:
        """Generate validation tasks."""
        tasks = []
        
        # Market research task
        tasks.append(AtomicTask(
            id="",
            name="Market Research",
            description=f"Conduct comprehensive market research for: {idea}",
            task_type="validation",
            estimated_duration=120 if complexity == 'complex' else 60,
            complexity=complexity,
            priority="high",
            dependencies=[],
            resources=["market_research_tool", "competitor_analysis_tool"],
            metadata={"project_type": project_type}
        ))
        
        # Compliance check task
        tasks.append(AtomicTask(
            id="",
            name="Compliance Check",
            description=f"Check compliance requirements for: {idea}",
            task_type="validation",
            estimated_duration=90 if complexity == 'complex' else 45,
            complexity=complexity,
            priority="high",
            dependencies=["task_000"],  # Depends on market research
            resources=["compliance_tool", "audit_trail_tool"],
            metadata={"project_type": project_type}
        ))
        
        # Risk assessment task
        tasks.append(AtomicTask(
            id="",
            name="Risk Assessment",
            description=f"Conduct risk assessment for: {idea}",
            task_type="validation",
            estimated_duration=60 if complexity == 'complex' else 30,
            complexity=complexity,
            priority="medium",
            dependencies=["task_000", "task_001"],  # Depends on market research and compliance
            resources=["risk_assessment_tool"],
            metadata={"project_type": project_type}
        ))
        
        return tasks
    
    def _generate_execution_tasks(self, idea: str, project_type: str, complexity: str) -> List[AtomicTask]:
        """Generate execution tasks."""
        tasks = []
        
        # Task decomposition
        tasks.append(AtomicTask(
            id="",
            name="Task Decomposition",
            description=f"Decompose project into atomic tasks: {idea}",
            task_type="execution",
            estimated_duration=60 if complexity == 'complex' else 30,
            complexity=complexity,
            priority="high",
            dependencies=["task_002"],  # Depends on risk assessment
            resources=["task_decomposition_tool"],
            metadata={"project_type": project_type}
        ))
        
        # Resource planning
        tasks.append(AtomicTask(
            id="",
            name="Resource Planning",
            description=f"Plan resource allocation for: {idea}",
            task_type="execution",
            estimated_duration=90 if complexity == 'complex' else 45,
            complexity=complexity,
            priority="high",
            dependencies=["task_003"],  # Depends on task decomposition
            resources=["resource_planning_tool", "cost_estimator"],
            metadata={"project_type": project_type}
        ))
        
        # Timeline planning
        tasks.append(AtomicTask(
            id="",
            name="Timeline Planning",
            description=f"Create execution timeline for: {idea}",
            task_type="execution",
            estimated_duration=60 if complexity == 'complex' else 30,
            complexity=complexity,
            priority="medium",
            dependencies=["task_003", "task_004"],  # Depends on task decomposition and resource planning
            resources=["timeline_tool"],
            metadata={"project_type": project_type}
        ))
        
        return tasks
    
    def _generate_build_tasks(self, idea: str, project_type: str, complexity: str) -> List[AtomicTask]:
        """Generate build tasks."""
        tasks = []
        
        # Architecture design
        tasks.append(AtomicTask(
            id="",
            name="Architecture Design",
            description=f"Design system architecture for: {idea}",
            task_type="build",
            estimated_duration=180 if complexity == 'complex' else 90,
            complexity=complexity,
            priority="high",
            dependencies=["task_005"],  # Depends on timeline planning
            resources=["architecture_designer", "secure_coder_gpt"],
            metadata={"project_type": project_type}
        ))
        
        # Security audit
        tasks.append(AtomicTask(
            id="",
            name="Security Audit",
            description=f"Conduct security audit for: {idea}",
            task_type="build",
            estimated_duration=120 if complexity == 'complex' else 60,
            complexity=complexity,
            priority="high",
            dependencies=["task_006"],  # Depends on architecture design
            resources=["security_auditor", "compliance_checker"],
            metadata={"project_type": project_type}
        ))
        
        # Code generation
        tasks.append(AtomicTask(
            id="",
            name="Code Generation",
            description=f"Generate MVP code for: {idea}",
            task_type="build",
            estimated_duration=240 if complexity == 'complex' else 120,
            complexity=complexity,
            priority="high",
            dependencies=["task_006", "task_007"],  # Depends on architecture design and security audit
            resources=["secure_coder_gpt", "code_generator"],
            metadata={"project_type": project_type}
        ))
        
        # Testing strategy
        tasks.append(AtomicTask(
            id="",
            name="Testing Strategy",
            description=f"Design testing strategy for: {idea}",
            task_type="build",
            estimated_duration=90 if complexity == 'complex' else 45,
            complexity=complexity,
            priority="medium",
            dependencies=["task_008"],  # Depends on code generation
            resources=["test_generator", "quality_analyzer"],
            metadata={"project_type": project_type}
        ))
        
        return tasks
    
    def _generate_marketing_tasks(self, idea: str, project_type: str, complexity: str) -> List[AtomicTask]:
        """Generate marketing tasks."""
        tasks = []
        
        # Brand positioning
        tasks.append(AtomicTask(
            id="",
            name="Brand Positioning",
            description=f"Develop brand positioning for: {idea}",
            task_type="marketing",
            estimated_duration=90 if complexity == 'complex' else 45,
            complexity=complexity,
            priority="medium",
            dependencies=["task_002"],  # Depends on risk assessment
            resources=["brand_analyzer", "positioning_tool"],
            metadata={"project_type": project_type}
        ))
        
        # Content creation
        tasks.append(AtomicTask(
            id="",
            name="Content Creation",
            description=f"Create marketing content for: {idea}",
            task_type="marketing",
            estimated_duration=120 if complexity == 'complex' else 60,
            complexity=complexity,
            priority="medium",
            dependencies=["task_009"],  # Depends on brand positioning
            resources=["content_api", "copy_generator"],
            metadata={"project_type": project_type}
        ))
        
        # Launch strategy
        tasks.append(AtomicTask(
            id="",
            name="Launch Strategy",
            description=f"Develop launch strategy for: {idea}",
            task_type="marketing",
            estimated_duration=90 if complexity == 'complex' else 45,
            complexity=complexity,
            priority="medium",
            dependencies=["task_009", "task_010"],  # Depends on brand positioning and content creation
            resources=["launch_planner", "market_entry_tool"],
            metadata={"project_type": project_type}
        ))
        
        return tasks
    
    def _generate_feedback_tasks(self, idea: str, project_type: str, complexity: str) -> List[AtomicTask]:
        """Generate feedback tasks."""
        tasks = []
        
        # Quality assessment
        tasks.append(AtomicTask(
            id="",
            name="Quality Assessment",
            description=f"Conduct quality assessment for: {idea}",
            task_type="feedback",
            estimated_duration=60 if complexity == 'complex' else 30,
            complexity=complexity,
            priority="medium",
            dependencies=["task_008", "task_011"],  # Depends on testing strategy and launch strategy
            resources=["quality_analyzer", "user_experience_tester"],
            metadata={"project_type": project_type}
        ))
        
        # Feedback collection
        tasks.append(AtomicTask(
            id="",
            name="Feedback Collection",
            description=f"Collect user feedback for: {idea}",
            task_type="feedback",
            estimated_duration=90 if complexity == 'complex' else 45,
            complexity=complexity,
            priority="low",
            dependencies=["task_012"],  # Depends on quality assessment
            resources=["feedback_collector", "survey_analyzer"],
            metadata={"project_type": project_type}
        ))
        
        return tasks
    
    def _resolve_task_dependencies(self, tasks: List[AtomicTask]) -> None:
        """Resolve dependencies between tasks."""
        # This is a simplified dependency resolution
        # In a real implementation, this would be more sophisticated
        for task in tasks:
            if task.task_type == "validation":
                # Validation tasks have no dependencies
                pass
            elif task.task_type == "execution":
                # Execution tasks depend on validation
                task.dependencies = [t.id for t in tasks if t.task_type == "validation"]
            elif task.task_type == "build":
                # Build tasks depend on execution
                task.dependencies = [t.id for t in tasks if t.task_type == "execution"]
            elif task.task_type == "marketing":
                # Marketing tasks depend on validation
                task.dependencies = [t.id for t in tasks if t.task_type == "validation"]
            elif task.task_type == "feedback":
                # Feedback tasks depend on build and marketing
                task.dependencies = [t.id for t in tasks if t.task_type in ["build", "marketing"]]
    
    def _optimize_task_graph(self, task_graph: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize the task graph for better execution."""
        # Sort tasks by priority and dependencies
        nodes = task_graph["nodes"]
        nodes.sort(key=lambda x: (
            {'high': 0, 'medium': 1, 'low': 2}.get(x['priority'], 1),
            len(x['dependencies'])
        ))
        
        # Update graph with optimized node order
        task_graph["nodes"] = nodes
        task_graph["metadata"]["optimization_level"] = "optimized"
        
        return task_graph
    
    def _resolve_dependencies(self, task_graph: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve and validate dependencies in the task graph."""
        # Create node lookup
        node_lookup = {node["id"]: node for node in task_graph["nodes"]}
        
        # Validate dependencies
        for node in task_graph["nodes"]:
            valid_deps = []
            for dep_id in node["dependencies"]:
                if dep_id in node_lookup:
                    valid_deps.append(dep_id)
                else:
                    self.logger.warning(f"Invalid dependency {dep_id} for node {node['id']}")
            
            node["dependencies"] = valid_deps
        
        return task_graph
    
    def get_decomposition_stats(self) -> Dict[str, Any]:
        """Get decomposition statistics."""
        return {
            "total_decompositions": len(self.decomposition_history),
            "average_tasks_per_decomposition": sum(
                h["task_count"] for h in self.decomposition_history
            ) / max(len(self.decomposition_history), 1),
            "last_decomposition": self.decomposition_history[-1] if self.decomposition_history else None
        } 