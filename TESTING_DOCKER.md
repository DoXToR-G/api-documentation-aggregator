# 🐳 Docker Testing Guide

Complete guide to building and testing the entire system locally in Docker.

## 📋 Prerequisites

- Docker Desktop installed and running
- At least 8GB RAM allocated to Docker
- Ports available: 3000, 5433, 6379, 8000, 9200

## 🚀 Quick Start

### 1. Clean Start (Recommended)

```bash
# Stop and remove all containers
docker-compose down -v

# Remove old images (optional)
docker system prune -a

# Build all services
docker-compose build

# Start all services
docker-compose up -d
```

### 2. Check Service Status

```bash
# View all services
docker-compose ps

# Expected output:
# NAME                  STATUS              PORTS
# backend               Up (healthy)        0.0.0.0:8000->8000/tcp
# celery_beat           Up
# celery_worker         Up
# elasticsearch         Up (healthy)        0.0.0.0:9200->9200/tcp
# frontend              Up                  0.0.0.0:3000->3000/tcp
# postgres              Up (healthy)        0.0.0.0:5433->5432/tcp
# redis                 Up (healthy)        0.0.0.0:6379->6379/tcp
```

### 3. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery_worker
```

## ✅ Testing Checklist

### 1. **PostgreSQL Database**

```bash
# Test connection
curl -f http://localhost:8000/health | jq

# Expected: "database": "connected"
```

### 2. **Redis**

```bash
# Test Redis
docker-compose exec redis redis-cli ping

# Expected: PONG
```

### 3. **Elasticsearch**

```bash
# Test Elasticsearch
curl http://localhost:9200/_cluster/health | jq

# Expected: "status": "green" or "yellow"
```

### 4. **Backend API**

```bash
# Health check
curl http://localhost:8000/health | jq

# Root endpoint
curl http://localhost:8000/ | jq

# API docs
open http://localhost:8000/docs
```

### 5. **Celery Worker**

```bash
# Check worker logs
docker-compose logs celery_worker | grep "ready"

# Expected: celery@... ready
```

### 6. **Celery Beat (Scheduler)**

```bash
# Check scheduler logs
docker-compose logs celery_beat | grep "Scheduler"

# Expected: Scheduler: Sending due task...
```

### 7. **Frontend**

```bash
# Access frontend
open http://localhost:3000

# Check if page loads without errors
```

## 🧪 End-to-End Testing

### Test 1: Manual Documentation Fetch

```bash
# Trigger Kubernetes documentation fetch
curl -X POST "http://localhost:8000/api/v1/fetcher/sync/provider/kubernetes?use_celery=false"

# Check status
curl "http://localhost:8000/api/v1/fetcher/status/latest/kubernetes" | jq
```

### Test 2: Search Functionality

```bash
# Search for "pod" in API documentation
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "pod",
    "filters": {
      "provider": "kubernetes"
    }
  }' | jq
```

### Test 3: AI Query

```bash
# Query the AI agent
curl -X POST "http://localhost:8000/ai/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I list all pods in Kubernetes?",
    "context": {},
    "session_id": "test-123"
  }' | jq
```

### Test 4: Vector Store

```bash
# Check vector store stats
curl http://localhost:8000/vector-store/stats | jq
```

### Test 5: WebSocket Chat (using wscat)

```bash
# Install wscat if not installed
npm install -g wscat

# Connect to WebSocket
wscat -c ws://localhost:8000/ws/ai

# Send message (after connection)
{"type": "query", "query": "Help me search for APIs", "session_id": "test-456"}

