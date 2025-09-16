# PLC Copilot Backend

> **A FastAPI backend for automating PLC (Programmable Logic Controller) programming and testing.**

🤖 **AI-Powered**: Converts natural language requirements into production-ready PLC code  
📋 **4-Stage Workflow**: Guided conversation from initial idea to refined implementation  
📄 **Document Intelligence**: Parses technical manuals to extract relevant device information  
🔧 **Code Library**: Industrial-grade ST code samples with intelligent search and management  
🚀 **Production Ready**: Deployed on Render.com with comprehensive monitoring and health checks

## Table of Contents

### Getting Started
- [Vision](#vision)
- [Features](#features)
- [Quick Start](#quick-start)

### API Documentation
- [API Reference](#api-reference)
- [User Workflow](#user-workflow)
- [Code Library (WIP)](#code-library-wip)

### Operations
- [Deployment](#deployment)
- [Development](#development)

### Integration
- [Frontend Integration](#frontend-integration)
- [Dependencies](#dependencies)

## Vision

Create the copilot for Programmable Logic Controllers. Automate automating. Program, test, maintain, redeploy robots and any PLC-powered assembly line and industrial process.

## Features

### Core Functionality ✅
1. **Multi-Stage Conversation System**: Guided 4-stage workflow from requirements to code refinement
2. **PDF Document Parsing**: Upload industrial device manuals and extract critical information relevant for PLC code
3. **AI-Powered PLC Code Generation**: Convert user prompts and manual context into structured text (PLC code) using OpenAI models
4. **Digital Twin Testing**: Simple simulation functionality to test structured text (PLC code) for robustness

### Work in Progress 🚧
5. **Code Library & Knowledge Base**: Industrial-grade ST code sample library with comprehensive API for uploading, searching, and managing user-contributed code. Includes semantic search capabilities and code similarity matching. Foundation for future RAG (Retrieval-Augmented Generation) integration.

### Technical Features
- **RESTful API**: Two-tier approach with conversation workflows and simple chat endpoints
- **Stage-Aware Prompts**: Specialized AI prompts for each conversation stage
- **Server-Side State Management**: Full conversation tracking and stage transitions
- **Production-ready deployment** on Render.com
- **Structured logging** and health monitoring
- **Database migrations** with Alembic
- **Background task processing** with Celery
- **Comprehensive error handling** and validation

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
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health
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

## API Reference

### Core Conversation API
- `POST /api/v1/conversations/` - Start new conversation (4-stage workflow)
- `PUT /api/v1/conversations/{id}` - Continue conversation with user message
- `GET /api/v1/conversations/{id}` - Get conversation state and history

### Simple Chat API
- `POST /api/v1/ai/chat` - Stateless chat interaction with AI

### Document Management
- `POST /api/v1/documents/upload` - Upload and parse PDF manuals
- `GET /api/v1/documents/` - List uploaded documents
- `GET /api/v1/documents/{id}` - Get specific document
- `POST /api/v1/documents/{id}/process` - Process document for PLC context
- `GET /api/v1/documents/{id}/extracted-data` - Get extracted technical data

### PLC Code Generation
- `POST /api/v1/plc-code/generate` - Generate PLC code from user prompt
- `GET /api/v1/plc-code/` - List generated PLC codes
- `GET /api/v1/plc-code/{id}` - Get specific PLC code
- `POST /api/v1/plc-code/{id}/validate` - Validate PLC code syntax
- `POST /api/v1/plc-code/{id}/compile` - Compile PLC code

### Digital Twin Testing
- `POST /api/v1/digital-twin/` - Create digital twin simulation
- `GET /api/v1/digital-twin/` - List digital twins
- `POST /api/v1/digital-twin/{id}/test` - Test PLC code in simulation
- `GET /api/v1/digital-twin/{id}/runs` - Get simulation test results

### Code Library (WIP) 🔧
*Work in Progress - Advanced ST code management and semantic search*

- `GET /api/v1/library/` - Library summary and statistics
- `GET /api/v1/library/structure` - Complete directory structure
- `POST /api/v1/library/search` - Search files by query and domain
- `GET /api/v1/library/browse/{domain}` - Browse files by domain
- `GET /api/v1/library/file/{domain}/{filename}` - Get file content
- `POST /api/v1/library/upload` - Upload ST files via JSON
- `POST /api/v1/library/upload-file` - Upload ST files via multipart
- `POST /api/v1/library/similar` - Find similar files
- `GET /api/v1/library/user-uploads` - List user contributions
- `DELETE /api/v1/library/user-uploads/{domain}/{filename}` - Delete files

### System
- `GET /health` - Health check endpoint
- `GET /` - API information

## User Workflow

The PLC Copilot follows a structured 4-stage conversation flow designed for efficiency and smooth user experience. Most time is spent in stages 2 and 4, while stages 1 and 3 are kept short to maintain momentum.

### Stage 1: Project Kickoff 🚀
**Purpose**: Capture the user's initial automation idea or problem statement.

**Duration**: Short (1-2 interactions)

**UI Requirements**:
- Simple, welcoming input field with placeholder: *"Describe what you want to automate..."*
- Examples: "Automate a conveyor belt sorting system", "Control a packaging line", "Monitor temperature in a furnace"
- **Primary API**: `POST /api/v1/conversations/` (start new conversation)
- **Alternative API**: `POST /api/v1/ai/chat` (simple stateless chat)
- Quick acknowledgment and immediate transition to Stage 2

**User Experience**:
- Single text input to get started quickly
- No complex forms or overwhelming questions
- AI acknowledges the request and moves to requirements gathering

### Stage 2: Gather Requirements 📋
**Purpose**: Interactive Q&A to gather all necessary technical requirements and context.

**Duration**: Medium (focused but thorough - aim for smooth progression)

**UI Requirements**:
- Conversational chat interface
- Progress indicator showing requirement completion
- **Force Transition Button**: "I'm ready to generate code" (user can skip remaining questions)
- **Document Upload**: Option to upload equipment manuals or specifications
- Smart question sequencing to avoid overwhelming the user
- **Primary API**: `POST /api/v1/conversations/` (continue conversation)
- **Stage Control**: `POST /api/v1/conversations/{id}/stage` (force transitions)
- **Document Upload**: `POST /api/v1/documents/upload` (optional manual uploads)

**AI Behavior**:
- Ask focused, relevant questions based on initial prompt
- **Single-Question Focus**: Each response contains exactly one focused question to prevent user overload
- **MCQ Support**: Provides structured multiple-choice questions for standardized options (safety features, voltages, protocols, etc.)
  - Structured API fields: `is_mcq`, `mcq_question`, `mcq_options`
  - Frontend should use ONLY MCQ fields for user interaction when `is_mcq` is true
  - Clean, focused UI without competing text or overwhelming choices
- Prioritize critical requirements first (safety, I/O, basic sequence)
- Adapt questioning based on user responses
- Provide option to proceed when minimum viable requirements are gathered

**Example Question Flow**:
- "What type of sensors will detect [specific items from initial prompt]?"
- "How many [input/output] points do you expect?"
- "Are there any safety requirements or emergency stops?"
- "What PLC platform are you using, or do you need recommendations?"

**Completion Criteria**:
- Minimum viable requirements captured, OR
- User manually forces transition to Stage 3

### Stage 3: Code Generation ⚡
**Purpose**: Generate initial PLC code based on gathered requirements.

**Duration**: Short (automated process with progress indication)

**UI Requirements**:
- Loading animation with progress indicators
- Status messages: "Analyzing requirements...", "Generating ladder logic...", "Optimizing code..."
- **API Endpoint**: `POST /api/v1/plc-code/generate`
- Automatic transition to Stage 4 upon completion

**Generated Outputs**:
- Complete PLC program (ladder logic, structured text, etc.)
- I/O configuration tables
- Basic documentation and comments
- Initial code structure ready for testing

### Stage 4: Refinement & Testing 🔧
**Purpose**: Test code robustness and refine through chat interaction or manual edits.

**Duration**: Extended (most time spent here - iterative improvement)

**UI Requirements**:
- **Split View**: Code editor + chat interface
- **Manual Editing**: Full code editing capabilities with syntax highlighting
- **Chat Refinement**: Continue conversation to request modifications
- **Testing Integration**: 
  - Digital twin simulation controls
  - Validation and error checking
  - Test scenario runners
- **Export Options**: Download final code in various formats
- **API Endpoints**:
  - `POST /api/v1/conversations/` (primary refinement discussions)
  - `POST /api/v1/ai/chat` (alternative simple chat)
  - `POST /api/v1/plc-code/{id}/validate` (code validation)
  - `POST /api/v1/digital-twin/{id}/test` (simulation testing)
  - Manual code updates via editor

**Refinement Options**:
1. **Chat-based**: "Add a safety timeout for conveyor motor", "Optimize the sorting logic"
2. **Manual editing**: Direct code modifications with real-time validation
3. **Testing feedback**: Run simulations and iterate based on results

**Testing Features**:
- Digital twin simulation with visual feedback
- Automated robustness testing
- Edge case scenario validation
- Performance optimization suggestions

### Conversation Management

PLC Copilot provides two API approaches for different use cases:

#### Primary API: Multi-Stage Conversation System
**Recommended for production frontends**

Use `POST /api/v1/conversations/` for the full stage-aware workflow:

```typescript
// Start new conversation
const response = await fetch('/api/v1/conversations/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: "I need to control a conveyor belt system with safety stops"
  })
});

const conversation = await response.json();
// Returns: { conversation_id, stage, response, suggested_actions, stage_progress }
```

**Stage Management**:
- Server tracks conversation state and current stage
- Automatic stage detection based on conversation context
- Manual stage control via `POST /api/v1/conversations/{id}/stage`
- Stage-specific prompts automatically selected
- Full conversation history and state persistence

**Stage Transitions**:
- **1→2**: Automatic when initial requirements need clarification
- **2→3**: Automatic when requirements are sufficient, or user forces via "Generate Code"
- **3→4**: Automatic after code generation
- **4→2**: Manual via "Refine Requirements" or stage transition API

**Frontend Integration**:
```typescript
// Continue conversation with stage awareness
const response = await fetch('/api/v1/conversations/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    conversation_id: "existing-conversation-id",
    message: "Add emergency stop functionality"
  })
});

// Get stage suggestions and progress
const suggestions = await fetch(`/api/v1/conversations/${conversationId}/stage/suggestions`);
```

#### Alternative API: Simple Chat
**For ad-hoc queries or testing**

Use `POST /api/v1/ai/chat` for simple, stateless interactions:

```typescript
const response = await fetch('/api/v1/ai/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_prompt: "Explain PLC ladder logic basics",
    model: "gpt-4o-mini",
    temperature: 0.7
  })
});
```

**When to use each API**:
- **Conversations API**: Multi-stage PLC development workflows, state tracking, iterative refinement
- **Chat API**: Quick questions, documentation, general PLC knowledge queries

**State Management**:
- Conversation state managed server-side
- Full message history and stage context preserved
- Requirements, generated code, and refinements tracked
- Export and version control throughout the workflow

## Deployment

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
- **AI**: OpenAI GPT-4o for document analysis, GPT-4o-mini for conversations
- **PDF Processing**: PyPDF2, pdfplumber, PyMuPDF for text extraction
- **Validation**: Pydantic for request/response validation
- **Logging**: Structured logging with structlog
- **Monitoring**: Sentry for error tracking (optional)
- **Deployment**: Render.com with Gunicorn + Uvicorn workers

## Document Processing Pipeline

### Multi-Method PDF Text Extraction

The system uses **3 complementary extraction libraries** with intelligent fallback:

| Method | Advantages | Best For |
|--------|-----------|-----------|
| **pdfplumber** | Excellent table extraction, preserves positioning | Technical datasheets, specifications |
| **PyMuPDF (fitz)** | Fast processing, good with graphics/images | Mixed content documents |
| **PyPDF2** | Lightweight, wide compatibility | Simple text documents, fallback |

### Smart Processing Strategy

```python
# Page-level deduplication prevents redundant processing
page_texts = {}  # Track successfully extracted pages
for page_num in range(doc.page_count):
    if page_num in page_texts:
        continue  # Skip already extracted pages
```

**Process Flow:**
1. **pdfplumber** processes all pages first
2. **PyMuPDF** handles failed pages
3. **PyPDF2** processes remaining failures
4. **Assemble in page order** for final output

### LLM-Based Content Analysis

**Single-pass processing** using **GPT-4o**:
- **Temperature 0.3** for consistent technical analysis
- **8KB content limit** per document for cost efficiency
- **Structured extraction** of PLC-relevant specifications

**Extracted Information:**
- I/O specifications (digital/analog inputs/outputs)
- Control logic requirements and safety systems
- Operating parameters and communication protocols
- Timing requirements and performance criteria

### Future Enhancements

**Planned Improvements:**
- **OCR integration** for scanned PDFs and image-based content
- **Smart context re-injection** when initial analysis seems incomplete
- **Chunked analysis** for large documents with section-wise processing
- **Image/diagram extraction** using GPT-4o-Vision for circuit diagrams
- **Multi-language support** for German/Japanese technical documentation

## Code Library (WIP) 🔧

The Code Library feature provides a comprehensive system for managing industrial-grade ST (Structured Text) code samples, enabling code reuse, discovery, and intelligent retrieval.

### Current Implementation

**ST Code Sample Library**: Industrial-grade examples covering:
- **Conveyor Systems**: Belt control with safety features and E-stop handling
- **Safety Systems**: SIL2 safety controllers with dual-channel monitoring  
- **Process Control**: Advanced PID controllers with auto-tuning and anti-windup
- **Motor Control**: VFD motor control systems with protection and energy optimization

**Complete REST API** for code management:
- Browse and search the code library by domain and keywords
- Upload user-contributed ST files with metadata and categorization
- Find similar code patterns and get intelligent recommendations
- Manage user uploads with full CRUD operations

**File Organization**:
```
st_code_library/           # Core library (read-only examples)
├── conveyor_systems/
├── safety_systems/
├── process_control/
└── motor_control/

user_uploads/st_code/      # User contributions (writable)
├── user_domain_1/
└── user_domain_2/
```

### Usage Examples

**Browse the library**:
```bash
GET /api/v1/library/                    # Get summary and statistics
GET /api/v1/library/browse/motor_control # Browse specific domain
GET /api/v1/library/file/safety_systems/safety_controller_sil2.st
```

**Search for code**:
```bash
POST /api/v1/library/search
{
  "query": "motor protection overload",
  "domain": "motor_control",
  "limit": 5
}
```

**Upload custom code**:
```bash
POST /api/v1/library/upload
{
  "filename": "my_custom_controller.st",
  "content": "PROGRAM MyController...",
  "domain": "process_control",
  "description": "Custom temperature controller",
  "author": "John Engineer",
  "tags": ["temperature", "pid", "custom"]
}
```

### Future Roadmap (RAG Integration)

**Planned Features**:
- **Vector Embeddings**: Use OpenAI embeddings for semantic code search
- **LangChain Integration**: RAG (Retrieval-Augmented Generation) for intelligent code suggestions
- **Context-Aware Generation**: Enhance PLC code generation with relevant library examples
- **Automatic Code Categorization**: AI-powered tagging and domain classification
- **Code Quality Scoring**: Automated analysis of uploaded code for best practices

**Integration Points**:
- **Conversation Orchestrator**: Inject relevant code examples during multi-stage conversations
- **PLC Code Generation**: Use library patterns to improve generated code quality
- **Smart Recommendations**: Suggest similar implementations based on user requirements

### Testing

#### Cost-Efficient Testing 🪙
For frequent testing without high OpenAI costs:
```bash
# Use efficient test suite (80% cost reduction)
TESTING=true python scripts/test_4_stage_system_efficient.py

# Test MCQ functionality
TESTING=true python scripts/test_mcq.py
```

#### Comprehensive Testing
For full coverage (higher cost):
```bash
# Full test suite
python scripts/test_4_stage_system.py

# Test all endpoints
python scripts/test_all_endpoints.py
```

Run the Code Library API test suite:
```bash
python scripts/test_code_library_api.py
```

> 💡 **Cost Tip**: Set `TESTING=true` to use gpt-4o-mini with reduced token limits. See [COST_OPTIMIZATION.md](COST_OPTIMIZATION.md) for details.

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

For questions and support, please [create an issue](link-to-issues) or contact Jonas Petersen.

## OpenAI parameters: max_tokens vs max_completion_tokens

Note from OpenAI (paraphrased):

"Hi, Atty from OpenAI here — max_tokens continues to be supported in all existing models, but the o1 series only supports max_completion_tokens. We are doing this because max_tokens previously meant both the number of tokens we generated (and billed you for) and the number of tokens you got back in."

What this project does:

- We accept the legacy field `max_tokens` in API requests for backward compatibility.
- We also accept the newer `max_completion_tokens` field. When both are present the server prefers `max_completion_tokens`.
- When calling OpenAI, the server sends `max_completion_tokens` to the API (mapped from your request). This prevents errors with newer models that don't accept `max_tokens`.

How to test the OpenAI call (prompt -> response):

1. Ensure your key is in `.env` or exported in the environment as `OPENAI_API_KEY`.

2. Start your environment:
```bash
conda activate plc-copilot
PYTHONPATH=$(pwd) python scripts/live_openai_smoke.py
```

3. The script will send a simple prompt and print the response content and usage information. It demonstrates the request (prompt) and response (content + usage).

4. To test via the API endpoint (Swagger or curl):

Using Swagger: visit `http://localhost:8000/docs`, open `POST /api/v1/ai/chat`, and try a payload like:

```json
{
  "user_prompt": "Explain emergency stop logic for a conveyor",
  "model": "gpt-4o-mini",
  "temperature": 1.0,
  "max_tokens": 128
}
```

Using curl:
```bash
curl -X POST "http://localhost:8000/api/v1/ai/chat" -H "Content-Type: application/json" -d '{"user_prompt":"Say hi","model":"gpt-4o-mini","max_tokens":64}'
```

5. If the target model rejects a parameter (for example, if you accidentally pass `max_tokens` to an o1-series model), the API will return HTTP 400 with a JSON detail indicating the offending parameter and an explanation. Example response:

```json
HTTP/1.1 400 Bad Request
{
  "detail": {"error":"invalid_request","param":"max_tokens","message":"Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead."}
}
```

This project maps and surfaces those errors so callers can correct their requests.

## Using the API from a Frontend (Quick)

Yes — you can call the backend API from a frontend application. Basic flow:

1. Ensure the backend is running and accessible (CORS may need configuring for your frontend origin).
2. Protect the OpenAI API key on the server side — never expose it in the frontend. The frontend should call your backend endpoints which perform OpenAI calls.

Example fetch from a browser-based frontend (React / plain JS):

```javascript
// Example: call the AI chat endpoint
async function sendPrompt(prompt) {
  const resp = await fetch("https://your-backend.example.com/api/v1/ai/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_prompt: prompt, model: "gpt-4o-mini" })
  });

  if (!resp.ok) throw new Error(`API error: ${resp.status}`);
  return resp.json();
}

// Usage
sendPrompt("Explain emergency stop logic for a conveyor").then(console.log).catch(console.error);
```

If you run the frontend locally during development, enable CORS for your dev origin in `app/core/config.py` BACKEND_CORS_ORIGINS or configure your deployment accordingly.

## API Usage (detailed)

This section documents how to interact with the backend API in a practical way: headers, authentication recommendations, request/response shapes, file uploads, error handling, and examples in curl/JavaScript/Python.

Base URL and common headers
- Base URL (local dev): http://localhost:8000
- Versioned API prefix used in examples: /api/v1
- Common headers:
  - Content-Type: application/json (for JSON requests)
  - For file uploads use multipart/form-data with the file field named `file`.

Authentication
- This project does not enforce an application-level auth scheme by default. In production you should add authentication (JWT or API keys). Keep your OpenAI API key only on the server (in `.env` or platform secrets). Do NOT expose it to clients.

Error format
- OpenAI parameter/value errors are returned as HTTP 400 with a structured detail object:

```json
HTTP/1.1 400 Bad Request
{
  "detail": {"error":"invalid_request","param":"max_tokens","message":"Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead."}
}
```

- Other server errors use standard FastAPI responses (500 with string detail) unless otherwise handled by an endpoint.

OpenAI parameter handling (max_tokens vs max_completion_tokens)
- This backend accepts both `max_tokens` (legacy) and `max_completion_tokens` (preferred). If both are provided, `max_completion_tokens` takes precedence.
- The server maps the request to `max_completion_tokens` when calling the OpenAI client so newer models that reject `max_tokens` work without breaking older callers.

Endpoints (detailed)

1) AI Chat
- POST /api/v1/ai/chat
- Description: Send a free-form prompt to a supported LLM and return a text response and usage information.
- Request JSON fields:
  - user_prompt: string (required)
  - model: string (optional, default gpt-4o-mini)
  - temperature: number (0.0 - 2.0) — some models only support default values; parameter errors will be returned as 400.
  - max_tokens (legacy): integer — legacy alias for `max_completion_tokens`
  - max_completion_tokens: integer — preferred field for completion limits

- Example request:
```json
{
  "user_prompt": "Explain emergency stop logic for a conveyor",
  "model": "gpt-4o-mini",
  "temperature": 1.0,
  "max_completion_tokens": 128
}
```
- Example response:
```json
{
  "model": "gpt-4o-mini",
  "content": "...generated text...",
  "usage": {"prompt_tokens": 10, "completion_tokens": 64, "total_tokens": 74}
}
```

2) PLC code generation
- POST /api/v1/plc/generate
- Description: Generate PLC code from a user prompt and optional document context.
- Request shape (`PLCGenerationRequest`) includes:
  - user_prompt: string (required)
  - language: enum (e.g., structured_text)
  - document_id (optional): applies document context
  - temperature, max_tokens / max_completion_tokens as above
  - include_io_definitions: bool
  - include_safety_checks: bool

- Response shape: `PLCCodeResponse` which includes `source_code`, `generation_parameters`, and `generation_metadata` (model, temperature, token limits and usage).

3) Document management
- POST /api/v1/documents/upload
  - Upload a PDF via multipart/form-data with form field `file`.
  - Example curl:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/documents/upload" -F "file=@/path/to/manual.pdf"
    ```
  - Response: created document metadata (id, filename, file_path, etc.).

- POST /api/v1/documents/{id}/process
  - Triggers document analysis using the OpenAI service. Any OpenAI parameter errors during analysis will be surfaced as 400 responses.

4) Digital twin and other endpoints
- See the endpoint list above; request/response shapes follow the models and schemas in `app/schemas/`.

Examples

Curl (AI chat):
```bash
curl -s -X POST "http://localhost:8000/api/v1/ai/chat" \
  -H "Content-Type: application/json" \
  -d '{"user_prompt":"Say hi","model":"gpt-4o-mini","max_tokens":64}'
```

JavaScript (browser / frontend example):
```javascript
async function sendPrompt(prompt) {
  const resp = await fetch('/api/v1/ai/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_prompt: prompt, max_tokens: 64 })
  });
  if (!resp.ok) throw new Error('API error ' + resp.status);
  return resp.json();
}

sendPrompt('Explain emergency stop logic for a conveyor').then(console.log).catch(console.error);
```

Python (requests):
```python
import requests

resp = requests.post('http://localhost:8000/api/v1/ai/chat', json={
    'user_prompt': 'Say hi',
    'max_tokens': 64
})
resp.raise_for_status()
data = resp.json()
print('Model:', data['model'])
print('Response:', data['content'])
print('Usage:', data.get('usage'))
```

Testing prompt -> response (how to observe prompt then response)
- Quick live test (script included):
  1. Ensure `.env` contains `OPENAI_API_KEY` or export it in your shell.
  2. Activate conda env and run:
     ```bash
     conda activate plc-copilot
     PYTHONPATH=$(pwd) python scripts/live_openai_smoke.py
     ```
  3. The script will call the `chat_completion` service and print the response content and usage object.

- Using Swagger UI: run the app and open http://localhost:8000/docs → find `POST /api/v1/ai/chat` → paste a request and execute. The UI shows request and response detail.

Integration and automated testing
- Unit tests and integration tests are in `tests/`. The repository includes `tests/test_integration_openai_param_error.py` which simulates OpenAI returning an unsupported parameter error and asserts the endpoint returns HTTP 400 with a structured error detail.

Tips and notes
- If a model reports unsupported parameters or values, the API will return a 400 with `detail` describing the `param` and `message`. This lets clients correct the request without guessing what went wrong.
- Keep model-specific behavior in mind: some models restrict temperature or token limits. Prefer explicit `max_completion_tokens` if targeting the o1 series.


## API Documentation (Detailed)

This project exposes a versioned REST API with OpenAPI documentation automatically generated by FastAPI. When running locally or deployed, visit:

- Interactive Swagger UI: `GET /docs`
- ReDoc (alternative UI): `GET /redoc`

Below is a concise list of endpoints with request/response shapes and examples.

### 🚀 Primary API: Multi-Stage Conversations
**Recommended for production frontend integration**

#### Start/Continue Conversation
```http
POST /api/v1/conversations/
Content-Type: application/json

{
  "conversation_id": "optional-existing-id",
  "message": "I need to control a conveyor belt with emergency stops",
  "force_stage": "project_kickoff" // optional override
}
```

**Response:**
```json
{
  "conversation_id": "uuid-string",
  "stage": "project_kickoff",
  "response": "I'll help you design a conveyor belt control system...",
  "next_stage": "gather_requirements",
  "stage_progress": { "requirements_identified": 2, "confidence": 0.7 },
  "suggested_actions": [
    "Provide conveyor speed requirements",
    "Specify safety sensor types"
  ],
  "is_mcq": false,
  "mcq_question": null,
  "mcq_options": []
}
```

**MCQ Response Example (gather_requirements stage):**
```json
{
  "conversation_id": "uuid-string",
  "stage": "gather_requirements",
  "response": "Based on your conveyor system requirements, I need to understand your safety priorities...",
  "next_stage": "gather_requirements",
  "suggested_actions": ["Select your required safety features"],
  "is_mcq": true,
  "mcq_question": "What safety features do you require for your conveyor system?",
  "mcq_options": [
    "Emergency stop buttons only",
    "Light curtains for perimeter protection",
    "Safety mats for operator zones",
    "Comprehensive safety package (all features)"
  ]
}
```

**Critical Frontend MCQ Handling:**
- When `is_mcq` is true, display ONLY `mcq_question` and `mcq_options` to user
- Avoid displaying full `response` text alongside MCQ to prevent cognitive overload
- Provide clean, focused interface for user selection
```

#### Get Conversation State
```http
GET /api/v1/conversations/{conversation_id}
```

#### Manual Stage Transitions
```http
POST /api/v1/conversations/{conversation_id}/stage
Content-Type: application/json

{
  "target_stage": "code_generation",
  "force": true
}
```

#### Stage Suggestions & Progress
```http
GET /api/v1/conversations/{conversation_id}/stage/suggestions
```

**Returns:** Valid transitions, suggested next stage, progress metrics

### 🔧 Alternative API: Simple Chat
**For ad-hoc queries and testing**

#### Simple AI Chat
```http
POST /api/v1/ai/chat
Content-Type: application/json

{
  "user_prompt": "Explain PLC ladder logic basics",
  "model": "gpt-4o-mini",
  "temperature": 0.7,
  "max_completion_tokens": 512
}
```

**Response:**
```json
{
  "model": "gpt-4o-mini",
  "content": "PLC ladder logic is a programming language...",
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 128,
    "total_tokens": 143
  }
}
```

## Frontend Integration

For comprehensive frontend integration details, including MCQ handling, stage management, and best practices, see the **[Frontend Integration Guide](./FRONTEND_INTEGRATION_GUIDE.md)**.

### Quick Integration Summary

### 📋 Frontend Integration Guide

#### Recommended Workflow for React/Vue/Angular

```typescript
// 1. Initialize conversation state
interface ConversationState {
  conversationId: string | null;
  currentStage: string;
  messages: Array<{role: string, content: string, timestamp: string}>;
  suggestedActions: string[];
  stageProgress: Record<string, any>;
}

// 2. Start conversation
async function startConversation(initialMessage: string): Promise<ConversationState> {
  const response = await fetch('/api/v1/conversations/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: initialMessage })
  });
  
  const data = await response.json();
  return {
    conversationId: data.conversation_id,
    currentStage: data.stage,
    messages: [
      { role: 'user', content: initialMessage, timestamp: new Date().toISOString() },
      { role: 'assistant', content: data.response, timestamp: new Date().toISOString() }
    ],
    suggestedActions: data.suggested_actions || [],
    stageProgress: data.stage_progress || {}
  };
}

// 3. Continue conversation
async function continueConversation(
  conversationId: string, 
  message: string,
  forceStage?: string
): Promise<ConversationState> {
  const response = await fetch('/api/v1/conversations/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      conversation_id: conversationId,
      message,
      force_stage: forceStage
    })
  });
  
  const data = await response.json();
  // Update your state accordingly
  return data;
}

// 4. Force stage transition (optional)
async function transitionStage(conversationId: string, targetStage: string) {
  await fetch(`/api/v1/conversations/${conversationId}/stage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target_stage: targetStage })
  });
}
```

#### Stage-Specific UI Components

```typescript
// Stage indicators
const StageIndicator = ({ currentStage }: { currentStage: string }) => {
  const stages = [
    { key: 'project_kickoff', label: 'Project Kickoff', icon: '�' },
    { key: 'gather_requirements', label: 'Gather Requirements', icon: '📝' },
    { key: 'code_generation', label: 'Code Generation', icon: '⚙️' },
    { key: 'refinement_testing', label: 'Refinement & Testing', icon: '🔧' }
  ];
  
  return (
    <div className="stage-indicator">
      {stages.map((stage, index) => (
        <div 
          key={stage.key}
          className={`stage ${currentStage === stage.key ? 'active' : ''}`}
        >
          {stage.icon} {stage.label}
        </div>
      ))}
    </div>
  );
};

// Suggested actions
const SuggestedActions = ({ actions, onAction }: { 
  actions: string[], 
  onAction: (action: string) => void 
}) => (
  <div className="suggested-actions">
    <h4>Suggested Next Steps:</h4>
    {actions.map((action, index) => (
      <button 
        key={index}
        onClick={() => onAction(action)}
        className="action-button"
      >
        {action}
      </button>
    ))}
  </div>
);
```

#### Error Handling

```typescript
// Robust error handling
async function apiCall(url: string, options: RequestInit) {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      
      if (response.status === 400 && errorData.detail) {
        // Handle structured API errors (e.g., OpenAI parameter errors)
        throw new Error(`API Error: ${errorData.detail.message || errorData.detail}`);
      }
      
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API call failed:', error);
    throw error;
  }
}
```
```
    ```json
    {
      "model": "gpt-4o-mini",
      "content": "string",
      "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
    }
    ```

