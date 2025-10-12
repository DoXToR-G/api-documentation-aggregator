# How MCP (Model Context Protocol) Works in This Project

## Overview

The MCP (Model Context Protocol) in this project creates a **tool-based architecture** that separates the AI agent logic from the actual tool implementations. Think of it as a plugin system where:

- **MCP Server** = Defines what tools are available and implements them
- **MCP Client** = Calls those tools on behalf of the AI agent
- **Enhanced AI Agent** = Orchestrates which tools to use based on user intent

```
User Query
    ↓
Enhanced AI Agent (Orchestrator)
    ↓
MCP Client (Tool Caller)
    ↓
MCP Server (Tool Provider)
    ↓
Database / Vector Store / Analytics
```

---

## Architecture Components

### 1. **MCP Server** (`backend/app/mcp/server.py`)

**Purpose**: Defines and implements the available tools

**Key Features**:
- Registers 4 tools with their schemas
- Implements the actual tool logic
- Uses official `mcp` Python package

**Tools Provided**:

1. **`search_api_docs`** - Search API documentation
   ```python
   {
       "name": "search_api_docs",
       "description": "Search API documentation using semantic search",
       "inputSchema": {
           "query": str,           # Search text
           "provider_ids": [int],  # Filter by providers (Atlassian, K8s, etc.)
           "methods": [str],       # Filter by HTTP methods (GET, POST, etc.)
           "limit": int            # Max results
       }
   }
   ```
   - **Implementation**: Direct PostgreSQL query with ILIKE search
   - **Database**: Queries `api_documentation` table joined with `api_providers`
   - **Returns**: List of matching endpoints with title, description, provider, method

2. **`get_api_endpoint`** - Get specific endpoint details
   ```python
   {
       "name": "get_api_endpoint",
       "inputSchema": {
           "endpoint_id": int,     # Database ID
           "provider_id": int,     # Provider filter
           "path": str,            # Endpoint path
           "method": str           # HTTP method
       }
   }
   ```
   - **Implementation**: Query single endpoint by ID
   - **Returns**: Full endpoint details including request/response schemas

3. **`analyze_api_usage`** - Analyze usage patterns
   ```python
   {
       "name": "analyze_api_usage",
       "inputSchema": {
           "provider_id": int,
           "time_range": str,      # "1d", "7d", "30d", "90d"
           "metrics": [str]        # Which metrics to analyze
       }
   }
   ```
   - **Implementation**: Queries `search_queries` table
   - **Returns**: Usage statistics and patterns

4. **`suggest_api_improvements`** - Suggest documentation improvements
   ```python
   {
       "name": "suggest_api_improvements",
       "inputSchema": {
           "provider_id": int,
           "endpoint_id": int,
           "feedback_type": str    # "clarity", "examples", "structure"
       }
   }
   ```
   - **Implementation**: AI-based suggestions (placeholder)
   - **Returns**: Improvement recommendations

**Code Structure**:
```python
class APIDocMCPServer:
    def __init__(self):
        self.server = Server("api-doc-mcp-server")
        self.setup_handlers()

    def setup_handlers(self):
        @self.server.list_tools()
        async def list_tools():
            return [tool1, tool2, tool3, tool4]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict):
            if name == "search_api_docs":
                return await self.search_api_docs(**arguments)
            # ... other tools

    async def search_api_docs(self, query, provider_ids, methods, limit):
        # Direct database access
        db = SessionLocal()
        results = db.query(APIDocumentation).filter(...).all()
        return {"results": results}
```

---

### 2. **MCP Client** (`backend/app/mcp/client.py`)

**Purpose**: Provides the interface for the AI agent to call MCP tools

**Key Features**:
- Validates tool arguments against schemas
- Executes tools by calling their implementations
- Handles errors and logging

**How It Works**:

```python
class MCPClient:
    def __init__(self):
        self.available_tools = []  # List of tool definitions
        self.connection_status = "disconnected"

    async def connect(self):
        """Connect to MCP server (simulated in this implementation)"""
        self.connection_status = "connected"
        return True

    async def list_tools(self):
        """Return list of available tools"""
        return [
            {
                "name": "search_api_docs",
                "description": "...",
                "inputSchema": {...}
            },
            # ... other tools
        ]

    async def call_tool(self, tool_name: str, arguments: Dict):
        """
        Call a tool with validation:
        1. Check tool exists
        2. Validate arguments against schema
        3. Execute the tool
        4. Return results
        """
        tool = self._find_tool(tool_name)
        if not self._validate_arguments(arguments, tool["inputSchema"]):
            return {"error": "Invalid arguments"}

        return await self._execute_tool(tool_name, arguments)

    async def _execute_search_tool(self, arguments):
        """
        Actual implementation of search tool
        - Queries PostgreSQL database
        - Applies filters (provider, method)
        - Returns formatted results
        """
        db = SessionLocal()
        db_query = db.query(APIDocumentation).join(APIProvider)

        if arguments.get("provider_ids"):
            db_query = db_query.filter(
                APIDocumentation.provider_id.in_(arguments["provider_ids"])
            )

        if arguments.get("query"):
            search_term = f"%{arguments['query']}%"
            db_query = db_query.filter(
                or_(
                    APIDocumentation.title.ilike(search_term),
                    APIDocumentation.description.ilike(search_term)
                )
            )

        results = db_query.limit(arguments.get("limit", 10)).all()
        return {"results": results}
```

