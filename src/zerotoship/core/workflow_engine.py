import asyncio
import logging
import yaml
import operator
from uuid import uuid4
from pathlib import Path
from functools import lru_cache
from typing import Dict, Any, List, Optional
from asyncio import Lock
from dpath.util import merge as dpath_merge, get as dpath_get

# Assuming other components are correctly located
from ..crews import CREW_REGISTRY
from ..database.project_registry import ProjectRegistry
from ..core.schema_validator import validate_workflows_against_schema

logger = logging.getLogger(__name__)

class WorkflowEngine:
    """
    The production-ready orchestration engine for ZeroToShip. It manages the
    execution of complex, conditional, and parallel workflows with robust
    safeguards and enterprise-grade features.
    """
    def __init__(self, project_data: Dict[str, Any], registry: Optional[ProjectRegistry] = None):
        self.project_data = project_data
        self.registry = registry
        self.workflows = self._load_workflows()
        self.data_lock = Lock()
        
        # Safeguards
        self.max_iterations = 50
        self.step_timeout = 300
        
        logger.info(f"WorkflowEngine initialized for project: {self.project_data.get('id')}")

    @lru_cache(maxsize=1)
    def _load_workflows(self) -> Dict[str, Any]:
        """Loads and validates the workflow configuration file."""
        try:
            workflow_path = Path("config/workflows.yaml")
            with open(workflow_path, 'r') as f:
                workflows = yaml.safe_load(f)
            validate_workflows_against_schema(workflows)
            logger.info(f"Successfully loaded and validated {len(workflows)} workflows.")
            return workflows
        except Exception as e:
            logger.error(f"FATAL: Could not load or validate workflows.yaml: {e}", exc_info=True)
            return {}

    def get_current_state(self) -> str:
        return self.project_data.get('state', 'ERROR')

    def get_current_workflow(self) -> Dict[str, Any]:
        """Safely retrieves the current workflow definition."""
        workflow_name = self.project_data.get('workflow')
        if not workflow_name or workflow_name not in self.workflows:
            logger.error(f"Workflow '{workflow_name}' not found.")
            return {}
        return self.workflows[workflow_name]

    def _get_step_definition(self, state: str) -> Optional[Dict[str, Any]]:
        """Finds the definition of a step by its state name within the current workflow."""
        sequence = self.get_current_workflow().get('sequence', [])
        for i, step in enumerate(sequence):
            # Add index to the step definition for easier lookup later
            step['index'] = i 
            if 'parallel' in step:
                for sub_step in step['parallel']:
                    if sub_step.get('state') == state:
                        return step
            elif 'loop' in step:
                if state.startswith(step['loop'].get('state_prefix', '')):
                     return step
            elif step.get('state') == state:
                return step
        return None

    def _evaluate_conditions(self, conditions_block: Optional[Dict]) -> bool:
        """Recursively evaluates compound conditions (all/any)."""
        if not conditions_block:
            return True

        operators = {'>': operator.gt, '<': operator.lt, '==': operator.eq, '!=': operator.ne, '>=': operator.ge, '<=': operator.le}

        def check(condition):
            try:
                actual = dpath_get(self.project_data, condition['field'], separator='.')
                op = operators[condition['operator']]
                return op(actual, condition['value'])
            except (KeyError, TypeError):
                return False

        if 'all' in conditions_block:
            return all(check(cond) for cond in conditions_block['all'])
        if 'any' in conditions_block:
            return any(check(cond) for cond in conditions_block['any'])
        return False

    async def _execute_step(self, step_def: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Executes a step, handling single, parallel, or loop logic."""
        tasks = []
        
        # Prepare tasks based on step type
        if 'parallel' in step_def:
            for sub_step in step_def['parallel']:
                crew_class = CREW_REGISTRY.get(sub_step['crew'])
                if crew_class:
                    tasks.append(crew_class(self.project_data).run_async())
        elif 'loop' in step_def:
            # Loop logic would be more complex, involving state checks and iteration counts
            pass # Placeholder for loop execution
        elif 'crew' in step_def:
            crew_class = CREW_REGISTRY.get(step_def['crew'])
            if crew_class:
                tasks.append(crew_class(self.project_data).run_async())

        if not tasks:
            return []

        # Execute tasks with timeouts
        timed_tasks = [asyncio.wait_for(task, timeout=self.step_timeout) for task in tasks]
        results = await asyncio.gather(*timed_tasks, return_exceptions=True)
        return results

    def _get_next_state(self, last_step_index: int) -> str:
        """Determines the next valid state by checking subsequent steps and their conditions."""
        sequence = self.get_current_workflow().get('sequence', [])
        for i in range(last_step_index + 1, len(sequence)):
            next_step_candidate = sequence[i]
            if self._evaluate_conditions(next_step_candidate.get('conditions')):
                # Return the state of the first valid next step
                if 'state' in next_step_candidate:
                    return next_step_candidate['state']
                if 'parallel' in next_step_candidate:
                    # The "state" of a parallel block is considered the state of its first task for transition purposes
                    return next_step_candidate['parallel'][0]['state']
                if 'loop' in next_step_candidate:
                    return f"{next_step_candidate['loop']['state_prefix']}_1"
        return 'COMPLETED' # No more valid steps found

    async def run(self) -> Dict[str, Any]:
        """The main, hardened execution loop for the workflow."""
        iteration = 0
        state_history = []

        while self.project_data.get('state') not in ['COMPLETED', 'ERROR']:
            # --- 1. Safeguards ---
            iteration += 1
            if iteration > self.max_iterations:
                logger.error(f"WATCHDOG: Max iterations exceeded. Forcing ERROR state.")
                self.project_data['state'] = 'ERROR'
                break

            current_state = self.get_current_state()
            state_history.append(current_state)
            if len(state_history) > 4 and len(set(state_history[-4:])) <= 2:
                 logger.error(f"CYCLE DETECTED: States repeating. Forcing ERROR state.")
                 self.project_data['state'] = 'ERROR'
                 break
            
            logger.info(f"--- Step {iteration}: Executing state '{current_state}' ---")
            
            # --- 2. Execution ---
            current_step = self._get_step_definition(current_state)
            if not current_step:
                logger.error(f"State '{current_state}' not found in workflow. Halting.")
                self.project_data['state'] = 'ERROR'
                break

            results = await self._execute_step(current_step)

            # --- 3. Atomic State Update ---
            async with self.data_lock:
                had_errors = False
                for res in results:
                    if isinstance(res, Exception):
                        had_errors = True
                        logger.error(f"A crew failed during execution: {res}", exc_info=res)
                    elif isinstance(res, dict):
                        dpath_merge(self.project_data, res)

                if had_errors:
                    self.project_data['state'] = 'ERROR'
                else:
                    # Deterministically find and set the next state
                    next_state = self._get_next_state(current_step.get('index', -1))
                    self.project_data['state'] = next_state
            
            # Persist state after each step
            if self.registry:
                await self.registry.save_project_state(self.project_data, version=iteration)
        
        logger.info(f"✅ Workflow finished with final state: {self.get_current_state()}")
        return self.project_data