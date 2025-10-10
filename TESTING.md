# 🧪 Testing Guide for MCP-Based API Documentation System

This guide will help you test the MCP-based API documentation system both locally and with Docker.

## 📋 Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PowerShell (for Windows testing script)

## 🔍 Code Crosscheck Results

### ✅ **What's Working Well:**

1. **MCP Architecture**: Complete MCP server, client, and tool framework
2. **AI Agent**: Enhanced AI agent with intent analysis and context awareness
3. **Vector Store**: ChromaDB integration for semantic search
4. **API Endpoints**: All AI endpoints properly implemented
5. **Docker Setup**: Complete containerization with proper environment variables

### 🔧 **Issues Fixed:**

1. **Import Order**: Fixed startup event definition order in main.py
2. **Docker Configuration**: Updated docker-compose.yml with MCP-specific settings
3. **Volume Management**: Added ChromaDB persistent storage
4. **Environment Variables**: Added all necessary MCP and AI configuration

## 🚀 Testing Steps

### **Step 1: Verify Prerequisites**

Ensure Docker Desktop is running and you have:
- Docker & Docker Compose installed
- Python 3.11+ (for local development)
- Ports 8000, 5433, 9200 available

### **Step 2: Docker Build and Test**

#### **Option A: Use PowerShell Script (Windows)**
```powershell
.\build_and_test.ps1
```

#### **Option B: Manual Docker Commands**
```bash
# Build the backend
docker-compose build backend

# Start services
docker-compose up -d postgres redis elasticsearch

# Wait for services to be healthy, then start backend
docker-compose up -d backend

# Check status
docker-compose ps
```

### **Step 3: Verify System Health**

1. **Health Check**: http://localhost:8000/health
2. **API Documentation**: http://localhost:8000/docs
3. **Root Endpoint**: http://localhost:8000/
4. **AI Status**: http://localhost:8000/ai/status

### **Step 4: Test AI Endpoints**

#### **Test AI Query**
```bash
curl -X POST "http://localhost:8000/ai/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I search for API endpoints?",
    "context": {},
    "session_id": "test-session-123"
  }'
```

#### **Test AI Status**
```bash
curl http://localhost:8000/ai/status
```

#### **Test Conversation History**
```bash
curl "http://localhost:8000/ai/conversation/test-session-123"
```

## 🧪 Test Scenarios

### **1. Basic Functionality**
- ✅ System startup and health checks
- ✅ Database connectivity
- ✅ Vector store initialization
- ✅ MCP client connection

### **2. AI Agent Capabilities**
- ✅ Intent analysis with confidence scoring
- ✅ Context-aware responses
- ✅ Session management
- ✅ Conversation history

### **3. MCP Tools**
- ✅ Tool listing and validation
- ✅ Search API documentation
- ✅ Get API endpoint details
- ✅ Analyze API usage
- ✅ Suggest improvements

### **4. Vector Store**
- ✅ Document storage and retrieval
- ✅ Semantic search
- ✅ Embedding generation
- ✅ Collection management

## 🔧 Troubleshooting

### **Common Issues:**

1. **Docker Build Fails**
   - Check Docker Desktop is running
   - Ensure sufficient disk space
   - Clear Docker cache: `docker system prune -f`

2. **Services Won't Start**
   - Check port conflicts (8000, 5432, 6379, 9200)
   - Verify Docker Compose version compatibility
   - Check service health checks

3. **AI Agent Errors**
   - Verify all dependencies are installed
   - Check environment variables
   - Review backend logs: `docker-compose logs backend`

### **Debug Commands:**

```bash
# View backend logs
docker-compose logs -f backend

# Check service status
docker-compose ps

# Restart specific service
docker-compose restart backend

# Access backend container
docker-compose exec backend bash
```

## 📊 Expected Test Results

### **Successful Test Output:**
```
🚀 Building and Testing MCP-Based API Documentation System
✅ Docker is running
✅ Backend built successfully
✅ Health check passed: healthy
✅ Root endpoint working: MCP-Based API Documentation Aggregator
✅ AI status working: 0 conversations
✅ AI query working: Intent detected: search
🎉 Testing completed!
```

### **API Response Examples:**

#### **Health Check:**
```json
{
  "status": "healthy",
  "database": "connected",
  "vector_store": "connected",
  "vector_store_stats": {
    "total_documents": 0,
    "collection_name": "api_documentation"
  }
}
```

#### **AI Query Response:**
```json
{
  "query": "How do I search for API endpoints?",
  "intent": {
    "type": "search",
    "confidence": 0.95,
    "tools": ["search_api_docs"]
  },
  "response": {
    "type": "enhanced_search_results",
    "results": [...],
    "total": 1
  }
}
```

## 🎯 Next Steps After Testing

1. **Frontend Development**: Build React/Next.js interface
2. **Real Data Integration**: Connect to actual API providers
3. **Advanced AI Features**: Implement LLM integration
4. **Production Deployment**: Configure production environment
5. **Monitoring & Analytics**: Add observability tools

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review Docker and backend logs
3. Verify all prerequisites are met
4. Check GitHub issues for known problems

---

**Happy Testing! 🚀**
