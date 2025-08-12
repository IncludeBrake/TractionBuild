import os
import yaml
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def _create_yaml_if_not_exists(path: Path, data: dict, description: str):
    """Helper function to create a YAML file if it doesn't exist."""
    if not path.exists():
        try:
            with open(path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Generated default {description} at: {path}")
        except Exception as e:
            logger.error(f"Failed to generate {description}: {e}")

def generate_default_configs():
    """Ensures default configuration files for agents, tasks, and workflows exist."""
    config_dir = Path('config/')
    config_dir.mkdir(exist_ok=True)

    # --- 1. Default agents.yaml (Template for users) ---
    default_agents = {
        'validator_agent': {
            'role': 'Market Research and Validation Specialist',
            'goal': 'Conduct comprehensive market research and validate business ideas',
            'backstory': 'An expert market researcher with 15+ years of experience...'
        },
        # Add other generic agent examples if desired
    }
    _create_yaml_if_not_exists(config_dir / 'agents.yaml', {'agents': default_agents}, "agents.yaml")

    # --- 2. Default tasks.yaml (Template for users) ---
    default_tasks = {
        'market_research': {
            'description': 'Conduct comprehensive market research and analysis for an idea.',
            'expected_output': 'A detailed market analysis report with insights and recommendations.',
            'agent': 'validator_agent'
        },
        # Add other generic task examples if desired
    }
    _create_yaml_if_not_exists(config_dir / 'tasks.yaml', {'tasks': default_tasks}, "tasks.yaml")

    # --- 3. Default workflows.yaml (Crucial for the engine) ---
    default_workflows = {
        'validation_and_launch': {
            'metadata': {
                'description': 'A complete validation and marketing launch workflow for non-software products.',
                'compliance': ['GDPR', 'CCPA'],
                'visualize': True
            },
            'sequence': [
                {'state': 'IDEA_VALIDATION', 'crew': 'ValidatorCrew'},
                {'state': 'MARKETING_PREPARATION', 'crew': 'MarketingCrew'},
                {'state': 'LAUNCH_PREPARATION', 'crew': 'LaunchCrew'},
                {'state': 'FEEDBACK_COLLECTION', 'crew': 'FeedbackCrew'},
                {'state': 'COMPLETED'}
            ]
        },
        'default_software_build': {
            'metadata': {
                'description': 'The standard end-to-end workflow for building a new software product.',
                'compliance': ['SOC2'],
                'visualize': True
            },
            'sequence': [
                {'state': 'IDEA_VALIDATION', 'crew': 'ValidatorCrew'},
                {
                    'state': 'EXECUTION_PLANNING', 
                    'crew': 'ExecutionCrew',
                    'conditions': {
                        'all': [
                            {'field': 'validation.passed', 'operator': '==', 'value': True},
                            {'field': 'validation.confidence', 'operator': '>=', 'value': 0.75}
                        ]
                    },
                    'on_fail': {'action': 'escalate_to', 'workflow': 'human_review'}
                },
                {'state': 'PRODUCT_BUILD', 'crew': 'BuilderCrew'},
                {'state': 'FEEDBACK_COLLECTION', 'crew': 'FeedbackCrew'},
                {'state': 'COMPLETED'}
            ]
        }
    }
    _create_yaml_if_not_exists(config_dir / 'workflows.yaml', default_workflows, "workflows.yaml")

def ensure_output_directories():
    """Ensures all necessary output directories exist."""
    directories = ['output/workflows', 'output/test_results', 'output/diagrams', 'output/logs']
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    logger.info("Verified all output directories exist.")

def initialize_system():
    """
    A single entry point to initialize the ZeroToShip system, ensuring all
    necessary configurations and directories are in place.
    """
    logger.info("🚀 Initializing ZeroToShip system...")
    generate_default_configs()
    ensure_output_directories()
    logger.info("✅ ZeroToShip system initialization complete.")