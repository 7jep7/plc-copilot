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

### System
- `GET /health` - Health check endpoint
- `GET /` - API information

## 4-Stage User Flow

The PLC Copilot follows a structured 4-stage conversation flow designed for efficiency and smooth user experience. Most time is spent in stages 2 and 4, while stages 1 and 3 are kept short to maintain momentum.

### Stage 1: Initial User Prompt 🚀
**Purpose**: Capture the user's initial automation idea or problem statement.

**Duration**: Short (1-2 interactions)

**UI Requirements**:
- Simple, welcoming input field with placeholder: *"Describe what you want to automate..."*
- Examples: "Automate a conveyor belt sorting system", "Control a packaging line", "Monitor temperature in a furnace"
- **API Endpoint**: `POST /api/v1/ai/chat`
- Quick acknowledgment and immediate transition to Stage 2

**User Experience**:
- Single text input to get started quickly
- No complex forms or overwhelming questions
- AI acknowledges the request and moves to requirements gathering

### Stage 2: Requirement Definition 📋
**Purpose**: Interactive Q&A to gather all necessary technical requirements and context.

**Duration**: Medium (focused but thorough - aim for smooth progression)

**UI Requirements**:
- Conversational chat interface
- Progress indicator showing requirement completion
- **Force Transition Button**: "I'm ready to generate code" (user can skip remaining questions)
- **Document Upload**: Option to upload equipment manuals or specifications
- Smart question sequencing to avoid overwhelming the user
- **API Endpoints**: 
  - `POST /api/v1/ai/chat` (interactive Q&A)
  - `POST /api/v1/documents/upload` (optional manual uploads)

**AI Behavior**:
- Ask focused, relevant questions based on initial prompt
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

### Stage 3: PLC Code Generation ⚡
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

### Stage 4: Testing and Refinement �
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
  - `POST /api/v1/ai/chat` (refinement discussions)
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

**Stage Transitions**:
- **1→2**: Automatic after initial prompt
- **2→3**: User-controlled ("Generate Code" button) or automatic when requirements complete
- **3→4**: Automatic after code generation
- **4→2**: Option to "Refine Requirements" (back to Stage 2)

**State Persistence**:
- Full conversation history maintained
- Requirements and code versions tracked
- Ability to revert to previous stages or code versions

**API Integration**:
- Primary conversation endpoint: `POST /api/v1/ai/chat` with stage context
- Code management through dedicated PLC endpoints
- Real-time validation and testing integration

**User Control**:
- Clear stage indicators (1→2→3→4)
- Ability to force progression from Stage 2
- Option to return to requirements if code needs major changes
- Export functionality available throughout Stage 4
- Conversation state managed server-side
- Real-time validation and guidance at each stage

**UI Flow Control**:
- Clear stage progression indicators (1→2→3→4)
- Stage completion validation before advancement
- Ability to edit/refine previous stages
- Final deliverable summary and export options

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
  "model": "gpt-5-nano",
  "temperature": 1.0,
  "max_tokens": 128
}
```

Using curl:
```bash
curl -X POST "http://localhost:8000/api/v1/ai/chat" -H "Content-Type: application/json" -d '{"user_prompt":"Say hi","model":"gpt-5-nano","max_tokens":64}'
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
    body: JSON.stringify({ user_prompt: prompt, model: "gpt-5-nano" })
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
  - model: string (optional, default gpt-5-nano)
  - temperature: number (0.0 - 2.0) — some models only support default values; parameter errors will be returned as 400.
  - max_tokens (legacy): integer — legacy alias for `max_completion_tokens`
  - max_completion_tokens: integer — preferred field for completion limits

- Example request:
```json
{
  "user_prompt": "Explain emergency stop logic for a conveyor",
  "model": "gpt-5-nano",
  "temperature": 1.0,
  "max_completion_tokens": 128
}
```
- Example response:
```json
{
  "model": "gpt-5-nano",
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
  -d '{"user_prompt":"Say hi","model":"gpt-5-nano","max_tokens":64}'
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

### AI Chat
- POST /api/v1/ai/chat
  - Description: Send a user prompt to an LLM and receive a text response.
  - Request JSON:
    ```json
    {
      "user_prompt": "string",
      "model": "string (optional, default: gpt-5-nano)",
      "temperature": 1.0,
      "max_completion_tokens": 512
    }
    ```

### Conversation System
- POST /api/v1/conversations/ - Start a new conversation
- GET /api/v1/conversations/ - List conversations
- POST /api/v1/conversations/{id}/message - Send message to conversation
- GET /api/v1/conversations/{id} - Get conversation details
  - Response JSON:
    ```json
    {
      "model": "gpt-5-nano",
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

Advanced: OpenAPI and client SDKs
- FastAPI automatically generates an OpenAPI JSON at `/openapi.json`. Use it to generate client SDKs (e.g., via OpenAPI Generator or `openapi-python-client`).

Example to generate a Python client:
```bash
pip install openapi-python-client
openapi-python-client generate --url http://localhost:8000/openapi.json
```

Example to generate TypeScript client using OpenAPI Generator (requires Java):
```bash
openapi-generator-cli generate -i http://localhost:8000/openapi.json -g typescript-fetch -o ./frontend-client
```

---

If you'd like, I can:
- Add a README subsection that includes a minimal JavaScript client wrapper for the AI endpoints.
- Add CORS configuration examples and secure auth (JWT/API key).
- Add a GitHub Actions workflow to run tests and build OpenAPI clients on push.

Which of these would you like me to add next?