"""
CrewAI Adapter for ZeroToShip.
Provides a standardized interface wrapper around CrewAI library.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

try:
    from crewai import Agent, Task, Crew, Process
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Agent = None
    Task = None
    Crew = None
    Process = None

logger = logging.getLogger(__name__)


class CrewAIAdapter(ABC):
    """
    Base adapter class that wraps CrewAI functionality.
    Provides the standardized run() interface expected by our CrewRouter.
    """

    def __init__(self, project_data: Dict[str, Any]):
        """
        Initialize the adapter with project data.

        Args:
            project_data: Dictionary containing project information
        """
        if not CREWAI_AVAILABLE:
            raise ImportError(
                "CrewAI is not installed. Install with: pip install crewai"
            )

        self.project_data = project_data
        self.crew_name = self.__class__.__name__
        logger.info(f"Initializing {self.crew_name} with CrewAI adapter")

    @abstractmethod
    def create_agents(self) -> List[Agent]:
        """
        Create and return the agents for this crew.
        Subclasses must implement this method.

        Returns:
            List of CrewAI Agent objects
        """
        pass

    @abstractmethod
    def create_tasks(self, agents: List[Agent]) -> List[Task]:
        """
        Create and return the tasks for this crew.
        Subclasses must implement this method.

        Args:
            agents: List of agents created by create_agents()

        Returns:
            List of CrewAI Task objects
        """
        pass

    def get_next_state(self) -> str:
        """
        Determine the next workflow state after this crew completes.
        Override this method in subclasses to customize state transitions.

        Returns:
            Name of the next workflow state
        """
        return "COMPLETED"

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the crew and return standardized results.
        This is the interface expected by CrewRouter.

        Args:
            context: Dictionary with workflow context and data

        Returns:
            Standardized result dictionary with status, message, data, next_state
        """
        logger.info(f"[{self.crew_name}] Starting execution")

        try:
            # Update project data with context
            self.project_data.update(context)

            # Create agents and tasks
            agents = self.create_agents()
            tasks = self.create_tasks(agents)

            logger.info(f"[{self.crew_name}] Created {len(agents)} agents and {len(tasks)} tasks")

            # Create and run the crew
            crew = Crew(
                agents=agents,
                tasks=tasks,
                process=Process.sequential,
                verbose=True
            )

            logger.info(f"[{self.crew_name}] Executing crew...")

            # Run crew in thread pool to avoid blocking
            result = await asyncio.to_thread(crew.kickoff)

            logger.info(f"[{self.crew_name}] Crew execution completed")

            # Extract result data
            if hasattr(result, 'raw'):
                result_data = result.raw
            elif hasattr(result, 'result'):
                result_data = result.result
            else:
                result_data = str(result)

            # Prepare output data
            output_key = f"{self.crew_name.lower().replace('crew', '')}_output"
            output_data = {
                output_key: result_data,
                "crew_name": self.crew_name,
                "agent_count": len(agents),
                "task_count": len(tasks)
            }

            # Return standardized format
            return {
                "status": "success",
                "message": f"[SUCCESS] {self.crew_name} completed successfully",
                "data": output_data,
                "next_state": self.get_next_state()
            }

        except Exception as e:
            logger.exception(f"[{self.crew_name}] Execution failed: {e}")
            return {
                "status": "error",
                "message": f"[ERROR] {self.crew_name} failed: {str(e)}",
                "data": {},
                "error_type": type(e).__name__,
                "next_state": "ERROR"
            }


class SimpleAgent:
    """
    Fallback agent class when CrewAI is not available.
    Allows testing the adapter interface without CrewAI installed.
    """
    def __init__(self, role: str, goal: str, backstory: str, **kwargs):
        self.role = role
        self.goal = goal
        self.backstory = backstory


class SimpleTask:
    """
    Fallback task class when CrewAI is not available.
    Allows testing the adapter interface without CrewAI installed.
    """
    def __init__(self, description: str, agent: Any, expected_output: str = "", **kwargs):
        self.description = description
        self.agent = agent
        self.expected_output = expected_output