**Validation Process**:
```python
def _validate_arguments(self, arguments, schema):
    """
    Checks:
    - Required fields present
    - Field types correct (int, str, array)
    - Enum values valid
    """
    errors = []
    for field in schema["required"]:
        if field not in arguments:
            errors.append(f"Missing: {field}")
    return {"valid": len(errors) == 0, "errors": errors}
```

---

### 3. **Enhanced AI Agent** (`backend/app/services/enhanced_ai_agent.py`)

**Purpose**: Orchestrates the entire AI workflow

**Key Responsibilities**:
1. **Analyze user intent** - Classify what user wants (search, endpoint info, analytics)
2. **Select appropriate tools** - Choose which MCP tools to call
3. **Call MCP tools** - Use MCP Client to execute tools
4. **Enhance results** - Add context, calculate relevance, format response
5. **Manage sessions** - Track conversation history

**Workflow**:

```python
class EnhancedAIAgent:
    def __init__(self):
        self.mcp_client = MCPClient()          # Tool caller
        self.vector_store = ChromaDBClient()   # Semantic search
        self.session_contexts = {}             # Conversation tracking

    async def process_user_query(self, query, context, session_id):
        """
        Main entry point for user queries

        Flow:
        1. Analyze intent → What does user want?
        2. Get context → Semantic search for relevant docs
        3. Generate response → Call MCP tools
        4. Return enhanced response → Format and add insights
        """

        # Step 1: Intent Analysis
        intent = await self._analyze_intent_enhanced(query, session_id)
        # Returns: {type: "search", confidence: 0.95, tools: ["search_api_docs"]}

        # Step 2: Get Context
        relevant_docs = await self._get_relevant_context(query, intent)

        # Step 3: Generate Response
        response = await self._generate_enhanced_response(
            query, intent, relevant_docs, context, session_id
        )

        # Step 4: Return
        return {
            "query": query,
            "intent": intent,
            "response": response,
            "session_id": session_id
        }
```

**Intent Detection** (Rules-Based):
```python
async def _analyze_intent_enhanced(self, query, session_id):
    """
    Classify user intent using keyword matching

    Intent Types:
    - search: "find", "search", "list", "show"
    - endpoint_info: "tell me about", "what does", "explain"
    - analytics: "usage", "stats", "performance"
    - tutorial: "how to use", "example", "guide"
    """

    query_lower = query.lower()

    intent_patterns = {
        'search': {
            'keywords': ['search', 'find', 'list', 'show', 'display'],
            'confidence_base': 0.9
        },
        'endpoint_info': {
            'keywords': ['tell me about', 'what does', 'explain'],
            'confidence_base': 0.8
        }
    }

    # Find best match
    best_intent = None
    best_confidence = 0

    for intent_type, pattern in intent_patterns.items():
        keyword_matches = sum(
            1 for kw in pattern['keywords'] if kw in query_lower
        )
        if keyword_matches > 0:
            confidence = pattern['confidence_base'] + (keyword_matches * 0.05)
            if confidence > best_confidence:
                best_confidence = confidence
                best_intent = intent_type

    return {
        'type': best_intent or 'search',
        'confidence': best_confidence or 0.6,
        'tools': self._get_tools_for_intent(best_intent)
    }
```

**Tool Selection**:
```python
def _get_tools_for_intent(self, intent_type):
    """Map intent to MCP tools"""
    tool_mapping = {
        'search': ['search_api_docs'],
        'endpoint_info': ['get_api_endpoint', 'search_api_docs'],
        'analytics': ['analyze_api_usage'],
        'tutorial': ['search_api_docs', 'get_api_endpoint']
    }
    return tool_mapping.get(intent_type, ['search_api_docs'])
```

