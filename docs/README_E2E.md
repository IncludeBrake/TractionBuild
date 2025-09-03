# tractionbuild E2E Implementation

## 🚀 Quick Start

### 1. Start the Services
```bash
make up
```

### 2. Initialize Database
```bash
# Connect to Postgres and run the schema
docker exec -it tractionbuild-postgres-1 psql -U postgres -d tractionbuild -f /docker-entrypoint-initdb.d/init_db.sql
```

### 3. Test the API
```bash
# Run the E2E test
python test_e2e.py
```

## 📋 Definition of "Shipped"

✅ **docker compose up -d --build** - Services start successfully  
✅ **curl -X POST /api/v1/projects** → Returns project ID  
✅ **Within 60s, GET /status** → Returns COMPLETED  
✅ **Postgres** - Projects row + 2 execution_logs rows  
✅ **Neo4j** - Project node + 2 artifacts linked  
✅ **/metrics** - Shows 2 agent executions, 0 errors  

## 🔧 Architecture

### Core Components
- **Schemas** (`src/tractionbuild/schemas/core.py`) - Frozen contracts for all crews
- **Adapters** (`src/tractionbuild/crews/adapters.py`) - Wrap existing crews with schema enforcement
- **Workflow Engine** (`src/tractionbuild/core/workflow_engine.py`) - Drives Validator → Advisory → COMPLETED
- **API** (`src/tractionbuild/api/app.py`) - Clean REST API with 3 endpoints
- **Database** - Postgres for projects/logs, Neo4j for artifacts

### API Endpoints
- `POST /api/v1/projects` - Create project, start workflow
- `GET /api/v1/projects/{id}` - Get project with artifacts
- `GET /api/v1/projects/{id}/status` - Get status and progress
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

### Observability
- **3 Core Metrics**: Request counts, durations, project counts
- **Structured Logs**: JSON format with project_id, agent, duration
- **Health Checks**: Database connectivity verification

## 🧪 Testing

### Manual Testing
```bash
# Create a project
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Project",
    "description": "A test project",
    "hypothesis": "This will work",
    "target_avatars": ["sme"],
    "workflow": "validation_and_launch"
  }'

# Check status
curl http://localhost:8000/api/v1/projects/{PROJECT_ID}/status

# Get results
curl http://localhost:8000/api/v1/projects/{PROJECT_ID}
```

### Automated Testing
```bash
# Run E2E test
python test_e2e.py

# Run unit tests
make test
```

## 📊 Monitoring

### Metrics Available
- `tractionbuild_requests_total` - Total API requests
- `tractionbuild_requests_success` - Successful requests
- `tractionbuild_requests_error` - Failed requests
- `tractionbuild_request_duration_seconds` - Average request latency
- `tractionbuild_projects_created` - Total projects created
- `tractionbuild_projects_retrieved` - Total projects retrieved

### Health Check
```bash
curl http://localhost:8000/health
```

## 🔄 Workflow

1. **Project Creation** - User submits project data
2. **Validator Crew** - Validates market hypothesis and target avatars
3. **Advisory Board** - Provides go/no-go decision and recommendations
4. **Completion** - Results stored in Postgres and Neo4j

## 🛠️ Development

### Makefile Commands
- `make up` - Start services
- `make down` - Stop services
- `make test` - Run tests
- `make fmt` - Format code

### Adding New Crews
1. Create crew class inheriting from BaseCrew
2. Create adapter in `src/tractionbuild/crews/adapters.py`
3. Register in workflow engine
4. Update schemas if needed

## 🚨 Troubleshooting

### Common Issues
1. **Database Connection** - Check Postgres/Neo4j are running
2. **Crew Failures** - Check LLM API keys and crew configuration
3. **Timeout Errors** - Increase step_timeout in WorkflowEngine
4. **Schema Validation** - Ensure crew outputs match Pydantic models

### Logs
```bash
# View API logs
docker logs tractionbuild-api-1

# View database logs
docker logs tractionbuild-postgres-1
docker logs tractionbuild-neo4j-1
```
