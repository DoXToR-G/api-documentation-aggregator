-- Database initialization script
-- This script creates the initial database structure and seed data

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create the api_providers table
CREATE TABLE IF NOT EXISTS api_providers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    base_url TEXT NOT NULL,
    documentation_url TEXT NOT NULL,
    icon_url TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the api_documents table
CREATE TABLE IF NOT EXISTS api_documents (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER REFERENCES api_providers(id),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    url TEXT,
    method VARCHAR(10),
    endpoint VARCHAR(500),
    tags TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the search_logs table
CREATE TABLE IF NOT EXISTS search_logs (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    results_count INTEGER DEFAULT 0,
    search_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default API providers
INSERT INTO api_providers (name, display_name, base_url, documentation_url, icon_url, description, is_active) VALUES
('datadog', 'Datadog', 'https://api.datadoghq.com', 'https://docs.datadoghq.com/api/latest/', 'https://datadog-docs.imgix.net/images/dd_logo_n_70x75.png', 'Monitoring and observability platform with comprehensive APIs for metrics, logs, and traces', true),
('jira_cloud', 'Jira Cloud', 'https://api.atlassian.com', 'https://developer.atlassian.com/cloud/jira/platform/rest/v3/', 'https://atlassian.design/resources/logo-library', 'Atlassian Jira Cloud REST API for issue tracking and project management', true),
('kubernetes', 'Kubernetes', 'https://kubernetes.io', 'https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.28/', 'https://kubernetes.io/images/kubernetes-horizontal-color.png', 'Container orchestration platform API for managing clusters and workloads', true),
('prometheus', 'Prometheus', 'https://prometheus.io', 'https://prometheus.io/docs/prometheus/latest/querying/api/', 'https://prometheus.io/assets/prometheus_logo_grey.svg', 'Open-source monitoring system with HTTP API for querying metrics', true),
('grafana', 'Grafana', 'https://grafana.com', 'https://grafana.com/docs/grafana/latest/developers/http_api/', 'https://grafana.com/static/img/logos/grafana_logo.svg', 'Observability platform API for dashboards, data sources, and alerting', true),
('kibana', 'Kibana', 'https://www.elastic.co', 'https://www.elastic.co/guide/en/kibana/current/api.html', 'https://www.elastic.co/favicon.ico', 'Elasticsearch data visualization platform with REST APIs for saved objects and spaces', true)
ON CONFLICT (name) DO NOTHING; 