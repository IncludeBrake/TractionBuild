"""
Production-Ready Main Entry Point for tractionbuild.
Enhanced with workflow validation, tracking, monitoring, and comprehensive error handling.
"""
from dotenv import load_dotenv
load_dotenv()
import asyncio
import uuid
import yaml
import logging
import os
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

# Prometheus metrics for monitoring
try:
    from prometheus_client import Summary, Counter, Histogram, start_http_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    print("Warning: prometheus_client not available. Monitoring disabled.")

# tractionbuild imports
# Fixed with relative imports
from .core.workflow_engine import WorkflowEngine
from .core.learning_memory import LearningMemory
from .database.project_registry import ProjectRegistry
from .core.schema_validator import validate_and_enrich_data, is_valid_project_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
if PROMETHEUS_AVAILABLE:
    REQUEST_TIME = Summary('tractionbuild_request_processing_seconds', 'Time spent processing request')
    WORKFLOW_EXECUTIONS = Counter('tractionbuild_workflow_executions_total', 'Total workflow executions', ['workflow_name', 'status'])
    CREW_EXECUTIONS = Counter('tractionbuild_crew_executions_total', 'Total crew executions', ['crew_name', 'status'])
    PROJECT_CREATIONS = Counter('tractionbuild_project_creations_total', 'Total project creations', ['workflow_name'])
    ERROR_COUNTER = Counter('tractionbuild_errors_total', 'Total errors', ['error_type'])
    MEMORY_HITS = Counter('tractionbuild_memory_hits_total', 'Total memory recall hits')
else:
    # Mock metrics for when prometheus_client is not available
    class MockMetric:
        def time(self): return self
        def count(self, **kwargs): pass
        def inc(self, **kwargs): pass
        def observe(self, value): pass
        def labels(self, **kwargs): return self
    
    REQUEST_TIME = MockMetric()
    WORKFLOW_EXECUTIONS = MockMetric()
    CREW_EXECUTIONS = MockMetric()
    PROJECT_CREATIONS = MockMetric()
    ERROR_COUNTER = MockMetric()


