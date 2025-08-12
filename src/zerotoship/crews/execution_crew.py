from crewai import Crew, Agent, Task, Process
from .base_crew import BaseCrew # Import our standardized base class

class ExecutionCrew(BaseCrew):
    """
    The ExecutionCrew is a specialized team of AI agents that translates a
    validated idea into a comprehensive, actionable execution plan, complete
    with tasks, dependencies, timelines, and resource allocation.
    """

    def _create_crew(self) -> Crew:
        """
        Defines the agents and tasks that form the ExecutionCrew.
        This method is called by the BaseCrew's __init__.
        """

        # 1. --- DEFINE SPECIALIZED AGENTS ---
        
        task_decomposer = Agent(
            role="Lead Systems Analyst",
            goal="Decompose a high-level project idea into a granular list of atomic, actionable engineering tasks.",
            backstory="You are a meticulous systems analyst with a deep understanding of software development. You excel at breaking down complex requirements into clear, unambiguous tasks that a development team can execute.",
            tools=[],
            allow_delegation=False,
            verbose=True
        )

        dependency_mapper = Agent(
            role="Technical Project Manager",
            goal="Analyze a list of tasks to identify all dependencies, map them out, and identify the project's critical path.",
            backstory="You are an expert project manager with a knack for seeing the big picture. You can instantly identify which tasks block others, where work can be parallelized, and what the most critical sequence of events is for a successful project.",
            tools=[], # e.g., MermaidTools
            allow_delegation=False,
            verbose=True
        )

        resource_planner = Agent(
            role="Resource Allocation Specialist",
            goal="Create a detailed plan for allocating team members, budget, and technical resources to a project.",
            backstory="You are a strategic planner with a background in finance and project management. You are an expert at creating realistic budgets and assigning the right people to the right tasks to maximize efficiency.",
            tools=[],
            allow_delegation=False,
            verbose=True
        )
        
        execution_synthesizer = Agent(
            role="Director of Project Execution",
            goal="Synthesize all planning documents (task list, dependency graph, resource plan) into a single, comprehensive, and final execution blueprint.",
            backstory="You are the ultimate authority on project planning. Your job is to review all inputs, ensure they are coherent and complete, and produce the final, authoritative execution plan that the BuilderCrew will follow.",
            tools=[],
            allow_delegation=False,
            verbose=True
        )

        # 2. --- DEFINE THE SEQUENTIAL TASKS ---

        task_decomposition = Task(
            description="Based on the validated idea from the project data, break down the project into a list of granular, atomic tasks required for completion.",
            expected_output="A detailed list of tasks, each with a clear title and a description of what needs to be done.",
            agent=task_decomposer
        )

        task_dependency_mapping = Task(
            description="Analyze the list of tasks and map out all dependencies. Identify which tasks can be done in parallel and determine the critical path.",
            expected_output="A dependency graph (in Mermaid format) and a list of tasks that form the critical path.",
            agent=dependency_mapper,
            context=[task_decomposition] # Correctly references the Task object
        )

        task_resource_planning = Task(
            description="Create a resource plan based on the decomposed tasks. Estimate the required team skills, technology stack, and a high-level budget allocation.",
            expected_output="A resource plan document outlining team, technology, and budget requirements.",
            agent=resource_planner,
            context=[task_decomposition]
        )
        
        task_synthesis = Task(
            description="Synthesize the task list, dependency graph, and resource plan into a final, comprehensive execution blueprint. This blueprint will be the master document for the BuilderCrew.",
            expected_output="A final, unified execution plan in a well-structured document.",
            agent=execution_synthesizer,
            context=[task_decomposition, task_dependency_mapping, task_resource_planning]
        )
        
        # 3. --- ASSEMBLE AND RETURN THE CREW ---
        
        return Crew(
            agents=[task_decomposer, dependency_mapper, resource_planner, execution_synthesizer],
            tasks=[task_decomposition, task_dependency_mapping, task_resource_planning, task_synthesis],
            process=Process.sequential,
            verbose=True
        )