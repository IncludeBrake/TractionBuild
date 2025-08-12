const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const morgan = require('morgan');
const path = require('path');
const axios = require('axios');
const { exec } = require('child_process');
const { promisify } = require('util');
require('dotenv').config();

const execAsync = promisify(exec);
const app = express();
const PORT = process.env.PORT || 3000;

// Backend configuration
const BACKEND_CONFIG = {
    // Docker container endpoints
    docker: {
        host: process.env.DOCKER_HOST || 'localhost',
        port: process.env.DOCKER_PORT || 8000,
        healthEndpoint: '/health',
        metricsEndpoint: '/metrics'
    },
    // Kubernetes endpoints
    kubernetes: {
        namespace: process.env.K8S_NAMESPACE || 'zerotoship',
        service: process.env.K8S_SERVICE || 'zerotoship-app'
    },
    // Python application endpoints
    python: {
        host: process.env.PYTHON_HOST || 'localhost',
        port: process.env.PYTHON_PORT || 8000
    }
};

// Middleware
app.use(helmet());
app.use(compression());
app.use(morgan('combined'));
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Utility functions
async function checkDockerContainer() {
    try {
        const { stdout } = await execAsync('docker ps --filter "name=zerotoship" --format "{{.Names}}:{{.Status}}"');
        return stdout.trim().split('\n').filter(line => line.length > 0);
    } catch (error) {
        console.error('Docker check failed:', error.message);
        return [];
    }
}

async function checkKubernetesPods() {
    try {
        const { stdout } = await execAsync(`kubectl get pods -n ${BACKEND_CONFIG.kubernetes.namespace} -o json`);
        return JSON.parse(stdout);
    } catch (error) {
        console.error('Kubernetes check failed:', error.message);
        return { items: [] };
    }
}

async function executeZeroToShipWorkflow(idea, workflow) {
    try {
        // Try Docker first, then Kubernetes, then local Python
        const endpoints = [
            `http://${BACKEND_CONFIG.docker.host}:${BACKEND_CONFIG.docker.port}`,
            `http://${BACKEND_CONFIG.kubernetes.service}.${BACKEND_CONFIG.kubernetes.namespace}.svc.cluster.local:8000`,
            `http://${BACKEND_CONFIG.python.host}:${BACKEND_CONFIG.python.port}`
        ];

        for (const endpoint of endpoints) {
            try {
                console.log(`Trying endpoint: ${endpoint}`);
                const response = await axios.post(`${endpoint}/api/execute`, {
                    idea: idea,
                    workflow: workflow
                }, {
                    timeout: 30000 // 30 second timeout
                });
                return response.data;
            } catch (error) {
                console.log(`Endpoint ${endpoint} failed:`, error.message);
                continue;
            }
        }
        throw new Error('All backend endpoints failed');
    } catch (error) {
        console.error('Workflow execution failed:', error.message);
        throw error;
    }
}

// Routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Enhanced API Routes
app.get('/api/health', async (req, res) => {
    try {
        const dockerStatus = await checkDockerContainer();
        const k8sStatus = await checkKubernetesPods();
        
        res.json({ 
            status: 'healthy', 
            service: 'ZeroToShip Web Interface',
            version: '1.0.0',
            backend: {
                docker: {
                    containers: dockerStatus,
                    status: dockerStatus.length > 0 ? 'running' : 'not_found'
                },
                kubernetes: {
                    pods: k8sStatus.items.length,
                    status: k8sStatus.items.length > 0 ? 'running' : 'not_found'
                }
            }
        });
    } catch (error) {
        res.status(500).json({ 
            status: 'error',
            error: error.message 
        });
    }
});

