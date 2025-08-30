-- Initialize ZeroToShip database schema

-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    state VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    metadata JSONB DEFAULT '{}',
    results JSONB DEFAULT '{}'
);

-- Create execution_logs table
CREATE TABLE IF NOT EXISTS execution_logs (
    id SERIAL PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    duration_ms INTEGER NOT NULL,
    result JSONB,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_projects_state ON projects(state);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at);
CREATE INDEX IF NOT EXISTS idx_execution_logs_project_id ON execution_logs(project_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_agent_name ON execution_logs(agent_name);
CREATE INDEX IF NOT EXISTS idx_execution_logs_created_at ON execution_logs(created_at);

-- Enable pg_stat_statements extension
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
