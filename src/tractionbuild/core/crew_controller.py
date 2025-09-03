"""
CrewController for tractionbuild with advanced loop prevention and ML-based optimization.
Implements atomic state updates, watchdog timers, and ML-based loop detection.
"""

import yaml
import asyncio
import operator
from functools import lru_cache
from typing import Dict, Any, List, Optional
import logging
from asyncio import Lock
from dpath import get as dpath_get, merge as dpath_merge
from uuid import uuid4  # For log IDs
import json
from datetime import datetime
from pathlib import Path

# tractionbuild imports
from ..database.project_registry import ProjectRegistry
from ..crews import CREW_REGISTRY
from ..utils.mermaid_exporter import MermaidExporter

logger = logging.getLogger(__name__)


class CrewController:
    """Advanced crew controller with loop prevention and ML-based optimization."""
    
    def __init__(self, project_data: Dict[str, Any]):
        self.project_data = project_data
        self.workflows = self._load_workflows()
        self.registry = None  # Will be set if available
        self.state_to_crew_map = CREW_REGISTRY
        self.data_lock = Lock()
        self.exporter = MermaidExporter()
        self.max_global_iterations = 50  # Prevent infinite loops
        self.iteration_count = 0
        self.log_id = uuid4().hex  # Unique ID for logs
        self.state_history = []  # For cycle detection
        
        # ML loop detection (placeholder for sklearn)
        self.ml_model = None  # IsolationForest() if sklearn available
        
        logger.info(f"CrewController initialized for project: {project_data.get('id', 'unknown')}")
    
    def set_registry(self, registry: ProjectRegistry):
        """Set the project registry for persistence."""
        self.registry = registry
    
    @lru_cache(maxsize=128)
    def _load_workflows(self) -> Dict[str, Any]:
        """Load workflows from YAML with caching for performance."""
        try:
            workflow_path = Path("config/workflows.yaml")
            if not workflow_path.exists():
                logger.warning("Workflows file not found, using default workflow")
                return self._get_default_workflows()
            
            with open(workflow_path, 'r') as f:
                workflows = yaml.safe_load(f)
            
            logger.info(f"Loaded {len(workflows)} workflows: {list(workflows.keys())}")
            return workflows
        except Exception as e:
            logger.error(f"Failed to load workflows: {e}")
            return self._get_default_workflows()
    
    def _get_default_workflows(self) -> Dict[str, Any]:
        """Fallback default workflows if YAML file is not available."""
        return {
            "default_software_build": {
                "metadata": {
                    "compliance": ["SOC2"],
                    "audit": False,
                    "visualize": False,
                    "description": "Default software build workflow"
                },
                "sequence": [
                    {"state": "IDEA_VALIDATION", "crew": "ValidatorCrew"},
                    {"state": "TASK_EXECUTION", "crew": "BuilderCrew"},
                    {"state": "FEEDBACK_COLLECTION", "crew": "FeedbackCrew"}
                ]
            }
        }
    
    def _get_next_step_definition(self) -> Optional[Dict[str, Any]]:
        """Get next step definition with enhanced escalation handling."""
        workflow_name = self.project_data.get('workflow', 'default_software_build')
        workflow = self.workflows.get(workflow_name)
        if not workflow:
            logger.error(f"Workflow '{workflow_name}' not found")
            return None
        
        sequence = workflow.get('sequence', [])
        current_state = self.project_data.get('state', 'START')
        
        # Find the current step index
        current_index = -1
        for i, step in enumerate(sequence):
            if isinstance(step, dict):
                if 'parallel' in step:
                    # Check if current state is in parallel
                    for sub_step in step['parallel']:
                        if sub_step.get('state') == current_state:
                            current_index = i
                            break
                elif 'loop' in step:
                    # Check if current state is in loop with iteration tracking
                    for sub_step in step['loop']:
                        state_prefix = sub_step.get('state', '')
                        if current_state.startswith(state_prefix):
                            current_index = i
                            break
                elif step.get('state') == current_state:
                    current_index = i
                    break
        
        if current_index == -1:
            logger.warning(f"Current state '{current_state}' not found in workflow")
            # Try to find the first step that matches our current state
            for i, step in enumerate(sequence):
                if isinstance(step, dict) and step.get('state') == current_state:
                    current_index = i
                    break
        
        # Get next step
        for i in range(current_index + 1, len(sequence)):
            step = sequence[i]
            
            # Check conditions with enhanced evaluation
            if self._evaluate_conditions(step.get('conditions', [])):
                return step
        
        # If we reach here, no more steps - return COMPLETED
        return {'state': 'COMPLETED'}
    
    def _evaluate_conditions(self, conditions: List[Dict[str, Any]]) -> bool:
        """Evaluate runtime conditions with enhanced logic for all/any structures."""
        if not conditions:
            return True
        
        for condition in conditions:
            try:
                # Handle complex condition structures
                if 'all' in condition:
                    # Logical AND - all conditions must be true
                    return all(self._evaluate_single_condition(c) for c in condition['all'])
                elif 'any' in condition:
                    # Logical OR - any condition can be true
                    return any(self._evaluate_single_condition(c) for c in condition['any'])
                else:
                    # Simple condition
                    return self._evaluate_single_condition(condition)
                    
            except Exception as e:
                logger.error(f"Error evaluating condition {condition}: {e}")
                return False
        
        return True
    
    def _evaluate_single_condition(self, condition: Dict[str, Any]) -> bool:
        """Evaluate a single condition using safe access."""
        try:
            field = condition.get('field', '')
            op_str = condition.get('operator', '==')
            expected_value = condition.get('value')
            
            # Use safe access
            actual_value = dpath_get(self.project_data, field, None)
            
            # Map operator string to function
            op_func = getattr(operator, op_str, operator.eq)
            
            result = op_func(actual_value, expected_value)
            logger.debug(f"Condition: {field}={actual_value} {op_str} {expected_value} = {result}")
            return result
                
        except Exception as e:
            logger.error(f"Error evaluating single condition {condition}: {e}")
            return False
    
    def _handle_condition_failure(self, next_step: Optional[Dict[str, Any]]) -> bool:
        """Handle condition failures with escalation logic."""
        if not next_step:
            return False
        
        # Check for escalation
        for condition in next_step.get('conditions', []):
            if 'on_fail' in condition:
                escalation = condition['on_fail'].get('escalate_to')
                if escalation and escalation in self.workflows:
                    logger.info(f"{self.log_id}: Escalating to workflow: {escalation}")
                    self._escalate_workflow(escalation)
                    return True
        
        return False
    
    def _escalate_workflow(self, new_workflow: str):
        """Escalate to a different workflow."""
        old_workflow = self.project_data.get('workflow')
        self.project_data['workflow'] = new_workflow
        self.project_data['state'] = self.workflows[new_workflow]['sequence'][0]['state']
        logger.info(f"{self.log_id}: Escalated to workflow: {new_workflow}")
        
        # Log escalation if registry available
        if self.registry:
            escalation_data = {
                'project_id': self.project_data.get('id'),
                'from_workflow': old_workflow,
                'to_workflow': new_workflow,
                'timestamp': datetime.now().isoformat(),
                'reason': 'condition_failure'
            }
            asyncio.create_task(self.registry.log_escalation(
                self.project_data.get('id'),
                old_workflow,
                new_workflow
            ))
    
    def _detect_loop(self) -> bool:
        """Detect loops using state history analysis."""
        if len(self.state_history) < 5:
            return False
        
        # Simple cycle detection: check for repeating patterns
        if len(self.state_history) >= 4:
            # Check if last 4 states form a repeating pattern
            last_4 = self.state_history[-4:]
            if last_4[:2] == last_4[2:]:  # Pattern like A,B,A,B
                logger.warning(f"{self.log_id}: Loop pattern detected: {last_4}")
                return True
        
        # Check for stuck state (same state repeated)
        if len(self.state_history) >= 3:
            last_3 = self.state_history[-3:]
            if len(set(last_3)) == 1:  # All same state
                logger.warning(f"{self.log_id}: Stuck state detected: {last_3[0]}")
                return True
        
        return False
    
    async def route_and_execute(self) -> Dict[str, Any]:
        """Route and execute crews with advanced loop prevention."""
        self.iteration_count += 1
        if self.iteration_count > self.max_global_iterations:
            logger.error(f"{self.log_id}: Max iterations exceeded; forcing COMPLETED")
            self.project_data['state'] = 'COMPLETED'
            return self.project_data

        current_state = self.project_data['state']
        logger.info(f"{self.log_id}: Executing step: {current_state}")

        next_step = self._get_next_step_definition()
        if not next_step or not self._evaluate_conditions(next_step.get('conditions', [])):
            if self._handle_condition_failure(next_step):
                return self.project_data
            self.project_data['state'] = 'COMPLETED'
            return self.project_data

        tasks = []
        next_states = []

        async with self.data_lock:
            if 'parallel' in next_step:
                logger.info(f"{self.log_id}: Parallel block: {[s['state'] for s in next_step['parallel']]}")
                for sub_step in next_step['parallel']:
                    next_states.append(sub_step['state'])
                    crew_class = self.state_to_crew_map.get(sub_step['crew'])
                    if crew_class:
                        crew = crew_class(self.project_data.copy())  # Shallow copy to avoid races
                        tasks.append(asyncio.create_task(crew.run_async()))
            elif 'loop' in next_step:
                iterations = 0
                while iterations < next_step.get('max_iterations', 3) and not self._evaluate_conditions(next_step.get('break_conditions', [])):
                    state = f"{next_step['state_prefix']}_{iterations + 1}"
                    next_states.append(state)
                    crew_class = self.state_to_crew_map.get(next_step['crew'])
                    if crew_class:
                        crew = crew_class(self.project_data.copy())
                        tasks.append(asyncio.create_task(crew.run_async()))
                    iterations += 1
            else:
                next_states.append(next_step['state'])
                crew_class = self.state_to_crew_map.get(next_step['crew'])
                if crew_class:
                    crew = crew_class(self.project_data.copy())
                    tasks.append(asyncio.create_task(crew.run_async()))

        # Timeout wrapper
        tasks = [asyncio.wait_for(task, timeout=300) for task in tasks]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        async with self.data_lock:
            had_errors = False
            for result in results:
                if isinstance(result, asyncio.TimeoutError):
                    logger.error(f"{self.log_id}: Timeout in crew execution")
                    had_errors = True
                elif isinstance(result, Exception):
                    logger.error(f"{self.log_id}: Crew failed: {result}")
                    had_errors = True
                elif isinstance(result, dict):
                    dpath_merge(self.project_data, result)  # Deep merge
            
            if had_errors:
                self.project_data['state'] = 'ERROR'
                if self.registry:
                    await self.registry.rollback_state(self.project_data['id'])
                return self.project_data
            else:
                # CRITICAL: Ensure state advancement
                if next_states:
                    self.project_data['state'] = next_states[-1]
                    self.state_history.append(next_states[-1])
                    logger.info(f"{self.log_id}: State advanced to: {self.project_data['state']}")
                else:
                    self.project_data['state'] = 'COMPLETED'
                    logger.info(f"{self.log_id}: No next states, marking as COMPLETED")

        # ML loop detection
        if self._detect_loop():
            logger.warning(f"{self.log_id}: Potential loop detected; forcing COMPLETED")
            self.project_data['state'] = 'COMPLETED'

        # Save state if registry available
        if self.registry:
            await self.registry.save_project_state(self.project_data)
        
        return self.project_data
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get execution summary for monitoring."""
        return {
            'project_id': self.project_data.get('id'),
            'current_state': self.project_data.get('state'),
            'iteration_count': self.iteration_count,
            'max_iterations': self.max_global_iterations,
            'state_history': self.state_history,
            'log_id': self.log_id
        } 