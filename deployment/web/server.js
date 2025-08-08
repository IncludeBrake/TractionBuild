const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const morgan = require('morgan');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(helmet());
app.use(compression());
app.use(morgan('combined'));
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// API Routes
app.get('/api/health', (req, res) => {
    res.json({ 
        status: 'healthy', 
        service: 'ZeroToShip Web Interface',
        version: '1.0.0'
    });
});

app.get('/api/projects', (req, res) => {
    // Placeholder for projects endpoint
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
});

app.post('/api/mermaid', (req, res) => {
    // Placeholder for Mermaid diagram generation
    const { diagram } = req.body;
    
    if (!diagram) {
        return res.status(400).json({ error: 'Diagram definition required' });
    }
    
    // Here you would integrate with Mermaid.js to generate SVG
    res.json({
        svg: `<svg>Generated diagram for: ${diagram}</svg>`,
        diagram: diagram
    });
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
});

module.exports = app; 