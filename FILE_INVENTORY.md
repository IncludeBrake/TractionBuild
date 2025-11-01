# TRACTIONBUILD FILE INVENTORY

Generated inventory of all project files with descriptions. This document provides a complete overview of the current codebase structure.

## File Count by Category

- Configuration: 8 files
- Deployment: 25 files
- Documentation: 21 files
- Other: 15 files
- Root Files: 35 files
- Source Code: 85 files
- Tests: 31 files

## Complete File List

### .github/
- `dependabot.yml` - GitHub dependency update automation
- `workflows/` - CI/CD pipeline configurations

### app/
- `main.py` - FastAPI application entry point
- `routers/` - API route definitions

### config/
- `agents.yaml` - AI agent configurations
- `crew_config.yaml` - CrewAI crew settings
- `production.yaml` - Production environment config
- `project_workflows.yaml` - Project workflow definitions
- `tasks.yaml` - Task configurations
- `workflows.yaml` - Workflow orchestration definitions

### core/
- `cache.py` - Caching system implementation
- `llm.py` - Language model management
- `schemas.py` - Data validation schemas

### data/
- `budget.db` - Token usage database
- `execution_state/` - Workflow execution state storage
- `summarization_dataset.json` - Training data for summarization
- `token_usage.json.backup` - Backup of token usage data

### deployment/
- `charts/` - Helm chart definitions
- `web/` - Web application deployment files

### docs/
- `ADVISORY_BOARD_GUIDE.md` - Advisory board usage guide
- `AGENT_ROSTER.md` - List of available AI agents
- `ENHANCED_CONNECTION_SUMMARY.md` - Connection enhancement summary
- `ENHANCED_WORKFLOW_SUMMARY.md` - Workflow improvements summary
- `INFINITE_LOOP_FIX_SUMMARY.md` - Loop prevention fixes
- `LLM_FACTORY_INTEGRATION_SUMMARY.md` - LLM integration details
- `LLM_FACTORY_SETUP_GUIDE.md` - LLM setup instructions
- `MAIN_PY_PRODUCTION_SUMMARY.md` - Production deployment summary
- `NEW_DEVELOPER_ONBOARDING.md` - Developer onboarding guide
- `PATCH_README.md` - Patch notes and updates
- `PRODUCTION_READY_SUMMARY.md` - Production readiness assessment
- `PROJECT_STRUCTURE.md` - Project architecture overview
- `README_E2E.md` - End-to-end testing guide
- `Salem_Pricing_Guide.markdown` - Pricing strategy guide
- `TRACTIONBUILD_COMPREHENSIVE_GUIDE.md` - Complete system guide
- `TractionBuild Technical Specifications.txt` - Technical specs
- `TractionBuild_Tech_Spec_Doc.md` - Technical documentation
- `VAULT_INTEGRATION_SUMMARY.md` - Vault security integration
- `zero_to_ship_overview.md` - Deployment overview

### infra/
- `helm/` - Infrastructure Helm charts

### k8s/
- `cleanup.sh` - Kubernetes cleanup script
- `configmap.yaml` - Kubernetes config maps
- `deploy.ps1` - PowerShell deployment script
- `deploy.sh` - Bash deployment script
- `hpa.yaml` - Horizontal pod autoscaling
- `ingress.yaml` - Ingress configuration
- `namespace.yaml` - Namespace definitions
- `neo4j-deployment.yaml` - Neo4j database deployment
- `README.md` - Kubernetes deployment guide
- `secret.yaml` - Kubernetes secrets
- `zerotoship-deployment.yaml` - Main application deployment

### output/
- `project_3f58768f/` - Project execution output
- `project_46d538d6/` - Project execution output

### repo-tools/
- `doctor.ps1` - Repository health check script
- `requirements.txt` - Repository tool dependencies
- `config/` - Repository configuration
- `HOWTORUN/` - Usage instructions
- `scripts/` - Repository management scripts

