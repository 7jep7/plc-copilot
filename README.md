# PLC Copilot Backend

A FastAPI backend for automating PLC (Programmable Logic Controller) programming and testing.

## Vision

Create the copilot for Programmable Logic Controllers. Automate automating. Program, test, maintain, redeploy robots and any PLC-powered assembly line and industrial process.

## Features

### MVP Functionality
1. **PDF Document Parsing**: Upload industrial device manuals and extract critical information relevant for PLC code
2. **AI-Powered PLC Code Generation**: Convert user prompts and manual context into structured text (PLC code) using OpenAI models
3. **Digital Twin Testing**: Simple simulation functionality to test structured text (PLC code) for robustness

### Technical Features
- RESTful API endpoints with OpenAPI documentation
- Production-ready deployment on Render.com
- Structured logging and health monitoring
- Database migrations with Alembic
- Background task processing with Celery
- Comprehensive error handling and validation

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL
- Redis
- OpenAI API key

### Local Development with Docker

1. **Clone and setup environment**:
```bash
git clone <repository-url>
cd plc-copilot
cp .env.example .env
# Edit .env with your OpenAI API key and other settings
```

2. **Run with Docker Compose**:
```bash
docker-compose up --build
```

3. **Access the API**:
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Manual Local Setup

1. **Install dependencies**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your configuration:
# - DATABASE_URL (PostgreSQL connection string)
# - REDIS_URL
# - OPENAI_API_KEY
# - SECRET_KEY
```

3. **Initialize the database**:
```bash
# Run PostgreSQL and Redis locally, then:
alembic upgrade head
```

4. **Run the development server**:
```bash
python scripts/dev_server.py
# Or: uvicorn app.main:app --reload
```

5. **Run background worker (optional)**:
```bash
celery -A app.worker worker --loglevel=info
```

## API Endpoints

### Document Management
- `POST /api/v1/documents/upload` - Upload and parse PDF manuals
- `GET /api/v1/documents/` - List uploaded documents
- `GET /api/v1/documents/{id}` - Get specific document
- `POST /api/v1/documents/{id}/process` - Process document for PLC context
- `GET /api/v1/documents/{id}/extracted-data` - Get extracted technical data

### PLC Code Generation
- `POST /api/v1/plc/generate` - Generate PLC code from user prompt
- `GET /api/v1/plc/` - List generated PLC codes
- `GET /api/v1/plc/{id}` - Get specific PLC code
- `POST /api/v1/plc/{id}/validate` - Validate PLC code syntax
- `POST /api/v1/plc/{id}/compile` - Compile PLC code

### Digital Twin Testing
- `POST /api/v1/digital-twin/` - Create digital twin simulation
- `GET /api/v1/digital-twin/` - List digital twins
- `POST /api/v1/digital-twin/{id}/test` - Test PLC code in simulation
- `GET /api/v1/digital-twin/{id}/runs` - Get simulation test results

### System
- `GET /health` - Health check endpoint
- `GET /` - API information

## Production Deployment

### Render.com (Recommended)

1. **Fork this repository**

2. **Create services on Render.com**:
   - Connect your GitHub repository
   - Render will automatically detect the `render.yaml` configuration
   - Set required environment variables:
     - `OPENAI_API_KEY`
     - `SECRET_KEY`
     - Others are auto-configured via `render.yaml`

3. **Environment Variables**:
```bash
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_super_secret_key_here
SENTRY_DSN=your_sentry_dsn_here  # Optional
```

### Manual Deployment

1. **Build and deploy**:
```bash
# Build
pip install -r requirements.txt
alembic upgrade head

# Run production server
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

2. **Background worker**:
```bash
celery -A app.worker worker --loglevel=info
```

## Project Structure

```
plc-copilot/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── core/                   # Core configuration and utilities
│   │   ├── config.py          # Settings and configuration
│   │   ├── database.py        # Database connection and session
│   │   └── logging.py         # Structured logging setup
│   ├── api/                   # API endpoints
│   │   └── api_v1/           # API version 1
│   │       ├── api.py        # Main API router
│   │       └── endpoints/    # Individual endpoint modules
│   ├── models/               # SQLAlchemy database models
│   │   ├── document.py       # Document/manual models
│   │   ├── plc_code.py      # PLC code models
│   │   └── digital_twin.py  # Simulation models
│   ├── schemas/              # Pydantic request/response schemas
│   ├── services/             # Business logic services
│   │   ├── openai_service.py      # OpenAI API integration
│   │   ├── document_service.py    # Document processing
│   │   ├── plc_service.py         # PLC code management
│   │   └── digital_twin_service.py # Simulation logic
│   └── worker.py             # Celery worker configuration
├── alembic/                  # Database migrations
├── scripts/                  # Utility scripts
├── requirements.txt          # Python dependencies
├── render.yaml              # Render.com deployment config
├── docker-compose.yml       # Local Docker development
├── Dockerfile               # Container configuration
└── README.md               # This file
```

## Technology Stack

- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache/Queue**: Redis with Celery for background tasks
- **AI**: OpenAI GPT-4 for code generation and document analysis
- **PDF Processing**: PyPDF2, pdfplumber, PyMuPDF for text extraction
- **Validation**: Pydantic for request/response validation
- **Logging**: Structured logging with structlog
- **Monitoring**: Sentry for error tracking (optional)
- **Deployment**: Render.com with Gunicorn + Uvicorn workers

## Development

### Code Quality
```bash
# Format code
black app/
isort app/

# Lint
flake8 app/
mypy app/

# Test
pytest
```

### Database Management
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Monitoring
- Health endpoint: `/health`
- Logs: Structured JSON logs to stdout
- Metrics: Ready for Prometheus integration
- Errors: Sentry integration (configure `SENTRY_DSN`)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[License information here]

## Support

For questions and support, please [create an issue](link-to-issues) or contact [your-email].