### Document Management
- POST /api/v1/documents/upload
  - Upload a PDF file (multipart/form-data) with key `file`. Returns created `Document` metadata.
- GET /api/v1/documents/
  - List documents. Query params: `skip`, `limit`.
- POST /api/v1/documents/{id}/process
  - Process the uploaded document to extract PLC-relevant context.

### PLC Code Generation
- POST /api/v1/plc/generate
  - Request JSON (PLCGenerationRequest): includes `user_prompt`, `language` (e.g., `structured_text`), `max_tokens`, `temperature`, and flags like `include_io_definitions`.
  - Response JSON: `PLCCodeResponse` — contains `source_code`, `id`, `language`, `generated_at`, and metadata.

### Digital Twin
- POST /api/v1/digital-twin/
  - Create a digital twin simulation record; accept PLC code id and parameters.
- POST /api/v1/digital-twin/{id}/test
  - Run a simulation test. Returns run results and logs.

### System
- GET /health — useful for readiness/liveness checks by load balancers.

Notes on authentication and security:
- The backend currently expects trusted clients or deployment-level protection. Add an API authentication layer (JWT or API keys) for production.
- Do not store secrets in client-side code or public repositories. Use `.env` or platform secrets (Render, Docker secrets, etc.).

## SDK Generation

FastAPI automatically generates an OpenAPI JSON at `/openapi.json`. Use it to generate client SDKs for any language:

