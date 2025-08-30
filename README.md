# API Documentation Aggregator

A comprehensive web application that automatically fetches, maintains, and provides searchable documentation for APIs from various providers such as Atlassian (Jira), Datadog, Kubernetes, and more.

## 🚀 Features

- 🔄 **Automatic API Documentation Fetching** - Scheduled updates from multiple providers
- 🔍 **Intelligent Search** - Full-text search across all documentation with Elasticsearch
- 📱 **Modern Web Interface** - Responsive design with dark/light themes
- ⏰ **Scheduled Updates** - Keep documentation current with background tasks
- 🏷️ **Smart Categorization** - Automatic tagging and organization of API endpoints
- 📊 **Analytics & Insights** - Track usage patterns and popular searches
- 🤖 **AI Agent Integration** - Intelligent documentation suggestions and queries

## 🏗️ Architecture

- **Frontend**: Modern HTML/CSS/JS with Tailwind CSS
- **Backend**: FastAPI (Python) for high-performance REST API
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Search Engine**: Elasticsearch for intelligent search capabilities
- **Task Queue**: Celery with Redis for background job processing
- **Containerization**: Docker & Docker Compose for easy deployment

## 🛠️ Tech Stack

### Backend
- **FastAPI** (Python 3.11+) - High-performance web framework
- **SQLAlchemy + Alembic** - Database ORM & migrations
- **PostgreSQL** - Reliable data storage
- **Elasticsearch** - Advanced search engine
- **Celery + Redis** - Background task processing
- **Pydantic** - Data validation and serialization

### Frontend
- **HTML5 + CSS3** - Semantic markup and modern styling
- **Tailwind CSS** - Utility-first CSS framework
- **JavaScript (ES6+)** - Modern JavaScript features
- **Lucide Icons** - Beautiful, customizable icons

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

2. **Start the development environment**:
   ```bash
   docker-compose up -d
   ```

3. **Install backend dependencies** (for local development):
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Run database migrations**:
   ```bash
   cd backend
   alembic upgrade head
   ```

5. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## 📁 Project Structure

```
Latest_api_project/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API route handlers
│   │   ├── core/           # Core functionality & config
│   │   ├── db/             # Database models & setup
│   │   ├── fetchers/       # API documentation fetchers
│   │   ├── search/         # Search engine integration
│   │   ├── services/       # Business logic services
│   │   └── tasks/          # Background task definitions
│   ├── alembic/            # Database migrations
│   ├── scripts/            # Data import & utility scripts
│   └── requirements.txt    # Python dependencies
├── frontend-simple/         # HTML/CSS/JS frontend
├── docker-compose.yml      # Development environment
└── README.md               # This file
```

## 🔧 Configuration

The application uses environment variables for configuration. Create `.env` files in the backend directory with:

```env
# Database
DATABASE_URL=postgresql://api_user:password@localhost:5432/api_docs_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=api_docs

# Security
SECRET_KEY=your-secret-key-here

# API Provider Keys
ATLASSIAN_API_TOKEN=your-atlassian-token
DATADOG_API_KEY=your-datadog-key
DATADOG_APP_KEY=your-datadog-app-key
```

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

## 📦 Deployment

### Production Deployment
1. Set up production environment variables
2. Configure production database and Redis
3. Set up Elasticsearch cluster
4. Deploy using Docker or your preferred method

### Docker Deployment
```bash
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

- FastAPI community for the excellent web framework
- Elasticsearch for powerful search capabilities
- Tailwind CSS for the beautiful design system
- All contributors and supporters

## 📞 Support

If you have any questions or need help:
- Open an issue on GitHub
- Check the documentation at `/docs`
- Review the health endpoint at `/health`

---

**Made with ❤️ for the developer community** 