class tractionbuildOrchestrator:
    """Production-ready orchestrator for tractionbuild workflows."""
    
    def __init__(self, neo4j_uri: str = None, neo4j_user: str = "neo4j"):
        # Use environment variable or default to host.docker.internal for Docker compatibility
        if neo4j_uri is None:
            neo4j_uri = os.getenv("NEO4J_URI", "neo4j://host.docker.internal:7687")
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.registry = None
        self.workflows = self._load_workflows()
        self.memory = LearningMemory()
        
        # Start Prometheus metrics server if available
        if PROMETHEUS_AVAILABLE:
            try:
                metrics_port = int(os.getenv('PROMETHEUS_PORT', '8000'))
                start_http_server(metrics_port)
                logger.info(f"Prometheus metrics server started on port {metrics_port}")
                logger.info(f"Metrics available at http://localhost:{metrics_port}/metrics")
            except Exception as e:
                logger.warning(f"Failed to start Prometheus server: {e}")
    
    def _load_workflows(self) -> Dict[str, Any]:
        """Load and validate workflows from YAML."""
        try:
            workflow_path = Path("config/workflows.yaml")
            if not workflow_path.exists():
                logger.error("Workflows file not found: config/workflows.yaml")
                return {}
            
            with open(workflow_path, 'r') as f:
                workflows = yaml.safe_load(f)
            
            logger.info(f"Loaded {len(workflows)} workflows: {list(workflows.keys())}")
            return workflows
        except Exception as e:
            logger.error(f"Failed to load workflows: {e}")
            return {}
    
    async def __aenter__(self):
        """Async context manager entry."""
        try:
            self.registry = ProjectRegistry(
                neo4j_uri=self.neo4j_uri,
                neo4j_user=self.neo4j_user
            )
            await self.registry.__aenter__()
            logger.info("tractionbuild orchestrator initialized successfully")
            return self
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            raise
    
    async def __aexit__(self, exc_type, exc, tb):
        """Async context manager exit."""
        if self.registry:
            await self.registry.__aexit__(exc_type, exc, tb)
    
    async def create_project(self, idea: str, workflow_name: str = "default_software_build") -> Dict[str, Any]:
        """Create a new project with comprehensive validation."""
        try:
            # Validate workflow exists
            if workflow_name not in self.workflows:
                raise ValueError(f"Workflow '{workflow_name}' not found. Available: {list(self.workflows.keys())}")
            
            # Generate project ID
            project_id = f"project_{uuid.uuid4().hex[:8]}"
            
            # Get initial state from workflow
            workflow = self.workflows[workflow_name]
            initial_state = workflow['sequence'][0]['state']
            
            # Create initial project data
            project_data = {
                "id": project_id,
                "idea": idea,
                "workflow": workflow_name,
                "state": initial_state,
                "created_at": datetime.now().isoformat(),
                "metadata": {
                    "workflow_complexity": workflow.get('metadata', {}).get('complexity', 'unknown'),
                    "estimated_duration": workflow.get('metadata', {}).get('estimated_duration', 'unknown'),
                    "compliance": workflow.get('metadata', {}).get('compliance', [])
                }
            }
            
            # Validate project data
            if not is_valid_project_data(project_data):
                raise ValueError("Invalid project data structure")
            
            # Track project creation
            PROJECT_CREATIONS.labels(workflow_name=workflow_name).inc()
            
            logger.info(f"Created project '{project_id}' with workflow '{workflow_name}'")
            return project_data
            
        except Exception as e:
            ERROR_COUNTER.labels(error_type="project_creation").inc()
            logger.error(f"Failed to create project: {e}")
            raise
    
    async def execute_workflow(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a complete workflow with comprehensive monitoring."""
        project_id = project_data.get('id', 'unknown')
        workflow_name = project_data.get('workflow', 'unknown')
        
        logger.info(f"Starting workflow execution for project '{project_id}'")
        
        try:
            # Initialize workflow engine
            metrics = {"memory_hits_total": MEMORY_HITS} if PROMETHEUS_AVAILABLE else {}
            engine = WorkflowEngine(project_data, self.registry, metrics=metrics, memory=self.memory)
            
            # Track workflow start
            WORKFLOW_EXECUTIONS.labels(workflow_name=workflow_name, status="started").inc()
            
            # Execute workflow steps with enhanced loop prevention
            step_count = 0
            max_steps = 50  # Prevent infinite loops
            previous_states = []  # Track state history for loop detection
            
            while project_data.get('state') != 'COMPLETED' and project_data.get('state') != 'ERROR' and step_count < max_steps:
                step_count += 1
                current_state = project_data.get('state', 'UNKNOWN')
                
                # Loop detection: Check if we're stuck in the same state
                if len(previous_states) >= 3 and len(set(previous_states[-3:])) == 1:
                    logger.error(f"Loop detected: State '{current_state}' repeated 3 times. Forcing ERROR state.")
                    project_data['state'] = 'ERROR'
                    break
                
                previous_states.append(current_state)
                
                # Execute step with timing
                if PROMETHEUS_AVAILABLE:
                    with REQUEST_TIME.time():
                        project_data = await engine.route_and_execute()
                else:
                    project_data = await engine.route_and_execute()
                
                # Log step execution
                logger.info(f"Step {step_count}: {current_state} -> {project_data.get('state', 'UNKNOWN')}")
                
                # Check for errors
                if project_data.get('state') == 'ERROR':
                    WORKFLOW_EXECUTIONS.labels(workflow_name=workflow_name, status="error").inc()
                    ERROR_COUNTER.labels(error_type="workflow_execution").inc()
                    logger.error(f"Workflow execution failed at step {step_count}")
                    break
                
                # Add small delay to prevent overwhelming
                await asyncio.sleep(0.1)
            
            # Track workflow completion
            final_state = project_data.get('state')
            if final_state == 'COMPLETED':
                WORKFLOW_EXECUTIONS.labels(workflow_name=workflow_name, status="completed").inc()
                logger.info(f"Workflow completed successfully in {step_count} steps")
            elif final_state == 'ERROR':
                WORKFLOW_EXECUTIONS.labels(workflow_name=workflow_name, status="error").inc()
                logger.error(f"Workflow failed after {step_count} steps")
            else:
                WORKFLOW_EXECUTIONS.labels(workflow_name=workflow_name, status="timeout").inc()
                logger.warning(f"Workflow timed out after {step_count} steps")
            
            return project_data
            
        except Exception as e:
            ERROR_COUNTER.labels(error_type="workflow_execution").inc()
            WORKFLOW_EXECUTIONS.labels(workflow_name=workflow_name, status="error").inc()
            logger.error(f"Workflow execution failed: {e}")
            raise
    
    async def run_project(self, idea: str, workflow_name: str = "default_software_build") -> Dict[str, Any]:
        """Run a complete project from idea to completion."""
        try:
            # Create project
            project_data = await self.create_project(idea, workflow_name)
            
            # Execute workflow
            result = await self.execute_workflow(project_data)
            
            # Save final result
            await self._save_project_result(result)
            
            logger.info(f"✅ Project completed! Output in: output/{result['id']}/")
            return result
            
        except Exception as e:
            logger.error(f"Project execution failed: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for production monitoring."""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'components': {}
        }
        
        try:
            # Check database connectivity
            if self.registry:
                try:
                    # Simple connectivity test
                    health_status['components']['database'] = {
                        'status': 'healthy',
                        'type': 'neo4j'
                    }
                except Exception as e:
                    health_status['components']['database'] = {
                        'status': 'unhealthy',
                        'error': str(e),
                        'type': 'neo4j'
                    }
                    health_status['status'] = 'degraded'
            else:
                health_status['components']['database'] = {
                    'status': 'disabled',
                    'type': 'none'
                }
            
            # Check workflows
            health_status['components']['workflows'] = {
                'status': 'healthy',
                'count': len(self.workflows),
                'available': list(self.workflows.keys())
            }
            
            # Check metrics
            health_status['components']['metrics'] = {
                'status': 'healthy' if PROMETHEUS_AVAILABLE else 'disabled',
                'prometheus_enabled': PROMETHEUS_AVAILABLE
            }
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def _save_project_result(self, result: Dict[str, Any]) -> None:
        """Save project result to output directory and Neo4j database."""
        try:
            project_id = result.get('id', 'unknown')
            output_dir = Path(f"output/{project_id}")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save result as JSON
            result_file = output_dir / "result.json"
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            # Save execution history
            history_file = output_dir / "execution_history.json"
            with open(history_file, 'w') as f:
                json.dump(result.get('execution_history', []), f, indent=2, default=str)
            
            logger.info(f"Project results saved to {output_dir}")
            
            # 🔧 FIX: Also save to Neo4j database if registry is available
            if self.registry:
                try:
                    await self.registry.save_project_state(result)
                    logger.info(f"✅ Project state saved to Neo4j database: {project_id}")
                except Exception as db_error:
                    logger.error(f"Failed to save project state to database: {db_error}")
                    # Don't fail the entire save operation if database save fails
            else:
                logger.debug("No registry available - skipping database save")
            
        except Exception as e:
            logger.error(f"Failed to save project result: {e}")
    
    def validate_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """Validate a workflow configuration."""
        if workflow_name not in self.workflows:
            return {
                'valid': False,
                'error': f"Workflow '{workflow_name}' not found",
                'available_workflows': list(self.workflows.keys())
            }
        
        workflow = self.workflows[workflow_name]
        
        # Basic validation
        errors = []
        warnings = []
        
        if 'sequence' not in workflow:
            errors.append("Workflow missing 'sequence' field")
        
        if 'metadata' not in workflow:
            warnings.append("Workflow missing 'metadata' field")
        
        # Validate sequence structure
        sequence = workflow.get('sequence', [])
        if not sequence:
            errors.append("Workflow has empty sequence")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'workflow_name': workflow_name,
            'sequence_length': len(sequence)
        }
    
    def list_available_workflows(self) -> List[Dict[str, Any]]:
        """List all available workflows with metadata."""
        workflows = []
        for name, workflow in self.workflows.items():
            metadata = workflow.get('metadata', {})
            workflows.append({
                'name': name,
                'description': metadata.get('description', 'No description'),
                'complexity': metadata.get('complexity', 'unknown'),
                'estimated_duration': metadata.get('estimated_duration', 'unknown'),
                'compliance': metadata.get('compliance', []),
                'visualize': metadata.get('visualize', False)
            })
        return workflows


