# MCP-Based API Documentation Aggregator

> **🚀 An Open-Source Project by Kamil DoXToR-G.**

A next-generation, AI-powered API documentation service built on the **Model Context Protocol (MCP)** that automatically fetches, maintains, and provides intelligent search and assistance for APIs from various providers such as Atlassian (Jira), Datadog, Kubernetes, and more.

**🌟 This is an open-source project - contributions are welcome!**

Project is not done Yet. Coding and developing still in progress!!

## 👨‍💻 Author

**Kamil DoXToR-G.** - Full-stack developer passionate about creating useful tools for the developer community.

- 🎯 **Project Lead** - Architecture, backend development, and system design
- 🔧 **Tech Stack** - FastAPI, PostgreSQL, Elasticsearch, Docker
- 🌐 **Open Source** - Committed to building and sharing quality software
- 📧 **Contact** - Open issues on GitHub for questions and contributions

## 🚀 Features

- 🤖 **MCP (Model Context Protocol) Integration** - Modern AI agent framework
- 🔍 **AI-Powered Semantic Search** - Vector-based search with ChromaDB
- 💬 **Intelligent Chat Interface** - Real-time AI assistance via WebSocket
- 🔄 **Automatic Documentation Fetching** - Scheduled updates from multiple providers
- 📱 **Modern Web Interface** - Responsive design with dark/light themes
- ⏰ **Scheduled Updates** - Keep documentation current with background tasks
- 🏷️ **Smart Categorization** - Automatic tagging and organization of API endpoints
- 📊 **Advanced Analytics** - AI-driven insights and usage patterns
- 🧠 **Context-Aware Responses** - Intelligent understanding of user intent

## 🏗️ Architecture

- **🤖 MCP Layer**: Model Context Protocol server with tool definitions
- **🧠 AI Agent**: Intelligent query processing and context management
- **🔍 Vector Store**: ChromaDB for semantic search and embeddings
- **⚡ Backend**: FastAPI with WebSocket support for real-time communication
- **🗄️ Database**: PostgreSQL with SQLAlchemy ORM for structured data
- **🔎 Search Engine**: Elasticsearch + ChromaDB for hybrid search
- **📊 Task Queue**: Celery with Redis for background processing
- **🐳 Containerization**: Docker & Docker Compose for easy deployment

## 🛠️ Tech Stack

### Backend
- **FastAPI** (Python 3.11+) - High-performance web framework with WebSocket support
- **MCP** (Model Context Protocol) - Modern AI agent framework
- **SQLAlchemy + Alembic** - Database ORM & migrations
- **PostgreSQL** - Reliable data storage
- **ChromaDB** - Vector database for semantic search
- **Elasticsearch** - Hybrid search engine
- **Celery + Redis** - Background task processing
- **Pydantic** - Data validation and serialization

### Frontend
- **Next.js 14** - React framework with App Router
- **React 18** - Modern React with hooks and server components
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide Icons** - Beautiful, customizable icons
- **Axios** - HTTP client for API requests

### DevOps & Infrastructure
- **Docker & Docker Compose** - Containerized development environment
- **Health Checks** - Service monitoring and dependency management
- **Environment Configuration** - Flexible configuration management

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Git

### Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone <your-github-repo-url>
   cd Latest_api_project
   ```

2. **Configure environment variables**:
   ```bash
   # Copy the example environment file
   cp .env.example backend/.env

   # Edit backend/.env and add your API keys (optional for basic functionality)
   # IMPORTANT: Change SECRET_KEY for production use!
   ```

3. **Start the development environment**:
   ```bash
   docker-compose up -d
   ```

4. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Admin Dashboard: http://localhost:3000/admin (default credentials: see Security section)
   - Health Check: http://localhost:8000/health

## 📁 Project Structure

```
Latest_api_project/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API route handlers
│   │   │   └── v1/         # API v1 endpoints (providers, search, AI settings)
│   │   ├── core/           # Core functionality & config
│   │   ├── db/             # Database models & setup
│   │   ├── fetchers/       # API documentation fetchers
│   │   ├── mcp/            # Model Context Protocol server
│   │   ├── services/       # Business logic (AI agent, OpenAI MCP client)
│   │   ├── vector_store/   # ChromaDB integration
│   │   └── main.py         # Main FastAPI application
│   ├── Dockerfile          # Backend container config
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js 14 frontend
│   ├── app/                # Next.js App Router pages
│   │   ├── admin/          # Admin login & dashboard
│   │   ├── page.tsx        # Main landing page
│   │   └── layout.tsx      # Root layout
│   ├── components/         # React components
│   │   ├── AIConfigPanel.tsx       # OpenAI settings panel
│   │   ├── ChatInterface.tsx       # AI chat interface
│   │   ├── GameOfLife.tsx         # Background animation
│   │   └── ThemeToggle.tsx        # Dark/light mode toggle
│   ├── Dockerfile          # Frontend container config
│   └── package.json        # Node.js dependencies
├── docker-compose.yml      # Development environment
├── .env.example           # Environment variables template
└── README.md              # This file
```

## 🔧 Configuration

The application uses environment variables for configuration. A template file `.env.example` is provided in the root directory.

### Environment Setup

1. **Copy the example file**:
   ```bash
   cp .env.example backend/.env
   ```

2. **Edit `backend/.env`** with your configuration:
   ```env
   # Database
   DATABASE_URL=postgresql://api_user:password@localhost:5432/api_docs_db

   # Security - CHANGE THESE IN PRODUCTION!
   SECRET_KEY=your-secret-key-here

   # AI API Keys (Optional - for AI-powered features)
   OPENAI_API_KEY=sk-your-openai-api-key-here
   ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here

   # API Provider Keys (Optional - for documentation fetching)
   ATLASSIAN_API_TOKEN=your-atlassian-token
   DATADOG_API_KEY=your-datadog-key
   DATADOG_APP_KEY=your-datadog-app-key
   ```

3. **See `.env.example`** for all available configuration options

## 📚 Supported API Providers

- **Atlassian (Jira Cloud)** - Issue tracking and project management
- **Datadog** - Monitoring and observability platform
- **Kubernetes** - Container orchestration platform
- **Prometheus** - Metrics monitoring system
- **Grafana** - Data visualization and alerting
- **Kibana** - Elasticsearch data visualization

## 🔍 API Endpoints

- `GET /` - Application information
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation (Swagger UI)

### API v1 Endpoints
- `GET /api/v1/providers` - Manage API providers
- `GET /api/v1/documentation` - Browse API documentation
- `POST /api/v1/search` - Search across documentation
- `GET /api/v1/analytics` - Usage analytics
- `POST /api/v1/agent` - AI agent interactions

## 🧪 Testing

Run the test suite:

```bash
cd backend
pytest
```

## 🔒 Security

### ⚠️ IMPORTANT: Production Security Checklist

Before deploying to production, **YOU MUST** change the following default credentials:

1. **Database Password** in `docker-compose.yml`:
   ```yaml
   POSTGRES_PASSWORD: password  # ⚠️ CHANGE THIS!
   ```

2. **Secret Keys** in `docker-compose.yml`:
   ```yaml
   SECRET_KEY: dev-secret-key-change-in-production  # ⚠️ CHANGE THIS!
   ```

3. **Database Connection String**:
   ```yaml
   DATABASE_URL: postgresql://api_user:password@...  # ⚠️ CHANGE PASSWORD!
   ```

### Default Development Credentials

The project includes default credentials for **LOCAL DEVELOPMENT ONLY**:
- PostgreSQL: `api_user` / `password`
- Secret Key: `dev-secret-key-change-in-production`

**⚠️ These are intentionally weak and MUST be changed for any production deployment!**

### API Keys Storage

- **Frontend**: OpenAI API keys entered in the admin dashboard are stored in browser localStorage only
- **Backend**: API keys should be set via environment variables in the `.env` file
- **Never commit**: `.env` files are gitignored and should never be committed to version control

### Recommended Production Setup

1. Use strong, randomly generated passwords (32+ characters)
2. Store secrets in a secure secret management system (e.g., AWS Secrets Manager, HashiCorp Vault)
3. Enable HTTPS/TLS for all connections
4. Use environment-specific configuration files
5. Implement proper access controls and firewall rules

## 📦 Deployment

### Production Deployment
1. **⚠️ CRITICAL**: Change all default passwords and secret keys (see Security section above)
2. Set up production environment variables in `backend/.env`
3. Configure production database and Redis with strong credentials
4. Set up Elasticsearch cluster
5. Enable HTTPS/TLS
6. Deploy using Docker or your preferred method

### Docker Deployment
```bash
# Ensure you've updated credentials first!
docker-compose -f docker-compose.prod.yml up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Kamil DoXToR-G.** - Project creator and lead developer
- FastAPI community for the excellent web framework
- Elasticsearch for powerful search capabilities
- Tailwind CSS for the beautiful design system
- All contributors and supporters

## 📖 Documentation

### Available Documentation
- **[README.md](README.md)** - This file, project overview and quick start
- **[AI_SYSTEM_STATUS.md](AI_SYSTEM_STATUS.md)** - Current AI system status and configuration
- **[MCP_OPENAI_IMPLEMENTATION_SUMMARY.md](MCP_OPENAI_IMPLEMENTATION_SUMMARY.md)** - Complete MCP + OpenAI integration guide
- **[CHAT_INTERFACE_IMPROVEMENTS.md](CHAT_INTERFACE_IMPROVEMENTS.md)** - Chat UI features and improvements

### Current System Status

**The system includes:**
- ✅ **True MCP Protocol** - Resources, Tools, and Prompts implementation
- ✅ **OpenAI Integration** - GPT-4o-mini for intelligent responses
- ✅ **Smart Chat Interface** - Session persistence, fixed positioning, real-time AI assistance
- ✅ **PostgreSQL Database** - 1,660+ API endpoints indexed (Atlassian, Kubernetes)
- ✅ **Admin Dashboard** - Configure OpenAI settings, sync providers, monitor status
- ✅ **Vector Search Ready** - ChromaDB for semantic search
- ✅ **Modern UI** - Next.js 14 with dark/light themes, Conway's Game of Life background

**To use AI features:**
1. Get an OpenAI API key from https://platform.openai.com/api-keys
2. Go to http://localhost:3000/admin/dashboard
3. Click "Settings" and enter your API key
4. Click "Validate" then "Save"
5. Start chatting with the AI assistant!

## 📞 Support

If you have any questions or need help:
- Open an issue on GitHub
- Check the documentation at `/docs`
- Review the health endpoint at `/health`
- Read the guides above for specific topics

---

**Made with ❤️ for the developer community** 