### root/
- `.claudeignore` - Claude AI ignore patterns
- `.cursorignore` - Cursor editor ignore patterns
- `.coverage` - Test coverage report (can be removed)
- `.dockerignore` - Docker ignore patterns
- `.editorconfig` - Code style configuration
- `.env` - Environment variables
- `.env.example` - Environment variables template
- `.gitattributes` - Git attributes
- `.gitignore` - Git ignore patterns
- `.hadolint.yaml` - Dockerfile linting config
- `.pre-commit-config.yaml` - Pre-commit hooks
- `.python-version` - Python version specification
- `app_v1_integrated_backup.py` - Legacy application version (obsolete - can be removed)
- `app_v1_integrated.py` - Legacy application version (obsolete - can be removed)
- `app_v1_mock.py` - Legacy application version (obsolete - can be removed)
- `app_v1_real_integration.py` - Legacy application version (obsolete - can be removed)
- `chaos_testing_suite.py` - Chaos testing utilities
- `chat_ui_enhanced.py` - Enhanced chat interface
- `chat_ui.py` - Basic chat interface
- `check_connection.py` - Connection testing script
- `Cleanup_Project_Script_Outcome.txt` - Cleanup script output (can be removed)
- `cleanup_project.py` - Project cleanup script (can be removed)
- `CODEOWNERS` - GitHub code ownership
- `commands.md` - Available commands documentation
- `CONTRIBUTING.md` - Contribution guidelines
- `create_project.ps1` - Project creation script
- `dashboard.py` - Dashboard application
- `demo_smm.py` - Social media marketing demo
- `demo_standardized_outputs.py` - Output standardization demo
- `deploy_railway.ps1` - Railway deployment script
- `DEPLOYMENT_README.md` - Deployment instructions
- `deployment.yaml` - Deployment configuration (superseded by k8s/)
- `docker-compose.yml` - Docker compose configuration
- `Dockerfile` - Docker container definition
- `dockerizeforce.py` - Docker utilities
- `entrypoint.sh` - Container entrypoint script
- `env.example` - Environment variables example
- `get_helm.sh` - Helm installation script
- `init_db.sql` - Database initialization
- `Makefile` - Build automation
- `package-lock.json` - Node.js dependency lock
- `package.json` - Node.js dependencies
- `prometheus.yml` - Prometheus configuration
- `pyproject.toml` - Python project configuration
- `pytest.ini` - Pytest configuration
- `RAILWAY_DEPLOYMENT.md` - Railway deployment guide
- `railway.json` - Railway configuration
- `README_SCRIPTS.md` - Script usage guide
- `README.md` - Main project README
- `requirements.lock` - Dependency lock file
- `requirements.txt` - Python dependencies
- `resource_manager_validation.py` - Resource management validation
- `run_tractionbuild.bat` - Windows run script
- `runtime.txt` - Runtime configuration
- `SECURITY.md` - Security policy
- `service.yaml` - Service configuration (superseded by k8s/)
- `start_tractionbuild.ps1` - PowerShell start script
- `strategic_chaos_testing.py` - Strategic testing utilities
- `test_project_final.json` - Test data (can be removed)
- `test_project.json` - Test data (can be removed)
- `test_tractionbuild.ps1` - Test script
- `tractionbuild-job.yaml` - Job configuration (superseded by k8s/)
- `uv_auto.bat` - UV automation script
- `uv_auto.ps1` - UV automation script
- `uv_auto.sh` - UV automation script
- `uv.lock` - UV dependency lock

### runs/
- `default_run.yaml` - Default run configuration
- `5aa997c2-febe-4691-a694-d14a3bd1ed9f/` - Run output directory
- `48c7052c-c48b-45e1-9384-c5ba743e3f60/` - Run output directory
- `79ee9be0-4af3-4042-a25b-795219b27615/` - Run output directory
- `108e5284-adb6-47cb-8558-db1f9bf6d8f6/` - Run output directory
- `175a3bcb-4b10-4d6a-9db2-b598fe6c9160/` - Run output directory
- `50568b55-05cc-4bde-acb2-eba0f524f11e/` - Run output directory
- `60355b16-89a8-4a38-8108-fa5c6be0c348/` - Run output directory
- `91776dbd-486e-4100-9ad7-c079a8fcbec4/` - Run output directory
- `57489656-8f98-4114-ac8d-4a00c6f76f76/` - Run output directory
- `a5e77411-a21d-40d0-b963-6802699814bc/` - Run output directory
- `b3f199b7-55ba-44fd-b0fb-0fd7781e3b66/` - Run output directory
- `cef34f0d-a39f-4d34-977f-8b9a4ea8b047/` - Run output directory
- `de5eec42-ce00-4da6-8ace-a4deb48e9c43/` - Run output directory
- `ea83994e-98b9-4ac6-84f3-b2d75d99d0e3/` - Run output directory
- `f8b421f0-ef6d-4019-81b1-0319ecf183e7/` - Run output directory
- `f280532e-523d-4838-ad37-357f3028cd07/` - Run output directory
- `ffeae300-557b-4fb8-9bf9-924fcd2fe0b1/` - Run output directory
- `test_project_123/` - Test run output