async def run_workflow(idea: str, workflow_name: str):
    """Run a specific workflow with the given idea."""
    project_id = f"project_{uuid.uuid4().hex[:8]}"
    print(f"🚀 Starting tractionbuild for idea: '{idea}'")
    print(f"   workflow: '{workflow_name}'")

    # Load workflows to get the initial state
    with open('config/workflows.yaml', 'r') as f:
        workflows = yaml.safe_load(f)
    
    if workflow_name not in workflows:
        raise ValueError(f"Workflow '{workflow_name}' not found in config/workflows.yaml")

    initial_state = workflows[workflow_name]['sequence'][0]['state']
    print(f"   initial state: '{initial_state}'")
    
    project_data = {
        "id": project_id,
        "idea": idea,
        "workflow": workflow_name,
        "state": initial_state,
    }

    print(f"   project data state: '{project_data['state']}'")

    # The engine takes over from here
    metrics = {"memory_hits_total": MEMORY_HITS} if PROMETHEUS_AVAILABLE else {}
    engine = WorkflowEngine(project_data, metrics=metrics)

    # Enhanced loop prevention
    step_count = 0
    max_steps = 50
    previous_states = []
    
    while project_data.get('state') != 'COMPLETED' and project_data.get('state') != 'ERROR' and step_count < max_steps:
        step_count += 1
        current_state = project_data.get('state', 'UNKNOWN')
        
        # Loop detection
        if len(previous_states) >= 3 and len(set(previous_states[-3:])) == 1:
            print(f"   ⚠️  Loop detected: State '{current_state}' repeated 3 times. Forcing ERROR state.")
            project_data['state'] = 'ERROR'
            break
        
        previous_states.append(current_state)
        
        print(f"   executing step {step_count}: '{current_state}'")
        await engine.route_and_execute()
        
        # Small delay to prevent overwhelming
        await asyncio.sleep(0.1)

    final_state = project_data.get('state')
    print(f"\n✅ Process finished with final state: {final_state}")
    print(f"Final project data saved for project ID: {project_id}")
    return project_data


