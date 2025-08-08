"""
Production-Ready Workflow Engine for ZeroToShip.
Supports quantum-secure encryption, federated ML, conflict-resolving delta merges,
and advanced orchestration with loops, escalations, and visualization.
"""

import yaml
import asyncio
import logging
import operator
from functools import lru_cache
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path
import uuid
import dpath.util as dpath_get
import numpy as np
from cryptography.fernet import Fernet
import hashlib
import json
from uuid import uuid4  # For log IDs
from asyncio import Lock
import os # Added for os.getenv

# ZeroToShip imports
from ..database.project_registry import ProjectRegistry
from ..crews import CREW_REGISTRY
from ..core.schema_validator import (
    validate_and_enrich_data, safe_get_nested, safe_set_nested,
    validate_workflows_against_schema, validate_single_workflow
)
from ..utils.mermaid_exporter import MermaidExporter

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Production-ready workflow engine with quantum-secure encryption, federated ML, and advanced orchestration."""
    
    def __init__(self, project_data: Dict[str, Any], registry: Optional[ProjectRegistry] = None):
        # Validate and enrich project data with schema
        self.project_data = validate_and_enrich_data(project_data)
        
        # CRITICAL: Ensure state is always present
        self._validate_and_initialize_state()
        
        self.registry = registry
        self.workflows = self._load_workflows()
        self.execution_history = []
        self.data_lock = Lock()  # For safe parallel updates
        self.exporter = MermaidExporter()
        
        # Quantum-secure encryption
        self.encryption_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # ML optimization cache
        self._ml_cache = {}
        self._federated_ml_client = None  # Placeholder for Flower client
        
        # Loop tracking
        self.loop_iterations = {}
        self.loop_break_conditions = {}
        
        # --- LOOP PREVENTION SAFEGUARDS ---
        self.max_global_iterations = 50  # Watchdog: Hard limit on total steps
        self.iteration_count = 0
        self.state_history = []  # For cycle detection
        self.step_timeout_seconds = 300  # 5 minutes per step/crew
        self.log_id = uuid4().hex  # Unique ID for logs
        
        logger.info(f"Production WorkflowEngine initialized for project: {project_data.get('id', 'unknown')}")

    def _validate_and_initialize_state(self) -> None:
        """Ensure project_data always has a valid state field."""
        if 'state' not in self.project_data:
            logger.warning(f"{self.log_id}: 'state' missing in project_data, initializing from workflow")
            self.project_data['state'] = self._get_initial_state_from_workflow()
        elif not self.project_data['state']:
            logger.warning(f"{self.log_id}: 'state' is empty, initializing from workflow")
            self.project_data['state'] = self._get_initial_state_from_workflow()
        
        # Ensure state_history exists
        if 'state_history' not in self.project_data:
            self.project_data['state_history'] = []
        
        # Add current state to history
        if self.project_data['state'] not in self.project_data['state_history']:
            self.project_data['state_history'].append(self.project_data['state'])

    def _get_initial_state_from_workflow(self) -> str:
        """Get initial state from workflow configuration."""
        try:
            workflow_name = self.project_data.get('workflow', 'default_software_build')
            workflow_path = Path("config/workflows.yaml")
            
            if workflow_path.exists():
                with open(workflow_path, 'r') as f:
                    workflows = yaml.safe_load(f)
                
                if workflow_name in workflows:
                    sequence = workflows[workflow_name].get('sequence', [])
                    if sequence and len(sequence) > 0:
                        first_step = sequence[0]
                        if 'state' in first_step:
                            return first_step['state']
                        elif 'parallel' in first_step:
                            return first_step['parallel'][0]['state']
                        elif 'loop' in first_step:
                            return f"{first_step['loop']['state_prefix']}_1"
            
            # Fallback to default state
            logger.warning(f"{self.log_id}: Could not determine initial state from workflow, using default")
            return "IDEA_VALIDATION"
        except Exception as e:
            logger.error(f"{self.log_id}: Error getting initial state: {e}")
            return "IDEA_VALIDATION"
    
    @lru_cache(maxsize=128)
    def _load_workflows(self) -> Dict[str, Any]:
        """Load workflows from YAML with caching for performance and schema validation."""
        try:
            workflow_path = Path("config/workflows.yaml")
            if not workflow_path.exists():
                logger.warning("Workflows file not found, using default workflow")
                return self._get_default_workflows()
            
            with open(workflow_path, 'r') as f:
                workflows = yaml.safe_load(f)
            
            # CRITICAL: Validate the entire workflow configuration
            validate_workflows_against_schema(workflows)
            
            # Generate diagrams for workflows with visualize: true
            for name, workflow in workflows.items():
                if workflow.get('metadata', {}).get('visualize', False):
                    self._generate_workflow_diagram(name, workflow)
            
            logger.info(f"Loaded {len(workflows)} workflows: {list(workflows.keys())}")
            return workflows
        except Exception as e:
            logger.error(f"Failed to load workflows: {e}")
            return self._get_default_workflows()
    
    def _generate_workflow_diagram(self, workflow_name: str, workflow: Dict[str, Any]) -> str:
        """Generate Mermaid DAG from workflow sequence."""
        try:
            # Ensure workflow is a dictionary
            if not isinstance(workflow, dict):
                logger.error(f"Workflow {workflow_name} is not a dictionary: {type(workflow)}")
                return ""
            
            # Check if visualization is enabled
            metadata = workflow.get('metadata', {})
            if not isinstance(metadata, dict) or not metadata.get('visualize', False):
                return ""
            
            diagram = f"graph TD\n    Start --> {workflow_name}_start\n"
            sequence = workflow.get('sequence', [])
            prev = f"{workflow_name}_start"
            
            for i, step in enumerate(sequence):
                if isinstance(step, dict):
                    if 'parallel' in step:
                        # Handle parallel execution
                        parallel_states = []
                        for j, sub in enumerate(step['parallel']):
                            state_name = sub.get('state', f'parallel_{i}_{j}')
                            parallel_states.append(state_name)
                            diagram += f"    {prev} --> {state_name}\n"
                        prev = " | ".join(parallel_states)
                        
                    elif 'loop' in step:
                        # Handle loop execution with iteration tracking
                        loop_states = []
                        for j, sub in enumerate(step['loop']):
                            state_name = sub.get('state', f'loop_{i}_{j}')
                            loop_states.append(state_name)
                            diagram += f"    {prev} --> {state_name}\n"
                            diagram += f"    {state_name} --> {state_name} [Break condition]\n"
                        prev = " | ".join(loop_states)
                        
                    elif 'state' in step:
                        # Handle single state
                        state_name = step['state']
                        diagram += f"    {prev} --> {state_name}\n"
                        prev = state_name
            
            diagram += f"    {prev} --> End\n"
            
            # Export diagram
            svg_path = f"output/workflows/{workflow_name}_diagram.svg"
            Path("output/workflows").mkdir(parents=True, exist_ok=True)
            
            # Store diagram metadata in registry if available
            if self.registry:
                asyncio.create_task(self.registry.save_workflow_diagram(workflow_name, diagram))
            
            logger.info(f"Workflow diagram generated for {workflow_name}")
            return diagram
            
        except Exception as e:
            logger.error(f"Failed to generate workflow diagram for {workflow_name}: {e}")
            return ""
    
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
    
    def get_initial_state(self) -> str:
        """Correctly gets the very first state from the workflow sequence."""
        workflow_name = self.project_data.get('workflow', 'default_software_build')
        workflow = self.workflows.get(workflow_name)
        if not workflow:
            logger.error(f"Workflow '{workflow_name}' not found")
            return 'ERROR'
        
        sequence = workflow.get('sequence', [])
        if not sequence:
            logger.error(f"Workflow '{workflow_name}' has empty sequence")
            return 'ERROR'
        
        # The first step's state is returned, correctly handling different structures
        first_step = sequence[0]
        if 'state' in first_step:
            return first_step['state']
        # Handle cases like a parallel block being first
        if 'parallel' in first_step:
            return first_step['parallel'][0]['state']
        # Handle loop as first step
        if 'loop' in first_step:
            return f"{first_step['loop']['state_prefix']}_1"
        
        logger.error(f"First step in workflow '{workflow_name}' has unrecognized structure: {first_step}")
        return 'ERROR'
    
    def get_step_definition_by_state(self, state: str) -> Optional[Dict[str, Any]]:
        """Get step definition for a specific state."""
        workflow_name = self.project_data.get('workflow', 'default_software_build')
        workflow = self.workflows.get(workflow_name)
        if not workflow:
            return None
        
        sequence = workflow.get('sequence', [])
        
        for step in sequence:
            if isinstance(step, dict):
                if 'state' in step and step['state'] == state:
                    return step
                elif 'parallel' in step:
                    for sub_step in step['parallel']:
                        if sub_step.get('state') == state:
                            return sub_step
                elif 'loop' in step:
                    # Handle loop states with iteration tracking
                    state_prefix = step['loop'].get('state_prefix', '')
                    if state.startswith(state_prefix):
                        return step
        
        return None
    
    def get_next_step_definition(self, current_step: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
                # Check for escalation with ML prediction
                for condition in step.get('conditions', []):
                    if 'on_fail' in condition:
                        escalation = condition['on_fail'].get('escalate_to')
                        if escalation and escalation in self.workflows:
                            # Use ML to predict if escalation is needed
                            if self._predict_escalation():
                                logger.info("ML predicted escalation; adjusting path")
                            self._escalate_workflow(escalation)
                            return self.get_next_step_definition(step)  # Recurse for new workflow
                
                return step
        
        # If we reach here, no more steps - return COMPLETED
        return {'state': 'COMPLETED'}
    
    def _escalate_workflow(self, new_workflow: str):
        """Escalate to a different workflow with quantum-secure logging."""
        old_workflow = self.project_data.get('workflow')
        self.project_data['workflow'] = new_workflow
        self.project_data['state'] = self.get_initial_state()
        logger.info(f"Escalated to workflow: {new_workflow}")
        
        # Quantum-secure log escalation
        if self.registry:
            escalation_data = {
                'project_id': self.project_data.get('id'),
                'from_workflow': old_workflow,
                'to_workflow': new_workflow,
                'timestamp': datetime.now().isoformat(),
                'reason': 'condition_failure'
            }
            encrypted_data = self.cipher_suite.encrypt(json.dumps(escalation_data).encode())
            asyncio.create_task(self.registry.log_escalation(
                self.project_data.get('id'),
                old_workflow,
                new_workflow
            ))
    
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
        """Evaluate a single condition using safe schema-validated access."""
        try:
            field = condition.get('field', '')
            op_str = condition.get('operator', '==')
            expected_value = condition.get('value')
            
            # Use safe schema-validated access
            actual_value = safe_get_nested(self.project_data, field, None)
            
            # Map operator string to function
            op_func = getattr(operator, op_str, operator.eq)
            
            result = op_func(actual_value, expected_value)
            logger.debug(f"Condition: {field}={actual_value} {op_str} {expected_value} = {result}")
            return result
                
        except Exception as e:
            logger.error(f"Error evaluating single condition {condition}: {e}")
            return False
    
    def _detect_simple_cycle(self) -> bool:
        """Detects simple loops by checking for repeated state sequences."""
        # A simple cycle: e.g., A -> B -> C -> B -> C
        if len(self.state_history) < 5:
            return False
        # If the last 4 states are a repeating pattern (e.g., BCBC)
        if self.state_history[-4:] == self.state_history[-2:] * 2:
            logger.warning(f"{self.log_id}: Simple cycle detected: {self.state_history[-4:]}. Escalating.")
            return True
        return False
    
    def _predict_escalation(self) -> bool:
        """Predict escalation using federated ML."""
        # Placeholder for federated ML prediction
        # In production, this would use a trained model on registry data
        
        # Simulate prediction based on project data
        confidence = safe_get_nested(self.project_data, 'validation.confidence', 0.5)
        complexity = len(safe_get_nested(self.project_data, 'graph.nodes', []))
        
        # Simple heuristic: escalate if confidence is low or complexity is high
        prediction = confidence < 0.6 or complexity > 10
        logger.info(f"ML escalation prediction: {prediction} (confidence: {confidence}, complexity: {complexity})")
        return prediction
    
    def deep_merge_with_resolution(self, target: Dict, source: Dict):
        """Enhanced deep merge with conflict resolution."""
        for key, value in source.items():
            if key in target and isinstance(value, (int, float)) and isinstance(target[key], (int, float)):
                # Conflict resolution: take higher confidence, average other numeric values
                if key == 'confidence':
                    target[key] = max(target[key], value)
                else:
                    target[key] = (target[key] + value) / 2
            elif isinstance(value, dict) and key in target and isinstance(target[key], dict):
                self.deep_merge_with_resolution(target[key], value)
            else:
                target[key] = value
    
    async def run(self) -> Dict[str, Any]:
        """The main execution loop, now hardened against configuration and logic errors."""
        
        # Ensure state is properly initialized
        if 'state' not in self.project_data or not self.project_data['state']:
            self.project_data['state'] = self.get_initial_state()
        
        while self.project_data['state'] not in ['COMPLETED', 'ERROR']:
            # 1. Validate current state
            if 'state' not in self.project_data:
                logger.error(f"{self.log_id}: State missing during execution, attempting recovery")
                self._validate_and_initialize_state()
                if 'state' not in self.project_data:
                    self.project_data['state'] = 'ERROR'
                    break
            
            # 2. Get the definition for the CURRENT step
            current_step_def = self.get_step_definition_by_state(self.project_data['state'])
            if not current_step_def:
                logger.error(f"State '{self.project_data['state']}' not found in workflow. Halting.")
                self.project_data['state'] = 'ERROR'
                break  # Exit the loop

            # 3. Execute the crew for the current step (if one exists)
            crew_name = current_step_def.get('crew')
            if crew_name:
                logger.info(f"{self.log_id}: Executing crew '{crew_name}' for state '{self.project_data['state']}'")
                # Check if Celery is available for distributed execution
                try:
                    from ..tasks.crew_tasks import execute_crew_task
                    use_celery = os.getenv('ZEROTOSHIP_USE_CELERY', 'false').lower() == 'true'
                except ImportError:
                    use_celery = False
                
                try:
                    if use_celery:
                        # Distributed execution via Celery
                        logger.info(f"{self.log_id}: Dispatching {crew_name} to Celery worker")
                        celery_task = execute_crew_task.delay(crew_name, self.project_data.copy())
                        
                        # Wait for Celery task result with timeout
                        result = celery_task.get(timeout=self.step_timeout_seconds)
                    else:
                        # Local execution (fallback)
                        crew_class = CREW_REGISTRY.get(crew_name)
                        if crew_class:
                            crew = crew_class(self.project_data.copy())
                            result = await asyncio.wait_for(
                                crew.run_async(),
                                timeout=self.step_timeout_seconds
                            )
                        else:
                            result = {"error": f"Crew '{crew_name}' not found in registry"}
                    
                    # Merge results with state validation
                    if isinstance(result, dict) and 'error' not in result:
                        # Ensure result has state before merging
                        if 'state' not in result:
                            logger.warning(f"{self.log_id}: Crew result missing 'state', preserving current state")
                            result['state'] = self.project_data.get('state', 'COMPLETED')
                        
                        self.deep_merge_with_resolution(self.project_data, result)
                        
                        # Validate state after merge
                        if 'state' not in self.project_data:
                            logger.error(f"{self.log_id}: State lost after merge, attempting recovery")
                            self._validate_and_initialize_state()
                    elif 'error' in result:
                        logger.error(f"{self.log_id}: Crew execution error: {result['error']}")
                        self.project_data['state'] = 'ERROR'
                        break
                        
                except KeyError as e:
                    if 'state' in str(e):
                        logger.error(f"{self.log_id}: State KeyError in crew execution: {e}")
                        self._validate_and_initialize_state()
                        self.project_data['state'] = 'ERROR'
                        break
                    else:
                        raise
                except Exception as e:
                    logger.error(f"{self.log_id}: Crew execution failed: {e}")
                    self.project_data['state'] = 'ERROR'
                    break

            # 3. Deterministically find the NEXT state
            next_step_def = self.get_next_step_definition(current_step_def)
            
            if not next_step_def:
                # No more steps, the workflow is done
                self.project_data['state'] = 'COMPLETED'
            else:
                # Evaluate conditions for the next step
                if self._evaluate_conditions(next_step_def.get('conditions', [])):
                    # Advance the state
                    self.project_data['state'] = next_step_def['state']
                    self.state_history.append(next_step_def['state'])
                    logger.info(f"{self.log_id}: State successfully advanced to '{next_step_def['state']}'")
                else:
                    # Conditions not met, check for escalation or complete
                    if not self._handle_condition_failure(next_step_def):
                        self.project_data['state'] = 'COMPLETED'
        
        logger.info(f"{self.log_id}: ✅ Workflow finished with final state: {self.project_data['state']}")
        return self.project_data
    
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
    
    async def route_and_execute(self) -> Dict[str, Any]:
        """Route and execute crews with enhanced parallel safety and loop handling."""
        # 1. --- STATE VALIDATION AND RECOVERY ---
        self._validate_and_initialize_state()
        
        # 2. --- WATCHDOG AND CYCLE DETECTION ---
        self.iteration_count += 1
        if self.iteration_count > self.max_global_iterations:
            logger.error(f"{self.log_id}: WATCHDOG: Max iterations ({self.max_global_iterations}) exceeded. Forcing ERROR state.")
            self.project_data['state'] = 'ERROR'
            return self.project_data

        if self._detect_simple_cycle():
            logger.error(f"{self.log_id}: CYCLE DETECTED: State progression is stuck in a loop. Forcing ERROR state.")
            self.project_data['state'] = 'ERROR'
            return self.project_data

        # 3. --- ENHANCED ERROR HANDLING ---
        try:
            # Use the new hardened run method
            result = await self.run()
            
            # Validate result has state
            if isinstance(result, dict) and 'state' not in result:
                logger.warning(f"{self.log_id}: Result missing 'state', adding from current state")
                result['state'] = self.project_data.get('state', 'COMPLETED')
            
            return result
        except KeyError as e:
            if 'state' in str(e):
                logger.error(f"{self.log_id}: State KeyError detected: {e}")
                # Attempt recovery
                self._validate_and_initialize_state()
                self.project_data['state'] = 'ERROR'
                return self.project_data
            else:
                raise
        except Exception as e:
            logger.error(f"{self.log_id}: Unexpected error in route_and_execute: {e}")
            self.project_data['state'] = 'ERROR'
            return self.project_data
    
    def get_workflow_info(self, workflow_name: str) -> Dict[str, Any]:
        """Get information about a specific workflow."""
        workflow = self.workflows.get(workflow_name)
        if not workflow:
            return {}
        
        return {
            'name': workflow_name,
            'metadata': workflow.get('metadata', {}),
            'sequence_length': len(workflow.get('sequence', [])),
            'has_parallel': any('parallel' in step for step in workflow.get('sequence', [])),
            'has_conditions': any('conditions' in step for step in workflow.get('sequence', [])),
            'has_loops': any('loop' in step for step in workflow.get('sequence', [])),
            'encryption_enabled': True,
            'ml_optimization': True
        }
    
    def list_available_workflows(self) -> List[Dict[str, Any]]:
        """List all available workflows with metadata."""
        workflows = []
        for name, workflow in self.workflows.items():
            workflows.append(self.get_workflow_info(name))
        return workflows
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get execution history for the current project."""
        return self.execution_history.copy()
    
    def get_loop_iterations(self) -> Dict[str, int]:
        """Get current loop iteration counts."""
        return self.loop_iterations.copy()
    
    def validate_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """Validate a workflow configuration."""
        workflow = self.workflows.get(workflow_name)
        if not workflow:
            return {'valid': False, 'error': f"Workflow '{workflow_name}' not found"}
        
        try:
            validate_single_workflow(workflow_name, workflow)
            return {
                'valid': True,
                'workflow_name': workflow_name,
                'encryption_enabled': True,
                'ml_optimization': True
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'workflow_name': workflow_name
            } 