**Calling MCP Tools**:
```python
async def _handle_enhanced_search_query(self, query, context, session_id):
    """
    Handle search queries with smart enhancements

    Enhancements:
    1. Auto-detect provider names (jira → Atlassian ID 2)
    2. Clean query (remove "list", "apis", "show")
    3. Call MCP search tool
    4. Calculate relevance scores
    5. Add usage tips
    """

    # Auto-detect provider
    provider_map = {
        'atlassian': 2, 'jira': 2,
        'kubernetes': 3, 'k8s': 3,
        'datadog': 1
    }
    provider_ids = []
    for name, id in provider_map.items():
        if name in query.lower():
            provider_ids = [id]
            break

    # Clean query
    noise_words = ['list', 'show', 'apis', 'api', 'endpoints']
    cleaned_query = query.lower()
    for word in noise_words:
        cleaned_query = cleaned_query.replace(f' {word} ', ' ')

    # Call MCP tool
    search_results = await self.mcp_client.call_tool(
        "search_api_docs",
        {
            "query": cleaned_query.strip(),
            "provider_ids": provider_ids,
            "methods": [],
            "limit": 10
        }
    )

    # Enhance results
    enhanced_results = []
    for result in search_results.get('results', []):
        enhanced_result = result.copy()
        enhanced_result['search_relevance'] = self._calculate_relevance(
            query, result
        )
        enhanced_result['usage_tips'] = self._generate_usage_tips(result)
        enhanced_results.append(enhanced_result)

    return {
        "type": "enhanced_search_results",
        "results": enhanced_results,
        "total": len(enhanced_results),
        "query": query
    }
```

---

## Data Flow Example

### User Query: "list jira apis"

**Step 1: Frontend** (`ChatInterface.tsx`)
```typescript
// User types and hits enter
const response = await axios.post('http://localhost:8000/ai/query', {
  query: "list jira apis",
  context: {},
  session_id: null
});
```

**Step 2: Backend API** (`main.py`)
```python
@app.post("/ai/query")
async def ai_query(request: AIQueryRequest):
    response = await ai_agent_service.process_user_query(
        query="list jira apis",
        context={},
        session_id=None
    )
    return response
```

**Step 3: Enhanced AI Agent** (`enhanced_ai_agent.py`)
```python
async def process_user_query(query, context, session_id):
    # 3a. Analyze Intent
    intent = await self._analyze_intent_enhanced("list jira apis", session_id)
    # → {type: "search", confidence: 0.95, tools: ["search_api_docs"]}

    # 3b. Handle Search
    response = await self._handle_enhanced_search_query(
        "list jira apis", context, session_id
    )

    # Inside _handle_enhanced_search_query:

    # 3c. Detect Provider
    provider_ids = [2]  # "jira" detected → Atlassian ID 2

    # 3d. Clean Query
    cleaned_query = ""  # "list jira apis" → "" (all noise words)

    # 3e. Call MCP Client
    search_results = await self.mcp_client.call_tool(
        "search_api_docs",
        {
            "query": "",           # Empty = get all from provider
            "provider_ids": [2],   # Atlassian
            "methods": [],
            "limit": 10
        }
    )
```

**Step 4: MCP Client** (`client.py`)
```python
async def call_tool(tool_name, arguments):
    # 4a. Validate tool exists
    tool = self._find_tool("search_api_docs")  # ✓ Found

    # 4b. Validate arguments
    validation = self._validate_arguments(arguments, tool["inputSchema"])
    # ✓ Valid

    # 4c. Execute tool
    return await self._execute_search_tool(arguments)
```

**Step 5: Tool Execution** (`client.py`)
```python
async def _execute_search_tool(arguments):
    # 5a. Build database query
    db_query = db.query(APIDocumentation).join(APIProvider)

    # 5b. Apply provider filter
    db_query = db_query.filter(APIDocumentation.provider_id == 2)

    # 5c. No text search (query is empty)
    # This returns ALL Atlassian endpoints

    # 5d. Get results
    results = db_query.limit(10).all()
    # → 10 Atlassian endpoints

    # 5e. Format results
    formatted_results = [
        {
            "id": 1,
            "title": "Get announcement banner configuration",
            "description": "Returns the current announcement...",
            "provider": "Atlassian",
            "endpoint": "/rest/api/3/announcementBanner",
            "method": "GET"
        },
        # ... 9 more results
    ]

    return {"results": formatted_results, "total": 10}
```

**Step 6: Back to Enhanced AI Agent** (`enhanced_ai_agent.py`)
```python
# Enhance results with relevance scores
enhanced_results = []
for result in search_results['results']:
    enhanced_result = result.copy()
    enhanced_result['search_relevance'] = 0.85
    enhanced_result['usage_tips'] = [
        "This is a read-only endpoint, safe to call multiple times"
    ]
    enhanced_results.append(enhanced_result)

# Return response
return {
    "type": "enhanced_search_results",
    "results": enhanced_results,
    "total": 10,
    "query": "list jira apis",
    "filters_applied": {"provider_ids": [2], "methods": []}
}
```