# Expected: AI response
```

## 🎨 Frontend Testing

### 1. **Home Page**
- Navigate to http://localhost:3000
- ✅ Check: Logo, hero section, features display
- ✅ Check: Provider grid shows providers

### 2. **Search Page**
- Navigate to http://localhost:3000/search
- ✅ Type query: "create pod"
- ✅ Apply filter: Provider = Kubernetes
- ✅ Verify results display

### 3. **Chat Interface**
- Navigate to http://localhost:3000/chat
- ✅ Check connection status (green dot)
- ✅ Send message: "How do I use the Kubernetes API?"
- ✅ Verify AI responds

### 4. **Theme Toggle**
- ✅ Click moon/sun icon in header
- ✅ Verify dark/light mode switches
- ✅ Reload page - theme persists

### 5. **Responsive Design**
- ✅ Resize browser window
- ✅ Check mobile view (< 640px)
- ✅ Check tablet view (768px - 1024px)

## 🔧 Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker-compose logs backend

# Common issues:
# - Database not ready: Wait for postgres health check
# - Port conflict: Check if port 8000 is in use
# - Missing env vars: Check docker-compose.yml environment section
```

### Frontend Won't Build

```bash
# Check logs
docker-compose logs frontend

# Common issues:
# - Node modules: Rebuild with --no-cache
docker-compose build --no-cache frontend

# - TypeScript errors: Check component files
# - Missing dependencies: npm install in frontend/
```

### Celery Tasks Not Running

```bash
# Check worker status
docker-compose logs celery_worker

# Check scheduler
docker-compose logs celery_beat

# Restart Celery services
docker-compose restart celery_worker celery_beat
```

### Database Connection Issues

```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Verify connection
docker-compose exec postgres psql -U api_user -d api_docs_db -c "\dt"

# Expected: List of tables
```

### Elasticsearch Issues

```bash
# Check Elasticsearch status
curl http://localhost:9200/_cat/health

# Increase memory if needed (in docker-compose.yml):
# ES_JAVA_OPTS=-Xms1g -Xmx1g
```

## 📊 Performance Testing

### Load Test Backend

```bash
# Install Apache Bench
# sudo apt-get install apache2-utils

# Test health endpoint
ab -n 1000 -c 10 http://localhost:8000/health

# Test search endpoint
ab -n 100 -c 5 -p search.json -T application/json http://localhost:8000/api/v1/search
```

### Monitor Resources

```bash
# Docker stats
docker stats

# Expected resource usage:
# Backend: ~200-500 MB
# Frontend: ~150-300 MB
# PostgreSQL: ~100-200 MB
# Elasticsearch: ~1-2 GB
# Redis: ~10-50 MB
# Celery Worker: ~200-400 MB
```

## 🔄 Reset & Rebuild

### Full Reset

```bash
# Stop everything
docker-compose down -v

# Remove all images
docker rmi $(docker images -q latest_api_project*)

# Rebuild from scratch
docker-compose build --no-cache

# Start fresh
docker-compose up -d
```

### Reset Database Only

```bash
# Stop services
docker-compose down

# Remove database volume
docker volume rm latest_api_project_postgres_data

# Restart
docker-compose up -d
```

## ✅ Success Criteria

All of these should pass:

- [ ] All 7 services running and healthy
- [ ] Backend health check returns "healthy"
- [ ] Frontend loads at http://localhost:3000
- [ ] Can fetch documentation via API
- [ ] Search returns results
- [ ] AI chat responds to queries
- [ ] WebSocket connection works
- [ ] Theme toggle works
- [ ] Celery worker processes tasks
- [ ] No error logs in any service

## 📝 Next Steps After Testing

1. **Populate Database**: Run all fetchers to get real API documentation
2. **Test Scheduled Tasks**: Wait for Celery Beat to run automatic syncs
3. **Frontend Development**: Add remaining components
4. **Add Authentication**: Secure API endpoints
5. **Production Deploy**: Set up production environment

## 🎉 If Everything Works

You now have a fully functional MCP-Based API Documentation Aggregator with:
- ✅ Multi-provider API documentation fetching
- ✅ AI-powered semantic search
- ✅ Real-time chat interface
- ✅ Scheduled automatic updates
- ✅ Modern responsive frontend
- ✅ Complete Docker infrastructure

---

**Happy Testing! 🚀**

For issues, check logs and refer to troubleshooting section above.
