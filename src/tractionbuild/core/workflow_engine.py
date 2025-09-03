import asyncio
import logging
from typing import Dict, Any
from ..schemas import ProjectStatus
from ..database.neo4j_writer import neo4j_writer
from ..learning.export import export_training_example
from dpath import merge as dpath_merge

logger = logging.getLogger(__name__)

class WorkflowEngine:
    def __init__(self, registry, step_timeout=300):
        self.registry = registry
        self.step_timeout = step_timeout
        self.data_lock = asyncio.Lock()
    
    async def run(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Run the validation_and_launch workflow: Validator → AdvisoryBoard → Marketing → COMPLETED."""
        self.project_data = {"project": project, "artifacts": {}}
        
        try:
            # Step 1: Validator
            logger.info(f"Starting validator for project {project.get('id', 'unknown')}")
            validator = self.registry.get("validator")
            if not validator:
                raise ValueError("Validator agent not found in registry")
            
            validation_result = await asyncio.wait_for(
                validator.run(self.project_data), 
                timeout=self.step_timeout
            )

            # --- 3. Atomic State Update & Graph Ingestion ---
            async with self.data_lock:
                if isinstance(validation_result, Exception):
                    logger.error(f"Validator failed during execution: {validation_result}", exc_info=validation_result)
                    self.project_data["project"]["state"] = ProjectStatus.ERROR.value
                    self.project_data["error"] = str(validation_result)
                elif isinstance(validation_result, dict):
                    # --- NEW: Ingest artifact into Neo4j ---
                    agent_key = "validator"
                    artifact = validation_result
                    # Add a 'kind' for the schema if it doesn't exist
                    if 'kind' not in artifact:
                        artifact['kind'] = agent_key.replace('_', ' ')
                    neo4j_writer.write_step_artifact(self.project_data["project"], agent_key, artifact)
                    # ----------------------------------------
                    
                    dpath_merge(self.project_data, {"artifacts": {agent_key: artifact}})
            
            logger.info(f"Validator completed for project {project.get('id', 'unknown')}")
            
            # Step 2: Advisory Board
            logger.info(f"Starting advisory board for project {project.get('id', 'unknown')}")
            advisory = self.registry.get("advisory")
            if not advisory:
                raise ValueError("Advisory agent not found in registry")
            
            advisory_result = await asyncio.wait_for(
                advisory.run(self.project_data),
                timeout=self.step_timeout
            )

            # --- 3. Atomic State Update & Graph Ingestion ---
            async with self.data_lock:
                if isinstance(advisory_result, Exception):
                    logger.error(f"Advisory failed during execution: {advisory_result}", exc_info=advisory_result)
                    self.project_data["project"]["state"] = ProjectStatus.ERROR.value
                    self.project_data["error"] = str(advisory_result)
                elif isinstance(advisory_result, dict):
                    # --- NEW: Ingest artifact into Neo4j ---
                    agent_key = "advisory"
                    artifact = advisory_result
                    # Add a 'kind' for the schema if it doesn't exist
                    if 'kind' not in artifact:
                        artifact['kind'] = agent_key.replace('_', ' ')
                    neo4j_writer.write_step_artifact(self.project_data["project"], agent_key, artifact)
                    # ----------------------------------------
                    
                    dpath_merge(self.project_data, {"artifacts": {agent_key: artifact}})
            
            logger.info(f"Advisory board completed for project {project.get('id', 'unknown')}")
            
            # Step 3: Marketing
            logger.info(f"Starting marketing agent for project {project.get('id', 'unknown')}")
            marketing = self.registry.get("marketing")
            if not marketing:
                raise ValueError("Marketing agent not found in registry")
            
            marketing_result = await asyncio.wait_for(
                marketing.execute(self.project_data),
                timeout=self.step_timeout
            )

            # --- 3. Atomic State Update & Graph Ingestion ---
            async with self.data_lock:
                if isinstance(marketing_result, Exception):
                    logger.error(f"Marketing failed during execution: {marketing_result}", exc_info=marketing_result)
                    self.project_data["project"]["state"] = ProjectStatus.ERROR.value
                    self.project_data["error"] = str(marketing_result)
                elif isinstance(marketing_result, dict):
                    # --- NEW: Ingest artifact into Neo4j ---
                    agent_key = "marketing"
                    artifact = marketing_result
                    # Add a 'kind' for the schema if it doesn't exist
                    if 'kind' not in artifact:
                        artifact['kind'] = agent_key.replace('_', ' ')
                    neo4j_writer.write_step_artifact(self.project_data["project"], agent_key, artifact)
                    # ----------------------------------------
                    
                    dpath_merge(self.project_data, {"artifacts": {agent_key: artifact}})
            
            logger.info(f"Marketing agent completed for project {project.get('id', 'unknown')}")
            
            # Mark as completed
            self.project_data["project"]["state"] = ProjectStatus.COMPLETED.value
            
            # Export training data for learning
            try:
                export_training_example(
                    self.project_data["project"]["id"], 
                    "data/training_dataset.jsonl"
                )
            except Exception as e:
                logger.warning(f"Failed to export training data: {e}")
            
            return self.project_data
            
        except asyncio.TimeoutError:
            logger.error(f"Workflow timeout for project {project.get('id', 'unknown')}")
            self.project_data["project"]["state"] = ProjectStatus.ERROR.value
            self.project_data["error"] = "Workflow timeout"
            return self.project_data
        except Exception as e:
            logger.error(f"Workflow error for project {project.get('id', 'unknown')}: {str(e)}")
            self.project_data["project"]["state"] = ProjectStatus.ERROR.value
            self.project_data["error"] = str(e)
            return self.project_data
