# 🚀 ZeroToShip

**AI-powered product studio that validates ideas, builds MVPs, and launches full products**

ZeroToShip is a self-evolving AI-powered product studio that validates ideas, builds MVPs, launches full products, and stores learnings to continuously improve.

## 🎯 Features

- **Idea Validation**: Market research and MVP scoping
- **Execution Planning**: Task decomposition and prioritization
- **Code Generation**: Automated software development
- **Launch Preparation**: Marketing assets and positioning
- **Learning System**: Graph-based memory and feedback loops

## 🛠️ Tech Stack

### Core Technologies
- **Python 3.12** - Main development language
- **CrewAI** - Multi-agent orchestration
- **Neo4j AuraDB** - Graph database for knowledge storage
- **Node.js** - JavaScript runtime for web components
- **Mermaid** - Diagram generation and visualization

### Key Dependencies
- `crewai[tools]` - AI agent framework with tool integration
- `python-dotenv` - Environment variable management
- `pyyaml` - Configuration file handling
- `neo4j` - Graph database driver
- `fastapi` - Web API framework
- `uvicorn` - ASGI server

## 🚀 Quick Start

### Prerequisites

1. **Python 3.12+**
2. **Node.js 18+**
3. **Neo4j AuraDB account**
4. **OpenAI API key**

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/zerotoship/zerotoship.git
   cd zerotoship
   ```

2. **Set up Python environment**
   ```bash
   uv venv --python 3.12
   .venv\Scripts\Activate.ps1  # Windows
   # source .venv/bin/activate  # Linux/Mac
   uv sync
   ```

3. **Install Node.js dependencies**
   ```bash
   npm install
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Set up Neo4j AuraDB**
   - Create a free AuraDB instance
   - Update `.env` with your connection details

### Usage

```bash
# Run the main ZeroToShip engine
python -m zerotoship.cli

# Start the web interface
uvicorn zerotoship.api:app --reload

# Run tests
pytest
```

## 🐳 Docker

### Quick Start with Docker

1. **Build the image**
   ```bash
   docker build -t zerotoship .
   ```

2. **Run with default settings**
   ```bash
   docker run -p 8000:8000 zerotoship
   ```

3. **Run with custom idea and workflow**
   ```bash
   docker run -p 8000:8000 \
     -e IDEA="Build a task management app" \
     -e WORKFLOW="validation_and_launch" \
     zerotoship
   ```

### Using Docker Compose

1. **Run with default settings**
   ```bash
   docker-compose up
   ```

2. **Run with custom environment variables**
   ```bash
   IDEA="Build a social media platform" WORKFLOW="validation_and_launch" docker-compose up
   ```

3. **Run with Neo4j database**
   ```bash
   docker-compose --profile with-database up
   ```

4. **Run with external Neo4j (Neo4j running on host)**
   ```bash
   docker-compose --profile external-neo4j up
   ```

### Docker Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `IDEA` | "Default Production Idea" | The product idea to process |
| `WORKFLOW` | "validation_and_launch" | The workflow to execute |
| `NEO4J_PASSWORD` | "test_password" | Neo4j database password |
| `PROMETHEUS_PORT` | 8000 | Port for Prometheus metrics |
| `MEMORY_FILE_PATH` | "/app/output/project_memory.json" | Path for project memory files |
| `CREWAI_MEMORY_PATH` | "/app/output/crewai_memory" | Path for CrewAI memory files |
| `HOME` | "/app" | Home directory for the container user |
| `NEO4J_URI` | "neo4j://host.docker.internal:7687" | Neo4j database URI for Docker compatibility |

### Docker Health Checks

The container includes health checks that monitor:
- Prometheus metrics endpoint availability
- Application responsiveness
- Configuration file presence

### Docker Volumes

The container uses the following volumes:
- `./output:/app/output` - Application output and logs
- `./data:/app/data` - Application data storage

### Docker Troubleshooting

#### Permission Issues
If you encounter permission errors like `[Errno 13] Permission denied: '/home/zerotoship'`, the container is properly configured to handle this. The application now writes all files to `/app/output/` where the non-root user has proper permissions.

#### Memory File Issues
The container automatically sets up the following memory paths:
- Project memory: `/app/output/project_memory.json`
- CrewAI memory: `/app/output/crewai_memory/`
- Home directory: `/app`

#### Neo4j Connection Issues
If you encounter `Neo4j service unavailable: Unable to retrieve routing information`, the container is configured to connect to Neo4j on the host machine using `host.docker.internal:7687`. 

**For local development:**
- Ensure Neo4j is running on your host machine on port 7687
- The container will automatically connect to `host.docker.internal:7687`

**For production:**
- Set the `NEO4J_URI` environment variable to your actual Neo4j instance
- Example: `NEO4J_URI=neo4j://your-neo4j-server:7687`

**Testing Neo4j connectivity:**
```bash
# Test from within the container
docker exec zerotoship-app python test_neo4j_connection.py

# Or test from host (if Neo4j is running locally)
python test_neo4j_connection.py
```

#### Testing the Container
You can test the container build and run with:

**Linux/Mac:**
```bash
chmod +x test_docker.sh
./test_docker.sh
```

**Windows:**
```powershell
.\test_docker.ps1
```

## 🏗️ Architecture

### Agent Crews

1. **Validator Crew**: Market research and idea validation
2. **Execution Graph Crew**: Task decomposition and planning
3. **Builder Crew**: Code generation and development
4. **Marketing Crew**: Launch preparation and positioning
5. **Feedback Crew**: Learning and improvement

### Data Flow

```
Input Idea → Validation → Execution Graph → Build → Launch → Feedback
     ↓           ↓              ↓           ↓        ↓        ↓
  Market    MVP Scope    Task Tree    Code    Assets   Learning
  Research   Definition   Planning   Generation  Creation  Storage
```

## 📁 Project Structure

```
zerotoship/
├── src/zerotoship/
│   ├── agents/          # CrewAI agents
│   ├── crews/           # Agent crews
│   ├── tools/           # Custom tools
│   ├── models/          # Data models
│   ├── database/        # Neo4j integration
│   ├── api/             # FastAPI endpoints
│   ├── cli/             # Command line interface
│   └── utils/           # Utilities
├── tests/               # Test suite
├── docs/                # Documentation
├── config/              # Configuration files
├── scripts/             # Utility scripts
└── web/                 # Frontend components
```

## 🔧 Configuration

### Environment Variables

```bash
# Core Configuration
PROJECT_NAME=ZeroToShip
ENVIRONMENT=development

# AI Providers
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4-turbo-preview
ANTHROPIC_API_KEY=your_anthropic_api_key

# Database
NEO4J_URI=bolt://your-aura-instance.neo4j.io:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Logging
LOG_LEVEL=INFO
CREWAI_LOG_LEVEL=INFO
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=zerotoship

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m slow
```

## 📊 Monitoring

- **Prometheus** metrics for system monitoring
- **Grafana** dashboards for visualization
- **Structured logging** with structlog
- **OpenTelemetry** for distributed tracing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🆘 Support

- **Documentation**: [https://zerotoship.dev](https://zerotoship.dev)
- **Issues**: [GitHub Issues](https://github.com/zerotoship/zerotoship/issues)
- **Discussions**: [GitHub Discussions](https://github.com/zerotoship/zerotoship/discussions)

## 🚀 Roadmap

- [ ] Multi-language code generation
- [ ] Advanced graph visualization
- [ ] Real-time collaboration
- [ ] Enterprise security features
- [ ] Mobile app development
- [ ] AI model fine-tuning

---

**Built with ❤️ by the ZeroToShip team** 