**Step 7: Back to Frontend** (`ChatInterface.tsx`)
```typescript
// Response received
const aiResponse = response.data.response;

// Format for display
if (aiResponse.type === 'enhanced_search_results') {
  responseText = `I found ${aiResponse.results.length} relevant endpoint(s):\n\n`;
  aiResponse.results.forEach((result, index) => {
    responseText += `${index + 1}. **${result.title}**\n`;
    responseText += `   Method: ${result.method}\n`;
    responseText += `   Provider: ${result.provider}\n`;
    responseText += `   Endpoint: ${result.endpoint}\n\n`;
  });
}

// Display in chat
setMessages([...messages, {
  role: 'assistant',
  content: responseText  // String, not object!
}]);
```

---

## Why This Architecture?

### Benefits:

1. **Separation of Concerns**
   - Agent logic (intent detection) separate from tools (database queries)
   - Tools can be updated independently
   - Easy to add new tools without changing agent

2. **Reusability**
   - Same tools can be called from different agents
   - Same MCP client can be used by multiple services

3. **Testability**
   - Can test MCP tools independently
   - Can mock MCP client for agent testing
   - Can test intent detection separately

4. **Extensibility**
   - Add new tool: Define in MCP server + implement
   - Add new intent: Update intent patterns + add handler
   - Add new provider: Update provider map + sync data

5. **Standardization**
   - Uses official MCP protocol
   - Standard tool schema format
   - Standard validation

---

## Current Implementation Status

### ✅ Fully Working:
- **MCP Client**: Calls tools with validation
- **Tool: search_api_docs**: PostgreSQL search with filters
- **Enhanced AI Agent**: Intent detection + tool orchestration
- **Provider Detection**: Auto-detects Atlassian, K8s, Datadog
- **Query Cleaning**: Removes noise words
- **Result Enhancement**: Adds relevance scores, usage tips

### ⚠️ Partially Implemented:
- **MCP Server**: Defined but client calls local implementations
  - Currently: Client has duplicate tool implementations
  - Reason: Simpler for now, avoids IPC overhead
  - Future: Could connect to actual MCP server process

- **Vector Store**: ChromaDB initialized but not used
  - Currently: Using simple ILIKE text search
  - Future: Could add semantic vector search

### ❌ Not Implemented Yet:
- **Tool: get_api_endpoint** - Stubbed, needs implementation
- **Tool: analyze_api_usage** - Stubbed, needs usage tracking
- **Tool: suggest_api_improvements** - Stubbed, needs AI integration
- **OpenAI Integration** - No API key needed currently
- **True IPC Between Client/Server** - Currently in-process

---

## Database Schema

The MCP tools query these tables:

### `api_providers`
```sql
id | name       | display_name | is_active | base_url
---+------------+--------------+-----------+---------------------------
1  | datadog    | Datadog      | true      | https://api.datadoghq.com
2  | atlassian  | Atlassian    | true      | https://developer.atlassian.com
3  | kubernetes | Kubernetes   | true      | https://kubernetes.io
```

### `api_documentation`
```sql
id | provider_id | title                    | endpoint_path              | http_method | description
---+-------------+--------------------------+----------------------------+-------------+-------------
1  | 2           | Get announcement banner  | /rest/api/3/announcementBanner | GET     | Returns...
2  | 2           | Update announcement      | /rest/api/3/announcementBanner | PUT     | Updates...
...
598 Atlassian endpoints
1062 Kubernetes endpoints
```

### `search_queries` (for analytics)
```sql
id | query         | provider_id | results_count | created_at
---+---------------+-------------+---------------+------------
1  | create issue  | 2           | 10            | 2025-10-11
2  | list jira     | 2           | 10            | 2025-10-11
```

---

## Configuration

### Backend (`backend/app/main.py`)
```python
# Initialize AI agent with MCP client
ai_agent_service = EnhancedAIAgent()

@app.on_event("startup")
async def startup_event():
    await ai_agent_service.initialize()
    # → Connects MCP client
    # → Lists available tools
    # → Logs: "AI Agent initialized with 4 MCP tools"
```

### Environment Variables
```bash
# Database (used by MCP tools)
DATABASE_URL=postgresql://api_user:password@postgres:5432/api_docs_db

# OpenAI (optional, not currently used)
OPENAI_API_KEY=sk-...

# Redis (for caching, future)
REDIS_URL=redis://redis:6379

# Elasticsearch (for search, not currently used)
ELASTICSEARCH_URL=http://elasticsearch:9200
```

---

## Summary

**MCP in this project = Tool-based architecture that separates:**
- **What tools exist** (MCP Server definitions)
- **How to call tools** (MCP Client validation + execution)
- **When to use tools** (Enhanced AI Agent intent detection)

**Key Insight**: The MCP layer acts as a **standardized interface** between the AI agent's decision-making and the actual tool implementations (database queries, analytics, etc.). This makes the system modular, testable, and extensible.

**Current State**: Fully functional search system with 1,660 API endpoints searchable via natural language queries like "list jira apis", with automatic provider detection and query optimization.