app.get('/api/backend/status', async (req, res) => {
    try {
        const [dockerContainers, k8sPods] = await Promise.all([
            checkDockerContainer(),
            checkKubernetesPods()
        ]);

        res.json({
            docker: {
                containers: dockerContainers,
                count: dockerContainers.length
            },
            kubernetes: {
                pods: k8sPods.items,
                count: k8sPods.items.length,
                namespace: BACKEND_CONFIG.kubernetes.namespace
            }
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/api/projects', async (req, res) => {
    try {
        // Try to get projects from backend
        const endpoints = [
            `http://${BACKEND_CONFIG.docker.host}:${BACKEND_CONFIG.docker.port}/api/projects`,
            `http://${BACKEND_CONFIG.python.host}:${BACKEND_CONFIG.python.port}/api/projects`
        ];

        for (const endpoint of endpoints) {
            try {
                const response = await axios.get(endpoint, { timeout: 5000 });
                return res.json(response.data);
            } catch (error) {
                console.log(`Project endpoint ${endpoint} failed:`, error.message);
                continue;
            }
        }

        // Fallback to local data
        res.json({
            projects: [
                {
                    id: '1',
                    name: 'Sample Project',
                    status: 'in_progress',
                    created_at: new Date().toISOString()
                }
            ]
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/api/execute', async (req, res) => {
    try {
        const { idea, workflow = 'default_software_build' } = req.body;
        
        if (!idea) {
            return res.status(400).json({ error: 'Idea is required' });
        }

        console.log(`Executing workflow: ${workflow} for idea: ${idea}`);
        
        const result = await executeZeroToShipWorkflow(idea, workflow);
        
        res.json({
            success: true,
            result: result,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        console.error('Execution error:', error);
        res.status(500).json({ 
            success: false,
            error: error.message 
        });
    }
});

app.post('/api/docker/start', async (req, res) => {
    try {
        const { idea, workflow } = req.body;
        const command = `docker run -d -p 8000:8000 --name zerotoship-execution zerotoship:latest "${idea}" "${workflow}"`;
        
        const { stdout } = await execAsync(command);
        
        res.json({
            success: true,
            container_id: stdout.trim(),
            message: 'Docker container started successfully'
        });
    } catch (error) {
        res.status(500).json({ 
            success: false,
            error: error.message 
        });
    }
});

app.post('/api/kubernetes/deploy', async (req, res) => {
    try {
        const { idea, workflow } = req.body;
        
        // Update the deployment with new environment variables
        const updateCommand = `kubectl set env deployment/zerotoship-app -n ${BACKEND_CONFIG.kubernetes.namespace} IDEA="${idea}" WORKFLOW="${workflow}"`;
        await execAsync(updateCommand);
        
        // Restart the deployment
        const restartCommand = `kubectl rollout restart deployment/zerotoship-app -n ${BACKEND_CONFIG.kubernetes.namespace}`;
        await execAsync(restartCommand);
        
        res.json({
            success: true,
            message: 'Kubernetes deployment updated and restarted'
        });
    } catch (error) {
        res.status(500).json({ 
            success: false,
            error: error.message 
        });
    }
});

app.get('/api/metrics', async (req, res) => {
    try {
        const endpoints = [
            `http://${BACKEND_CONFIG.docker.host}:${BACKEND_CONFIG.docker.port}/metrics`,
            `http://${BACKEND_CONFIG.python.host}:${BACKEND_CONFIG.python.port}/metrics`
        ];

        for (const endpoint of endpoints) {
            try {
                const response = await axios.get(endpoint, { timeout: 5000 });
                return res.set('Content-Type', 'text/plain').send(response.data);
            } catch (error) {
                console.log(`Metrics endpoint ${endpoint} failed:`, error.message);
                continue;
            }
        }

        res.status(404).json({ error: 'No metrics endpoint available' });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/api/mermaid', async (req, res) => {
    try {
        const { diagram, project_id } = req.body;
        
        if (!diagram) {
            return res.status(400).json({ error: 'Diagram definition required' });
        }

        // Try to get Mermaid diagram from backend
        const endpoints = [
            `http://${BACKEND_CONFIG.docker.host}:${BACKEND_CONFIG.docker.port}/api/mermaid`,
            `http://${BACKEND_CONFIG.python.host}:${BACKEND_CONFIG.python.port}/api/mermaid`
        ];

        for (const endpoint of endpoints) {
            try {
                const response = await axios.post(endpoint, { diagram, project_id }, { timeout: 10000 });
                return res.json(response.data);
            } catch (error) {
                console.log(`Mermaid endpoint ${endpoint} failed:`, error.message);
                continue;
            }
        }

        // Fallback to local generation
        res.json({
            svg: `<svg>Generated diagram for: ${diagram}</svg>`,
            diagram: diagram,
            project_id: project_id
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ 
        error: 'Something went wrong!',
        message: process.env.NODE_ENV === 'development' ? err.message : 'Internal server error'
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({ error: 'Not found' });
});

// Start server
app.listen(PORT, () => {
    console.log(`🚀 ZeroToShip Web Interface running on port ${PORT}`);
    console.log(`📊 Health check: http://localhost:${PORT}/api/health`);
    console.log(`🌐 Web interface: http://localhost:${PORT}`);
    console.log(`🔗 Backend integration enabled`);
    console.log(`   - Docker: ${BACKEND_CONFIG.docker.host}:${BACKEND_CONFIG.docker.port}`);
    console.log(`   - Kubernetes: ${BACKEND_CONFIG.kubernetes.namespace}/${BACKEND_CONFIG.kubernetes.service}`);
    console.log(`   - Python: ${BACKEND_CONFIG.python.host}:${BACKEND_CONFIG.python.port}`);
});

module.exports = app;
