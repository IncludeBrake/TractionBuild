#!/usr/bin/env python3
"""
Test script to verify Prometheus metrics are being collected correctly.
Runs a workflow and displays the metrics that would be exported.
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from prometheus_client import Counter, Gauge, Histogram, generate_latest
from src.zerotoship.core.workflow_engine import WorkflowEngine

# Initialize metrics
WORKFLOW_TOTAL = Counter('workflow_total', 'Total number of workflows run')
WORKFLOW_STATE = Gauge('workflow_state', 'Current workflow state', ['state'])
WORKFLOW_DURATION_SECONDS = Histogram('workflow_duration_seconds', 'Workflow execution duration in seconds')

async def main():
    print("Testing Prometheus Metrics Integration\n")
    print("=" * 60)

    # Create test project data
    project_data = {
        "id": "test_metrics_001",
        "idea": "Metrics Test",
        "workflow": "just_the_build",
        "state": "TASK_EXECUTION",
    }

    # Create metrics dictionary
    metrics_dict = {
        "workflow_total": WORKFLOW_TOTAL,
        "workflow_state": WORKFLOW_STATE,
        "workflow_duration_seconds": WORKFLOW_DURATION_SECONDS,
    }

    # Run workflow
    print("Running workflow with metrics tracking...\n")
    engine = WorkflowEngine(project_data, metrics=metrics_dict)
    result = await engine.run()

    print(f"\nWorkflow completed with state: {result['state']}")
    print(f"Message: {result['message']}\n")

    # Display metrics
    print("=" * 60)
    print("PROMETHEUS METRICS OUTPUT")
    print("=" * 60)

    metrics_output = generate_latest().decode('utf-8')

    # Filter and display relevant metrics
    for line in metrics_output.split('\n'):
        if any(keyword in line for keyword in ['workflow_total', 'workflow_state', 'workflow_duration_seconds']):
            print(line)

    print("\n" + "=" * 60)
    print("Metrics test completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
