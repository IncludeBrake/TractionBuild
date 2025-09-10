#!/usr/bin/env python3
"""
Demonstration of TractionBuild's standardized crew outputs and artifact storage.
This script shows the complete flow from crew execution to persistent storage.
"""

import tempfile
import os
from pathlib import Path

from src.core.types import CrewResult, Artifact, create_success_result, create_error_result
from src.services.artifact_store import ArtifactStore
from src.services.project_registry import ProjectRegistry

def demo_standardized_outputs():
    """Demonstrate the complete standardized output workflow."""
    print("🚀 TractionBuild Standardized Outputs Demo")
    print("=" * 50)

    # Create temporary directory for demo
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Using temporary directory: {temp_dir}")

        # Initialize services
        store = ArtifactStore(temp_dir)
        registry = ProjectRegistry(temp_dir)

        project_id = "demo-project-123"

        # 1. Create project
        print("\n📋 Step 1: Creating project")
        registry.create_project(project_id, "Build a task management SaaS platform")
        print("✅ Project created successfully")

        # 2. Simulate ValidatorCrew result
        print("\n🔍 Step 2: ValidatorCrew execution")
        validator_artifacts = [
            Artifact(
                type="json",
                data={
                    "market_size": "Medium ($75M TAM)",
                    "competition": "Moderate (5-8 competitors)",
                    "target_audience": "Tech-savvy professionals & small teams",
                    "risk_level": "Low-Medium",
                    "recommendation": "Proceed with MVP development"
                },
                meta={"confidence": 0.87, "source": "market_research"}
            ),
            Artifact(
                type="markdown",
                data="""# Market Validation Report

## Executive Summary
The task management SaaS idea shows strong potential with a clear market need and manageable competition.

## Key Findings
- **Market Opportunity**: $75M TAM with 15% projected growth
- **Target Users**: Small to medium teams (5-50 employees)
- **Competitive Advantage**: AI-powered task prioritization
- **Go-to-Market**: B2B SaaS with freemium model

## Risk Assessment
- Technical: Low (standard web technologies)
- Market: Medium (established competitors exist)
- Financial: Low (reasonable development budget)

## Recommendation
**APPROVED** for MVP development with 6-month timeline.
""",
                meta={"report_type": "validation_summary", "author": "ValidatorCrew"}
            )
        ]

        validator_result = create_success_result(
            crew_name="ValidatorCrew",
            summary="Market validation completed - strong potential identified",
            artifacts=validator_artifacts,
            tokens_in=120,
            tokens_out=240,
            cost_usd=0.012,
            duration_ms=2500
        )

        print("✅ ValidatorCrew result created")
        print(f"   📊 Stats: {validator_result.stats}")
        print(f"   🎯 Artifacts: {len(validator_result.artifacts)}")

        # 3. Store validator results
        print("\n💾 Step 3: Storing artifacts and updating registry")
        registry.append_crew_result(project_id, validator_result)
        print("✅ Results stored in registry")

        # 4. Simulate BuilderCrew result
        print("\n🔨 Step 4: BuilderCrew execution")
        builder_artifacts = [
            Artifact(
                type="json",
                data={
                    "architecture": "FastAPI + React + PostgreSQL",
                    "components": [
                        "User authentication service",
                        "Task management API",
                        "Real-time collaboration",
                        "AI-powered insights",
                        "Admin dashboard"
                    ],
                    "technologies": [
                        "Python 3.11", "FastAPI", "SQLAlchemy",
                        "React", "TypeScript", "PostgreSQL",
                        "Redis", "Docker", "Kubernetes"
                    ],
                    "deployment_strategy": "AWS EKS with CI/CD"
                },
                meta={"build_type": "mvp", "estimated_effort": "3 months"}
            )
        ]

        builder_result = create_success_result(
            crew_name="BuilderCrew",
            summary="MVP architecture designed and components specified",
            artifacts=builder_artifacts,
            tokens_in=180,
            tokens_out=350,
            cost_usd=0.018,
            duration_ms=3200
        )

        print("✅ BuilderCrew result created")
        print(f"   📊 Stats: {builder_result.stats}")
        print(f"   🎯 Artifacts: {len(builder_result.artifacts)}")

        # 5. Store builder results
        registry.append_crew_result(project_id, builder_result)
        print("✅ Builder results stored")

        # 6. Verify stored data
        print("\n🔍 Step 5: Verifying stored data")

        # Check registry
        project_data = registry.get_project_data(project_id)
        print(f"📋 Project registry: {len(project_data['crews'])} crew results")

        for crew_entry in project_data['crews']:
            crew_name = crew_entry['crew_name']
            print(f"   👷 {crew_name}: {crew_entry['summary']}")
            print(f"      📊 Stats: {crew_entry['stats']}")
            print(f"      🎯 Artifacts: {len(crew_entry['artifact_paths'])}")

        # Check artifacts
        validator_artifacts_loaded = store.load_artifacts(project_id, "ValidatorCrew")
        builder_artifacts_loaded = store.load_artifacts(project_id, "BuilderCrew")

        print(f"💾 Validator artifacts: {len(validator_artifacts_loaded)} loaded")
        print(f"💾 Builder artifacts: {len(builder_artifacts_loaded)} loaded")

        # 7. Show file structure
        print("\n📂 Step 6: File structure created")
        runs_dir = Path(temp_dir) / project_id
        if runs_dir.exists():
            for root, dirs, files in os.walk(runs_dir):
                level = root.replace(str(runs_dir), '').count(os.sep)
                indent = ' ' * 4 * level
                print(f"{indent}📁 {os.path.basename(root)}/")
                subindent = ' ' * 4 * (level + 1)
                for file in files:
                    print(f"{subindent}📄 {file}")

        # 8. Demonstrate error handling
        print("\n⚠️  Step 7: Error handling demonstration")
        error_result = create_error_result(
            crew_name="TestCrew",
            error_msg="Simulated network timeout",
            warnings=["Connection unstable", "Retry recommended"]
        )

        registry.append_crew_result(project_id, error_result)
        print("✅ Error result handled gracefully")

        # Final verification
        final_data = registry.get_project_data(project_id)
        print("\n🎉 Demo completed successfully!")
        print(f"📊 Total crew executions: {len(final_data['crews'])}")
        print(f"💾 Total artifacts stored: {sum(len(c['artifact_paths']) for c in final_data['crews'])}")
        print(f"📈 Project status: {final_data['states'][-1]}")

if __name__ == "__main__":
    demo_standardized_outputs()