**Python Client:**
```bash
pip install openapi-python-client
openapi-python-client generate --url http://localhost:8000/openapi.json
```

**TypeScript Client:**
```bash
openapi-generator-cli generate -i http://localhost:8000/openapi.json -g typescript-fetch -o ./frontend-client
```

## Next Steps

This backend provides a complete foundation for PLC automation workflows:

- ✅ **Multi-stage conversation system** for guided PLC development
- ✅ **Stage-aware AI prompts** for technical accuracy
- ✅ **Flexible API design** supporting both workflows and ad-hoc queries
- ✅ **Production-ready deployment** with comprehensive error handling
- ✅ **Frontend integration examples** with TypeScript patterns

**For Production:**
1. **Deploy to Render.com** using included `render.yaml` configuration
2. **Add Supabase persistence** for conversation state (beyond MVP)
3. **Implement authentication** (JWT/API keys) for security
4. **Scale workers** based on usage patterns

**For Development:**
1. **Follow frontend integration guide** in the API documentation section
2. **Use conversation endpoints** for full workflow features
3. **Test with provided examples** and Swagger UI at `/docs`
4. **Extend prompt templates** for domain-specific requirements

## Future Optimizations

### 💰 OpenAI API Cost Reduction

The current implementation sends full conversation context with every API call, which provides excellent context awareness but can be expensive at scale. Future optimizations include:

