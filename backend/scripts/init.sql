-- Database initialization script
-- This script creates the initial database structure and seed data

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Insert default API providers
INSERT INTO api_providers (name, display_name, base_url, documentation_url, icon_url, description, is_active) VALUES
('datadog', 'Datadog', 'https://api.datadoghq.com', 'https://docs.datadoghq.com/api/latest/', 'https://datadog-docs.imgix.net/images/dd_logo_n_70x75.png', 'Monitoring and observability platform with comprehensive APIs for metrics, logs, and traces', true),
('jira_cloud', 'Jira Cloud', 'https://api.atlassian.com', 'https://developer.atlassian.com/cloud/jira/platform/rest/v3/', 'https://atlassian.design/resources/logo-library', 'Atlassian Jira Cloud REST API for issue tracking and project management', true),
('kubernetes', 'Kubernetes', 'https://kubernetes.io', 'https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.28/', 'https://kubernetes.io/images/kubernetes-horizontal-color.png', 'Container orchestration platform API for managing clusters and workloads', true),
('prometheus', 'Prometheus', 'https://prometheus.io', 'https://prometheus.io/docs/prometheus/latest/querying/api/', 'https://prometheus.io/assets/prometheus_logo_grey.svg', 'Open-source monitoring system with HTTP API for querying metrics', true),
('grafana', 'Grafana', 'https://grafana.com', 'https://grafana.com/docs/grafana/latest/developers/http_api/', 'https://grafana.com/static/img/logos/grafana_logo.svg', 'Observability platform API for dashboards, data sources, and alerting', true),
('kibana', 'Kibana', 'https://www.elastic.co', 'https://www.elastic.co/guide/en/kibana/current/api.html', 'https://www.elastic.co/favicon.ico', 'Elasticsearch data visualization platform with REST APIs for saved objects and spaces', true)
ON CONFLICT (name) DO NOTHING; 