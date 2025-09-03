"""
Configuration generator for tractionbuild.
Ensures default config files exist to prevent warnings and make the system more reliable.
"""

import os
import yaml
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def generate_default_configs():
    """Ensures default config files exist to prevent warnings."""
    config_dir = Path('config/')
    config_dir.mkdir(exist_ok=True)
    
    # Generate default agents.yaml if it doesn't exist
    agents_config_path = config_dir / 'agents.yaml'
    if not agents_config_path.exists():
        default_agents = {
            'agents': {
                'validator_agent': {
                    'role': 'Market Research and Validation Specialist',
                    'goal': 'Conduct comprehensive market research and validate business ideas',
                    'backstory': 'Expert market researcher with 15+ years of experience in startup validation',
                    'verbose': True,
                    'allow_delegation': False
                },
                'feedback_agent': {
                    'role': 'Quality Assurance and Feedback Specialist',
                    'goal': 'Ensure quality outputs and collect actionable feedback',
                    'backstory': 'Expert quality assurance specialist with experience in product testing and feedback analysis',
                    'verbose': True,
                    'allow_delegation': False
                },
                'marketing_agent': {
                    'role': 'Marketing Strategy Specialist',
                    'goal': 'Develop comprehensive marketing strategies and campaigns',
                    'backstory': 'Experienced marketing strategist with expertise in digital marketing and brand development',
                    'verbose': True,
                    'allow_delegation': False
                },
                'builder_agent': {
                    'role': 'Technical Implementation Specialist',
                    'goal': 'Build and implement technical solutions',
                    'backstory': 'Senior software engineer with expertise in full-stack development and system architecture',
                    'verbose': True,
                    'allow_delegation': False
                },
                'launch_agent': {
                    'role': 'Product Launch Specialist',
                    'goal': 'Orchestrate successful product launches and go-to-market strategies',
                    'backstory': 'Product launch expert with experience in scaling products from concept to market',
                    'verbose': True,
                    'allow_delegation': False
                }
            }
        }
        
        with open(agents_config_path, 'w') as f:
            yaml.dump(default_agents, f, default_flow_style=False)
        logger.info("Generated default agents.yaml configuration")
    
    # Generate default tasks.yaml if it doesn't exist
    tasks_config_path = config_dir / 'tasks.yaml'
    if not tasks_config_path.exists():
        default_tasks = {
            'tasks': {
                'market_research': {
                    'description': 'Conduct comprehensive market research and analysis',
                    'expected_output': 'Detailed market analysis report with insights and recommendations',
                    'agent': 'validator_agent'
                },
                'idea_validation': {
                    'description': 'Validate business idea feasibility and market fit',
                    'expected_output': 'Validation report with go/no-go recommendation',
                    'agent': 'validator_agent'
                },
                'quality_assessment': {
                    'description': 'Assess quality of deliverables and outputs',
                    'expected_output': 'Quality assessment report with improvement recommendations',
                    'agent': 'feedback_agent'
                },
                'feedback_collection': {
                    'description': 'Collect and analyze stakeholder feedback',
                    'expected_output': 'Comprehensive feedback analysis with actionable insights',
                    'agent': 'feedback_agent'
                },
                'marketing_strategy': {
                    'description': 'Develop comprehensive marketing strategy and campaign plan',
                    'expected_output': 'Detailed marketing strategy with implementation roadmap',
                    'agent': 'marketing_agent'
                },
                'technical_implementation': {
                    'description': 'Implement technical solutions and build deliverables',
                    'expected_output': 'Technical implementation with code and documentation',
                    'agent': 'builder_agent'
                },
                'product_launch': {
                    'description': 'Orchestrate successful product launch and go-to-market execution',
                    'expected_output': 'Launch plan with execution timeline and success metrics',
                    'agent': 'launch_agent'
                }
            }
        }
        
        with open(tasks_config_path, 'w') as f:
            yaml.dump(default_tasks, f, default_flow_style=False)
        logger.info("Generated default tasks.yaml configuration")
    
    # Generate default workflows.yaml if it doesn't exist
    workflows_config_path = config_dir / 'workflows.yaml'
    if not workflows_config_path.exists():
        default_workflows = {
            'validation_and_launch': {
                'metadata': {
                    'description': 'Complete validation and launch workflow',
                    'compliance': ['GDPR', 'CCPA'],
                    'audit': True,
                    'visualize': True
                },
                'sequence': [
                    {'state': 'IDEA_VALIDATION', 'crew': 'ValidatorCrew'},
                    {'state': 'FEEDBACK_COLLECTION', 'crew': 'FeedbackCrew'},
                    {'state': 'COMPLETED'}
                ]
            },
            'default_software_build': {
                'metadata': {
                    'description': 'Default software development workflow',
                    'compliance': ['SOC2'],
                    'audit': False,
                    'visualize': False
                },
                'sequence': [
                    {'state': 'IDEA_VALIDATION', 'crew': 'ValidatorCrew'},
                    {'state': 'TASK_EXECUTION', 'crew': 'BuilderCrew'},
                    {'state': 'FEEDBACK_COLLECTION', 'crew': 'FeedbackCrew'},
                    {'state': 'COMPLETED'}
                ]
            }
        }
        
        with open(workflows_config_path, 'w') as f:
            yaml.dump(default_workflows, f, default_flow_style=False)
        logger.info("Generated default workflows.yaml configuration")
    
    logger.info("✅ All default configuration files generated successfully")


def ensure_output_directories():
    """Ensure all necessary output directories exist."""
    directories = [
        'output',
        'output/workflows',
        'output/test_results',
        'output/diagrams',
        'output/logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    logger.info("✅ All output directories created successfully")


def initialize_system():
    """Initialize the tractionbuild system with all necessary configurations."""
    logger.info("🚀 Initializing tractionbuild system...")
    
    # Generate default configs
    generate_default_configs()
    
    # Ensure output directories exist
    ensure_output_directories()
    
    logger.info("✅ tractionbuild system initialization complete") 