**📉 Token Usage Reduction:**
- **Truncate History**: Send only recent or relevant messages to reduce token usage
- **Summarize Context**: Use API to summarize past conversation, replacing long history with a concise summary
- **Use System Messages**: Define chatbot role in system message to avoid repeating in every request
- **Monitor Tokens**: Track usage with tools like `tiktoken` and optimize input to stay cost-efficient

**🎯 Smart Context Management:**
- **Stage-Specific Context**: Only send relevant context for current conversation stage
- **Document Context Caching**: Cache processed document summaries to avoid reprocessing
- **Incremental Updates**: Track context changes and send only deltas when possible
- **Context Compression**: Compress older conversation turns into concise summaries

**💡 Implementation Priority:**
1. **Message Window Reduction** (easy win: 60-80% token reduction)
2. **Stage-Specific Context Filtering** (medium complexity, high impact)
3. **OpenAI Assistants API Integration** (complex but enables persistent conversation threads)

Current cost: ~1,000-6,000 tokens per interaction. Target: ~300-1,500 tokens per interaction.

## Dependencies

### Technology Stack

**Core Framework**: FastAPI with Uvicorn/Gunicorn deployment  
**Database**: PostgreSQL with SQLAlchemy ORM and Alembic migrations  
**AI Integration**: OpenAI GPT models for conversation and code generation  
**Document Processing**: pdfplumber, PyMuPDF, PyPDF2 for PDF parsing  
**Background Tasks**: Celery with Redis for async processing  
**Deployment**: Render.com with Docker containerization  

**LangChain**: Currently included in dependencies for future RAG (Retrieval-Augmented Generation) integration with the Code Library feature. Not actively used in MVP but retained for planned semantic search and intelligent code retrieval capabilities.