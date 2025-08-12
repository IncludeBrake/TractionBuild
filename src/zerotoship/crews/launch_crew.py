from crewai import Crew, Agent, Task, Process
from .base_crew import BaseCrew # Import our standardized base class

class LaunchCrew(BaseCrew):
    """
    The LaunchCrew is a specialized team of AI agents that orchestrates the
    entire launch process, from pre-launch strategy and day-of execution
    to post-launch analysis and momentum building.
    """

    def _create_crew(self) -> Crew:
        """
        Defines the agents and tasks that form the LaunchCrew.
        """

        # 1. --- DEFINE SPECIALIZED AGENTS ---

        launch_strategist = Agent(
            role="Head of Product Launch",
            goal="Develop a comprehensive, timeline-driven launch plan that covers all technical, marketing, and communication aspects.",
            backstory="You are a master strategist with a track record of executing flawless product launches for major tech companies. You think in terms of checklists, milestones, and contingency plans.",
            tools=[],
            allow_delegation=False,
            verbose=True
        )

        execution_coordinator = Agent(
            role="Launch Day Coordinator",
            goal="Manage and monitor all activities on launch day to ensure a smooth execution, quickly resolving any issues that arise.",
            backstory="You are the calm center of the storm on launch day. You excel at real-time monitoring, communication, and problem-solving under pressure, ensuring the entire team is synchronized.",
            tools=[],
            allow_delegation=False,
            verbose=True
        )

        post_launch_analyst = Agent(
            role="Growth Marketing Analyst",
            goal="Analyze post-launch data to measure success against KPIs, identify key insights, and recommend strategies to sustain momentum.",
            backstory="You are a data-driven analyst obsessed with metrics. You live in analytics dashboards and can turn raw data into actionable insights for user retention and growth.",
            tools=[],
            allow_delegation=False,
            verbose=True
        )

        # 2. --- DEFINE THE SEQUENTIAL TASKS ---

        task_launch_preparation = Task(
            description="Based on the project data, including validated marketing assets, create a comprehensive launch plan. "
                        "Define a detailed timeline, a pre-launch buzz-building strategy, technical readiness checks, and a crisis management protocol.",
            expected_output="A detailed launch plan document, including a multi-phase timeline, a launch day checklist, and a crisis response plan.",
            agent=launch_strategist
        )

        task_launch_execution = Task(
            description="Coordinate the activities on launch day. Monitor systems, manage communications across platforms, "
                        "and track initial performance metrics like user sign-ups and server stability.",
            expected_output="A launch day execution summary, reporting on key events, issues encountered, and initial performance metrics.",
            agent=execution_coordinator,
            context=[task_launch_preparation] # This task depends on the plan
        )
        
        task_post_launch_analysis = Task(
            description="Analyze all data from the first week post-launch. Compare results against the KPIs defined in the launch plan. "
                        "Synthesize user feedback, engagement data, and market response into a report with actionable recommendations for sustaining momentum.",
            expected_output="A comprehensive post-launch analysis report with key insights and a prioritized roadmap for growth.",
            agent=post_launch_analyst,
            context=[task_launch_execution]
        )
        
        # 3. --- ASSEMBLE AND RETURN THE CREW ---
        
        return Crew(
            agents=[launch_strategist, execution_coordinator, post_launch_analyst],
            tasks=[task_launch_preparation, task_launch_execution, task_post_launch_analysis],
            process=Process.sequential,
            verbose=True
        )