### scripts/
- `check_env.py` - Environment validation script
- `fine_tune_summarizer.py` - Model fine-tuning script
- `setup_environment.py` - Environment setup script
- `ci/` - CI/CD scripts
- `dev/` - Development scripts

### src/
- `__init__.py` - Package initialization
- `core/` - Core system components
- `observability/` - Monitoring and observability
- `security/` - Security components
- `services/` - Service layer
- `smm/` - Social media marketing
- `tractionbuild/` - Main application package
- `tractionbuild.egg-info/` - Package metadata

### src/tractionbuild/
- `__init__.py` - Package initialization
- `main.py` - CLI entry point
- `adapters/` - Integration adapters
- `agents/` - AI agent implementations
- `api/` - API components
- `cli/` - Command line interface
- `core/` - Core system components
- `crews/` - AI agent crews
- `database/` - Database integrations
- `graphs/` - Graph processing
- `learning/` - Machine learning components
- `models/` - Data models
- `monitoring/` - Monitoring components
- `observability/` - Observability tools
- `schemas/` - Data schemas
- `security/` - Security components
- `services/` - Service implementations
- `tasks/` - Task definitions
- `tools/` - Utility tools
- `utils/` - Utility functions
- `vendors/` - Third-party integrations

### streamlit/
- `pages/` - Streamlit application pages

### tests/
- `conftest.py` - Test configuration
- `test_advisory_board.py` - Advisory board tests
- `test_dedupe.md` - Deduplication test documentation
- `test_docker.ps1` - Docker testing script
- `test_docker.sh` - Docker testing script
- `test_e2e_min.py` - Minimal end-to-end tests
- `test_e2e.py` - Full end-to-end tests
- `test_enhanced_connection.py` - Connection enhancement tests
- `test_enhanced_crews.py` - Enhanced crew tests
- `test_enhanced_crew_controller.py` - Crew controller tests
- `test_enhanced_workflows.py` - Workflow enhancement tests
- `test_enterprise_system.py` - Enterprise system tests
- `test_final_loop_fix.py` - Loop fix validation tests
- `test_final_production_certification.py` - Production certification tests
- `test_integrated_core.py` - Core integration tests
- `test_integration_flow.py` - Integration flow tests
- `test_llm_factory_integration.py` - LLM factory tests
- `test_llm_factory_simple.py` - Simple LLM factory tests
- `test_marketing_campaign_fix.py` - Marketing campaign tests
- `test_meta_memory.py` - Meta memory tests
- `test_neo4j_connection.py` - Neo4j connection tests
- `test_observability.py` - Observability tests
- `test_output_validator.py` - Output validation tests
- `test_production_fixes.py` - Production fix tests
- `test_production_ready.py` - Production readiness tests
- `test_project_registry.py` - Project registry tests
- `test_simple_crew.py` - Simple crew tests
- `test_simple_loop_fix.py` - Simple loop fix tests
- `test_smm_integration.py` - SMM integration tests
- `tests/agents/` - Agent-specific tests
- `tests/core/` - Core component tests
- `tests/crews/` - Crew-specific tests
- `tests/observability/` - Observability tests
- `tests/services/` - Service tests

## Notes

- Files marked as "(obsolete - can be removed)" are legacy files that should be deleted during cleanup
- Test artifacts in root directory should be cleaned up
- Multiple entry points (app_v1_*.py, main.py, app/main.py) suggest architectural consolidation needed
- Extensive documentation indicates mature project with good knowledge transfer
- Deployment files show both Docker and Kubernetes support
- Large number of test files indicates good testing practices but may need consolidation
