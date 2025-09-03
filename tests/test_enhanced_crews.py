"""
Test script for enhanced crew implementations with architectural patterns.
Demonstrates the improved crew orchestration, memory management, and task sequencing.
"""

import asyncio
import tempfile
import shutil
from pathlib import Path
from src.tractionbuild.crews.validator_crew import ValidatorCrew, ValidatorCrewConfig
from src.tractionbuild.crews.execution_crew import ExecutionCrew, ExecutionCrewConfig
from src.tractionbuild.crews.builder_crew import BuilderCrew, BuilderCrewConfig
from src.tractionbuild.crews.marketing_crew import MarketingCrew, MarketingCrewConfig
from src.tractionbuild.crews.feedback_crew import FeedbackCrew, FeedbackCrewConfig


async def test_enhanced_crews():
    """Test all enhanced crew implementations with architectural patterns."""
    
    # Create a temporary directory for testing
    temp_dir = Path(tempfile.mkdtemp())
    memory_file = temp_dir / "enhanced_crews_memory.json"
    
    try:
        print("🚀 Testing Enhanced Crew Implementations...")
        
        # Test 1: Validator Crew
        print("\n📊 Test 1: Validator Crew")
        validator_config = ValidatorCrewConfig(
            enable_memory_learning=True,
            enable_sequential_validation=True,
            enable_competitor_analysis=True,
            enable_market_sizing=True
        )
        validator_crew = ValidatorCrew(validator_config)
        
        # Test idea validation
        test_idea = "AI-powered project management tool for remote teams"
        validation_result = await validator_crew.validate_idea(
            idea=test_idea,
            context={"industry": "saas", "target_audience": "remote_teams"}
        )
        
        print(f"   ✅ Validation completed")
        print(f"   📈 Market Size: {validation_result.market_size}")
        print(f"   🎯 Target Audience: {validation_result.target_audience}")
        print(f"   💡 Recommendation: {validation_result.recommendation}")
        print(f"   🎯 Confidence Score: {validation_result.confidence_score}")
        
        # Test 2: Execution Crew
        print("\n⚙️ Test 2: Execution Crew")
        execution_config = ExecutionCrewConfig(
            enable_memory_learning=True,
            enable_task_decomposition=True,
            enable_dependency_mapping=True,
            enable_resource_planning=True
        )
        execution_crew = ExecutionCrew(execution_config)
        
        # Test execution planning
        validated_idea = {
            "idea": test_idea,
            "market_size": validation_result.market_size,
            "target_audience": validation_result.target_audience,
            "recommendation": validation_result.recommendation,
            "confidence_score": validation_result.confidence_score
        }
        
        execution_plan = await execution_crew.create_execution_plan(
            validated_idea=validated_idea,
            context={"budget": "$100K", "timeline": "6 months"}
        )
        
        print(f"   ✅ Execution plan created")
        print(f"   📋 Tasks: {len(execution_plan.get('tasks', []))}")
        print(f"   🔗 Dependencies: {len(execution_plan.get('dependencies', []))}")
        print(f"   ⏱️ Timeline: {execution_plan.get('timeline', 'TBD')}")
        print(f"   💰 Estimated Effort: {execution_plan.get('estimated_effort', 'TBD')}")
        
        # Test 3: Builder Crew
        print("\n🔨 Test 3: Builder Crew")
        builder_config = BuilderCrewConfig(
            enable_memory_learning=True,
            enable_code_generation=True,
            enable_testing=True,
            enable_documentation=True
        )
        builder_crew = BuilderCrew(builder_config)
        
        # Test code generation
        development_result = await builder_crew.generate_code(
            execution_plan=execution_plan,
            context={"tech_stack": "python", "framework": "fastapi"}
        )
        
        print(f"   ✅ Code generation completed")
        print(f"   📁 Code Files: {len(development_result.get('code_files', []))}")
        print(f"   🏗️ Architecture: {development_result.get('architecture', {}).get('type', 'TBD')}")
        print(f"   🧪 Tests: {len(development_result.get('tests', []))}")
        print(f"   📚 Documentation: {len(development_result.get('documentation', {}))}")
        
        # Test 4: Marketing Crew
        print("\n📢 Test 4: Marketing Crew")
        marketing_config = MarketingCrewConfig(
            enable_memory_learning=True,
            enable_positioning=True,
            enable_asset_generation=True,
            enable_launch_strategy=True
        )
        marketing_crew = MarketingCrew(marketing_config)
        
        # Test positioning
        product_spec = {
            "name": "ProjectFlow AI",
            "features": ["AI-powered task management", "Real-time collaboration", "Smart automation"],
            "target_audience": validation_result.target_audience,
            "market_size": validation_result.market_size
        }
        
        positioning_result = await marketing_crew.create_positioning(
            product_spec=product_spec,
            market_data={"competitors": ["Asana", "Monday.com"], "trends": ["AI integration", "Remote work"]}
        )
        
        print(f"   ✅ Positioning strategy created")
        print(f"   🎯 Target Audience: {positioning_result.get('target_audience', {}).get('primary', 'TBD')}")
        print(f"   💎 Value Proposition: {positioning_result.get('value_proposition', 'TBD')}")
        print(f"   📝 Messaging Framework: {len(positioning_result.get('messaging_framework', {}))} elements")
        
        # Test marketing assets
        assets_result = await marketing_crew.generate_marketing_assets(
            positioning=positioning_result,
            asset_requirements={"website": True, "social_media": True, "email": True}
        )
        
        print(f"   ✅ Marketing assets generated")
        print(f"   🌐 Website Copy: {len(assets_result.get('website_copy', {}))} sections")
        print(f"   📱 Social Media: {len(assets_result.get('social_media_content', []))} posts")
        print(f"   📧 Email Sequences: {len(assets_result.get('email_sequences', []))} sequences")
        
        # Test 5: Feedback Crew
        print("\n🔍 Test 5: Feedback Crew")
        feedback_config = FeedbackCrewConfig(
            enable_memory_learning=True,
            enable_quality_assurance=True,
            enable_output_validation=True,
            enable_continuous_improvement=True
        )
        feedback_crew = FeedbackCrew(feedback_config)
        
        # Test output validation
        project_output = {
            "code_quality": 0.85,
            "test_coverage": 0.92,
            "documentation": 0.78,
            "performance": 0.88,
            "security": 0.95
        }
        
        validation_result = await feedback_crew.validate_output(
            output=project_output,
            requirements={"min_quality": 0.8, "min_coverage": 0.9, "min_security": 0.9}
        )
        
        print(f"   ✅ Output validation completed")
        print(f"   ✅ Validation Status: {validation_result.get('validation_status', 'pending')}")
        print(f"   📊 Quality Score: {validation_result.get('quality_score', 0.0)}")
        print(f"   ⚠️ Issues Found: {len(validation_result.get('issues_found', []))}")
        print(f"   💡 Recommendations: {len(validation_result.get('improvement_recommendations', []))}")
        
        # Test feedback collection
        project_data = {
            "validation_result": validation_result,
            "development_result": development_result,
            "positioning_result": positioning_result,
            "execution_plan": execution_plan
        }
        
        feedback_result = await feedback_crew.collect_feedback(
            project_data=project_data,
            feedback_sources=["users", "stakeholders", "team", "reviewers"]
        )
        
        print(f"   ✅ Feedback collection completed")
        print(f"   👥 User Feedback: {len(feedback_result.get('user_feedback', {}))} items")
        print(f"   🎯 Stakeholder Feedback: {len(feedback_result.get('stakeholder_feedback', {}))} items")
        print(f"   👨‍💼 Team Feedback: {len(feedback_result.get('team_feedback', {}))} items")
        print(f"   📋 Priority Recommendations: {len(feedback_result.get('priority_recommendations', []))}")
        
        # Test quality report
        quality_report = await feedback_crew.generate_quality_report(
            project_results=project_data,
            quality_metrics={"target_quality": 0.9, "target_coverage": 0.95}
        )
        
        print(f"   ✅ Quality report generated")
        print(f"   📊 Quality Summary: {len(quality_report.get('quality_summary', {}))} metrics")
        print(f"   📈 Success Metrics: {len(quality_report.get('success_metrics', {}))} items")
        print(f"   🔄 Next Steps: {len(quality_report.get('next_steps', []))} actions")
        
        # Test 6: Memory Learning Verification
        print("\n🧠 Test 6: Memory Learning Verification")
        
        # Check memory stats for each crew
        crews = [
            ("Validator", validator_crew),
            ("Execution", execution_crew),
            ("Builder", builder_crew),
            ("Marketing", marketing_crew),
            ("Feedback", feedback_crew)
        ]
        
        for crew_name, crew_instance in crews:
            memory_stats = crew_instance.memory_manager.get_memory_stats()
            print(f"   📊 {crew_name} Crew Memory:")
            print(f"      Total Entries: {memory_stats['total_entries']}")
            print(f"      Memory Types: {len(memory_stats['type_counts'])}")
            
            # Get relevant patterns
            patterns = crew_instance.memory_manager.get_relevant_patterns(
                agent_id=f"{crew_name.lower()}_crew",
                context={"test_run": True},
                pattern_type="both"
            )
            
            for pattern_type, entries in patterns.items():
                print(f"      {pattern_type.title()} Patterns: {len(entries)}")
        
        # Test 7: Crew Integration Test
        print("\n🔄 Test 7: Crew Integration Test")
        
        # Simulate a complete project pipeline
        print("   🚀 Starting complete project pipeline...")
        
        # Step 1: Validation
        print("   📊 Step 1: Idea Validation")
        validation = await validator_crew.validate_idea(test_idea)
        
        # Step 2: Execution Planning
        print("   ⚙️ Step 2: Execution Planning")
        execution = await execution_crew.create_execution_plan({"idea": test_idea, "validation": validation.dict()})
        
        # Step 3: Code Generation
        print("   🔨 Step 3: Code Generation")
        development = await builder_crew.generate_code(execution)
        
        # Step 4: Marketing Strategy
        print("   📢 Step 4: Marketing Strategy")
        marketing = await marketing_crew.create_positioning({"product": "AI Project Manager", "features": development.get("code_files", [])})
        
        # Step 5: Quality Assurance
        print("   🔍 Step 5: Quality Assurance")
        quality = await feedback_crew.validate_output({"development": development, "marketing": marketing})
        
        print("   ✅ Complete pipeline executed successfully!")
        
        # Final Summary
        print("\n📈 Final Summary:")
        print(f"   🎯 Validated Idea: {test_idea}")
        print(f"   📊 Market Size: {validation.market_size}")
        print(f"   🔨 Generated Code Files: {len(development.get('code_files', []))}")
        print(f"   📢 Marketing Strategy: {marketing.get('value_proposition', 'TBD')}")
        print(f"   ✅ Quality Score: {quality.get('quality_score', 0.0)}")
        
        print("\n🎉 Enhanced crew tests completed successfully!")
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(test_enhanced_crews()) 
