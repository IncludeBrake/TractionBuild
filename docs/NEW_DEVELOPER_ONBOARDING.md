# 🚀 TractionBuild Developer Onboarding Guide

**Welcome to TractionBuild!** This guide will get you up and running as a productive contributor to our AI-powered product development platform.

---

## 📖 Table of Contents

1. [What is TractionBuild?](#what-is-tractionbuild)
2. [Quick Start (30 minutes)](#quick-start-30-minutes)
3. [Architecture Overview](#architecture-overview)
4. [Current Project State](#current-project-state)
5. [Development Environment Setup](#development-environment-setup)
6. [Development Workflow](#development-workflow)
7. [Contributing Guidelines](#contributing-guidelines)
8. [What Needs to Be Done](#what-needs-to-be-done)
9. [Troubleshooting](#troubleshooting)
10. [Resources & Next Steps](#resources--next-steps)

---

## 🤔 What is TractionBuild?

**TractionBuild is an AI-powered product studio that transforms ideas into market-ready products.**

### Our Mission
Turn any product idea into:
- ✅ Validated market opportunity
- ✅ Complete MVP codebase
- ✅ Launch-ready marketing materials
- ✅ Production deployment configuration

### How It Works
1. **Input**: A product idea (e.g., "Build a task management app")
2. **Validation**: AI agents research market fit and technical feasibility
3. **Build**: Specialized crews generate code, tests, and documentation
4. **Launch**: Marketing assets and deployment configs are created
5. **Learn**: System improves through feedback loops

### Key Technologies
- **CrewAI**: Multi-agent orchestration framework
- **Python 3.12**: Main development language
- **Neo4j**: Graph database for knowledge storage
- **FastAPI**: Web API framework
- **Docker/Kubernetes**: Container orchestration
- **Prometheus**: Monitoring and metrics

---

## ⚡ Quick Start (30 minutes)

### Prerequisites
- Python 3.12+
- Git
- Docker (optional, for full stack)
- Neo4j AuraDB account (free tier available)

### Step 1: Clone & Setup
```bash
# Clone the repository
git clone https://github.com/IncludeBrake/TractionBuild.git
cd TractionBuild

# Set up Python environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# Required: OPENAI_API_KEY
# Optional: ANTHROPIC_API_KEY, NEO4J_URI
```

### Step 3: Run Your First Project
```bash
# Run a simple project
python -m src.tractionbuild.main --idea "Build a habit tracker app" --workflow validation_and_launch
```

### Step 4: Check the Results
```bash
# Results are saved in output/project_[id]/
ls output/
# Look for result.json and execution_history.json
```

**🎉 Congratulations!** You've just generated a complete product concept with market analysis, technical architecture, and launch strategy.

---

## 🏗️ Architecture Overview

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Orchestrator  │───▶│  Workflow Engine│───▶│     Crews       │
│   (main.py)     │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Project Registry│    │   Configuration │    │   AI Agents     │
│   (Neo4j)       │    │   (YAML)        │    │   (CrewAI)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Agent Crews

1. **ValidatorCrew**: Market research, competitor analysis, feasibility assessment
2. **BuilderCrew**: Code generation, architecture design, testing
3. **MarketingCrew**: Positioning, content creation, launch planning
4. **LaunchCrew**: Deployment preparation, monitoring setup
5. **FeedbackCrew**: Performance analysis, improvement recommendations

### Data Flow

```
User Idea → Validation → Planning → Code Generation → Marketing → Launch → Feedback
     ↓         ↓         ↓         ↓            ↓         ↓         ↓
  Input    Market    Task     Complete      Assets    Deploy    Learning
           Data     Graph    Codebase     Created   Ready     Stored
```

### Key Files to Know

| File | Purpose | Importance |
|------|---------|------------|
| `src/tractionbuild/main.py` | Main orchestrator | ⭐⭐⭐ |
| `config/workflows.yaml` | Workflow definitions | ⭐⭐⭐ |
| `config/agents.yaml` | Agent configurations | ⭐⭐⭐ |
| `src/tractionbuild/core/workflow_engine.py` | Workflow execution | ⭐⭐⭐ |
| `src/tractionbuild/database/project_registry.py` | Data persistence | ⭐⭐ |

---

## 📊 Current Project State

### ✅ What's Working

- **Core Architecture**: Solid CrewAI integration with async execution
- **Workflow Engine**: YAML-configurable workflows with state management
- **Database Integration**: Neo4j connectivity for project storage
- **Monitoring**: Prometheus metrics and health checks
- **Testing**: 40+ test files with good coverage
- **Deployment**: Docker/Kubernetes configurations
- **Documentation**: Comprehensive technical guides

### ⚠️ Known Limitations

- **Code Generation**: Basic implementation, needs enhancement
- **Rollback System**: Not implemented (critical for production)
- **Error Recovery**: Limited graceful failure handling
- **Performance**: Not optimized for large-scale projects
- **Security**: Some production hardening needed

### 📈 Recent Progress

- ✅ Production orchestrator with monitoring
- ✅ Multi-workflow support
- ✅ Graph database integration
- ✅ Container deployment
- ✅ Health check endpoints

---

## 🛠️ Development Environment Setup

### Required Tools

```bash
# Python development
pip install -r requirements-dev.txt

# Code quality
pip install ruff black isort mypy pre-commit

# Testing
pip install pytest pytest-cov

# Documentation
pip install mkdocs mkdocs-material
```

### IDE Configuration

**VS Code Recommended Extensions:**
- Python
- Pylance
- Ruff
- Black Formatter
- isort
- GitLens
- Docker

**VS Code Settings:**
```json
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.ruffEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

### Database Setup

```bash
# Start Neo4j locally (optional)
docker run -d \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/test_password \
  neo4j:latest

# Or use Neo4j AuraDB (recommended)
# Sign up at neo4j.com/aura
```

---

## 🔄 Development Workflow

### Daily Development Cycle

1. **Morning**: Check issues, update from main
2. **Planning**: Pick task, create feature branch
3. **Development**: Write code, add tests
4. **Testing**: Run tests, check integration
5. **Review**: Self-review, push branch
6. **PR**: Create pull request, address feedback

### Branch Strategy

```
main (production-ready)
├── feature/feature-name
├── fix/issue-number
└── chore/maintenance-task
```

### Commit Convention

```
feat: add new workflow validation
fix: resolve neo4j connection timeout
docs: update api documentation
chore: update dependencies
```

### Testing Strategy

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test category
pytest -m unit
pytest -m integration

# Run tests for specific module
pytest tests/test_workflow_engine.py
```

### Code Quality Checks

```bash
# Format code
black src/
isort src/

# Lint code
ruff check src/

# Type check
mypy src/

# Security check
bandit -r src/
```

---

## 🤝 Contributing Guidelines

### Code Standards

- **Python**: PEP 8 compliant, type hints required
- **Documentation**: Docstrings for all public functions
- **Testing**: Minimum 80% coverage, integration tests for new features
- **Security**: No hardcoded secrets, input validation

### Pull Request Process

1. **Create Branch**: `git checkout -b feature/your-feature-name`
2. **Write Code**: Follow existing patterns and conventions
3. **Add Tests**: Ensure new functionality is tested
4. **Update Docs**: Modify documentation as needed
5. **Self Review**: Check your own code before requesting review
6. **Create PR**: Use descriptive title and detailed description
7. **Address Feedback**: Respond to reviewer comments promptly

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tests pass
- [ ] Security review completed
```

### Communication

- **Issues**: Use GitHub issues for bugs and features
- **Discussions**: Use GitHub discussions for questions
- **Slack**: Team coordination and daily standups
- **Docs**: Keep documentation current

---

## 🎯 What Needs to Be Done

### High Priority (Next Sprint)

1. **Implement Code Generation** (`src/tractionbuild/tools/code_tools.py`)
   - Complete the TODO: "Implement actual code generation"
   - Add support for multiple languages/frameworks
   - Integrate with existing validation

2. **Add Rollback Logic** (`src/tractionbuild/database/project_registry.py`)
   - Implement project state rollback functionality
   - Add transaction safety for database operations
   - Create recovery mechanisms for failed workflows

3. **OpenAI Feature Extraction** (`src/tractionbuild/vendors/salem/nodes.py`)
   - Complete the TODO: "Implement OpenAI call to extract features"
   - Add proper error handling and fallbacks

### Medium Priority

4. **Production Security Hardening**
   - Fix CORS configuration (restrict origins)
   - Implement proper authentication
   - Add rate limiting and input validation

5. **Database Migration**
   - Move from in-memory storage to persistent database
   - Implement data backup and recovery
   - Add database connection pooling

6. **Performance Optimization**
   - Optimize LLM API calls (caching, batching)
   - Improve workflow execution speed
   - Add async processing for long-running tasks

### Future Enhancements

7. **Advanced Features**
   - Multi-language code generation
   - Real-time collaboration
   - Advanced analytics dashboard
   - Mobile app development support

---

## 🔧 Troubleshooting

### Common Issues

**"Module not found" errors**
```bash
# Ensure you're in the virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Reinstall dependencies
pip install -r requirements.txt
```

**Neo4j connection failures**
```bash
# Check if Neo4j is running
docker ps | grep neo4j

# Test connection
python test_neo4j_connection.py

# Update .env with correct URI
NEO4J_URI=neo4j://localhost:7687
```

**Workflow execution hangs**
- Check Prometheus metrics at `http://localhost:8000/metrics`
- Look for error logs in `output/project_[id]/execution_history.json`
- Try with a simpler workflow first

**API key issues**
```bash
# Verify keys are set
echo $OPENAI_API_KEY

# Test API connectivity
python -c "import openai; openai.api_key = '$OPENAI_API_KEY'; print('API key valid')"
```

### Debug Commands

```bash
# Check system health
curl http://localhost:8000/health

# View workflow status
python -m src.tractionbuild.cli --list-workflows

# Run diagnostics
python scripts/diagnostics.py

# View logs
tail -f logs/tractionbuild.log
```

### Getting Help

1. **Check existing issues** on GitHub
2. **Search documentation** in `docs/` folder
3. **Ask in Slack** #dev-support channel
4. **Create an issue** if you find a bug

---

## 📚 Resources & Next Steps

### Essential Reading

1. **[Comprehensive Technical Guide](TRACTIONBUILD_COMPREHENSIVE_GUIDE.md)** - Deep dive into architecture
2. **[Zero to Ship Overview](zero_to_ship_overview.md)** - System integration guide
3. **[API Documentation](api/README.md)** - Web API reference
4. **[Deployment Guide](DEPLOYMENT_README.md)** - Production deployment

### Key Files to Study

```bash
# Core components
src/tractionbuild/main.py              # Main orchestrator
src/tractionbuild/core/workflow_engine.py  # Workflow execution
config/workflows.yaml                  # Workflow definitions
config/agents.yaml                     # Agent configurations

# Database & persistence
src/tractionbuild/database/project_registry.py  # Data layer
init_db.sql                           # Database schema

# Tools & integrations
src/tractionbuild/tools/              # Custom tools directory
src/tractionbuild/crews/              # Agent crews
```

### Learning Path

**Week 1: Getting Started**
- Complete this onboarding guide
- Run your first project end-to-end
- Understand the basic architecture

**Week 2: Deep Dive**
- Study the comprehensive technical guide
- Run the test suite
- Fix a small bug or add a test

**Week 3: Contributing**
- Pick a TODO item from the codebase
- Implement a small feature
- Submit your first pull request

### Next Steps

1. **Set up your development environment** (see Quick Start above)
2. **Run a test project** to see the system in action
3. **Read the technical documentation** for deeper understanding
4. **Pick a task** from the "What Needs to Be Done" section
5. **Join the team Slack** and introduce yourself

---

## 🎉 Welcome to the Team!

You're now equipped to contribute to TractionBuild! Remember:

- **Start small**: Fix bugs or add tests before major features
- **Ask questions**: No question is too basic
- **Document everything**: Keep docs current as you work
- **Test thoroughly**: Quality over speed
- **Have fun**: Building AI-powered product studios is awesome!

**Questions?** Reach out in Slack or create a GitHub discussion.

**Happy coding! 🚀**