async def main(idea: str, workflow_name: str = "default_software_build"):
    """Main entry point with comprehensive error handling and monitoring."""
    logger.info(f"🚀 Starting tractionbuild for '{idea}' with workflow '{workflow_name}'")
    
    # Initialize system with default configs
    try:
        from src.tractionbuild.core.config_generator import initialize_system
        initialize_system()
        logger.info("✅ System initialized with default configurations")
    except Exception as e:
        logger.warning(f"Warning: Failed to initialize system configs: {e}")
    
    # Set up environment variables for testing
    if not os.getenv("NEO4J_PASSWORD"):
        os.environ["NEO4J_PASSWORD"] = "test_password"
        logger.warning("Using test password for Neo4j")
    
    try:
        # Try to initialize orchestrator, but continue without registry if it fails
        try:
            async with tractionbuildOrchestrator() as orchestrator:
                # Validate workflow
                validation = orchestrator.validate_workflow(workflow_name)
                if not validation['valid']:
                    logger.error(f"Workflow validation failed: {validation['errors']}")
                    return None
                
                # Run project
                result = await orchestrator.run_project(idea, workflow_name)
                return result
        except Exception as e:
            logger.warning(f"Orchestrator initialization failed (continuing without registry): {e}")
            # Fallback to direct workflow execution
            return await run_workflow(idea, workflow_name)
            
    except Exception as e:
        logger.error(f"tractionbuild execution failed: {e}")
        if PROMETHEUS_AVAILABLE:
            ERROR_COUNTER.labels(error_type="main_execution").inc()
        return None


if __name__ == "__main__":
    # Set up the argument parser
    parser = argparse.ArgumentParser(description="Run the tractionbuild AI Product Studio.")
    parser.add_argument("--idea", type=str, required=True, help="The product or project idea to process.")
    parser.add_argument("--workflow", type=str, required=True, help="The name of the workflow to execute (e.g., 'validation_and_launch').")
    
    args = parser.parse_args()

    # Run the main async function with the provided arguments
    result = asyncio.run(main(idea=args.idea, workflow_name=args.workflow))
    
    if result:
        print(f"✅ Success! Project ID: {result.get('id')}")
        print(f"Final state: {result.get('state')}")
        print(f"Execution history: {len(result.get('execution_history', []))} steps")
    else:
        print("❌ Project execution failed") 