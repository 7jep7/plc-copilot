# PLC Copilot

A modern AI-powered assistant for PLC (Programmable Logic Controller) programming, built with OpenAI's Assistant API and designed for seamless integration with any frontend application.

## 🚀 Overview

PLC Copilot simplifies industrial automation programming by providing intelligent assistance for PLC code generation, requirement gathering, and technical documentation analysis. The system uses OpenAI's cutting-edge Assistant API with integrated vector store capabilities for robust document understanding and context-aware responses.

## ✨ Key Features

- **🤖 AI-Powered PLC Programming**: Intelligent code generation and technical guidance
- **📁 Smart Document Analysis**: Upload PDFs and get immediate device constant extraction
- **⚡ Dual Processing Modes**: Vector store for complex queries OR direct extraction for immediate results
- **💬 Interactive Requirements Gathering**: Smart questionnaires and conversation flow
- **🔄 Session Management**: Frontend-controlled session lifecycle with automatic cleanup
- **📊 Multiple Choice Questions**: Dynamic MCQ generation for requirement clarification
- **🎯 Progress Tracking**: Real-time progress estimation for requirements gathering
- **🏗️ Modern Architecture**: Built on OpenAI Assistant API with flexible file processing

## 🏛️ Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Application                     │
├─────────────────────────────────────────────────────────────┤
│                     FastAPI Backend                        │
├─────────────────────────────────────────────────────────────┤
│              SimplifiedContextService                      │
├─────────────────┬───────────────────────┬───────────────────┤
│ AssistantService│   VectorStoreService  │   Session Manager │
├─────────────────┴───────────────────────┴───────────────────┤
│                  OpenAI Assistant API                      │
│                  OpenAI Vector Store                       │
└─────────────────────────────────────────────────────────────┘
```

### Service Layer

- **SimplifiedContextService**: Main orchestration service handling three core interaction patterns
- **AssistantService**: Direct interface to OpenAI Assistant API with JSON schema enforcement
- **VectorStoreService**: File upload and management with OpenAI's native vector store

### API Design

The system provides a single, unified API endpoint that handles all interactions:
- `POST /api/v1/context/update` - Main interaction endpoint
- `POST /api/v1/context/cleanup` - Session cleanup endpoint
- `GET /api/v1/context/sessions/stats` - Session monitoring endpoint

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.11+
- OpenAI API Key with Assistant API access
- Virtual environment (recommended)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/7jep7/plc-copilot.git
   cd plc-copilot
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key and other settings
   ```

5. **Run the development server**
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
   ```

6. **Verify installation**
   ```bash
   curl http://localhost:8001/api/v1/context/health
   ```

### Environment Configuration

Create a `.env` file with the following variables:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_ASSISTANT_ID=your-assistant-id-here
OPENAI_VECTOR_STORE_ID=your-vector-store-id-here

# File Processing Configuration
USE_VECTOR_STORE=false  # Set to true to use OpenAI vector store, false for direct content extraction

# Database (SQLite for development)
DATABASE_URL=sqlite:///./plc_copilot.db

# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME=PLC Copilot

# Logging
LOG_LEVEL=INFO
```

## 📚 API Documentation

### Main Endpoint: Context Update

**`POST /api/v1/context/update`**

The primary endpoint for all interactions with the PLC Copilot assistant.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | Frontend-generated UUID for session tracking |
| `current_context` | string | Yes | JSON-encoded project context |
| `current_stage` | string | Yes | Current project stage (`gathering_requirements`, etc.) |
| `message` | string | No | User message or query |
| `mcq_responses` | string | No | JSON-encoded MCQ responses |
| `files` | file[] | No | File uploads (PDF, TXT, DOC) |

#### Example Request

```javascript
const formData = new FormData();
formData.append('session_id', crypto.randomUUID());
formData.append('current_context', JSON.stringify({
    device_constants: {},
    information: ""
}));
formData.append('current_stage', 'gathering_requirements');
formData.append('message', 'I need help with a conveyor belt control system');

const response = await fetch('/api/v1/context/update', {
    method: 'POST',
    body: formData
});
```

#### Response Format

```json
{
    "updated_context": {
        "device_constants": {},
        "information": "Updated project information..."
    },
    "chat_message": "I'd be happy to help with your conveyor belt system...",
    "session_id": "uuid-string",
    "is_mcq": true,
    "mcq_question": "What type of motor control do you need?",
    "mcq_options": ["VFD Control", "Direct On Line", "Soft Starter"],
    "is_multiselect": false,
    "generated_code": null,
    "current_stage": "gathering_requirements",
    "gathering_requirements_estimated_progress": 0.3
}
```

### Session Management

**`POST /api/v1/context/cleanup`**

Clean up session files and resources.

```json
{
    "session_ids": ["uuid1", "uuid2"]
}
```

**`GET /api/v1/context/sessions/stats`**

Get session statistics and monitoring information.

## 🔄 Integration Patterns

### Three Core Interaction Cases

The system handles three main interaction patterns:

1. **Project Kickoff** (No context, no files)
   - User starts with a general question
   - System offers sample projects via MCQ
   - Begins requirements gathering

2. **Context Update** (Context exists, no files)
   - User provides additional information
   - System updates project context
   - Continues requirements gathering or generates code

3. **File Upload** (Files + optional context)
   - User uploads technical documents
   - Files are processed via vector store OR direct extraction
   - Assistant uses document context for responses

## 📄 File Processing Modes

The system supports two file processing modes controlled by the `USE_VECTOR_STORE` configuration:

### Vector Store Mode (USE_VECTOR_STORE=true)
- **Best for**: Large document collections, complex multi-document queries
- **Process**: Files uploaded to OpenAI vector store → Assistant searches when needed
- **Pros**: Scalable, handles large documents, persistent storage
- **Cons**: May defer analysis, requires vector store setup

### Direct Extraction Mode (USE_VECTOR_STORE=false) ⭐ **Recommended**
- **Best for**: Immediate device constant extraction, fast response times
- **Process**: PDF text extracted → Key specifications parsed → Passed directly to assistant
- **Pros**: Immediate analysis, no deferred responses, token-optimized
- **Cons**: Limited by prompt token limits

#### Direct Extraction Features

When `USE_VECTOR_STORE=false`, the system:

1. **Extracts PDF text** using pdfplumber with table detection
2. **Categorizes technical specifications** into organized sections:
   - Basic Info (model, series, type)
   - Power & Environment (voltage, current, temperature, humidity)
   - Performance (CPU memory, program capacity, instruction speed)
   - I/O & Communication (max I/O points, max units)
   - Programming (languages, instruction sets, commands)
   - Physical (weight, dimensions, mounting)
3. **Optimizes content** to stay within token limits (~2000 tokens)
4. **Passes directly** to assistant for immediate device constant extraction

Example extracted specifications:
```
# Device Technical Specifications

## Basic Info:
- Model: KV-8000A
- Series: KV-8000/7000

## Power & Environment:
- Power Voltage: 24 VDC (±10%)
- Current Consumption: 400 mA or less
- Operating Temperature: 0 to +50°C (32 to 122°F)

## Performance:
- CPU Memory: 64 MB
- Program Capacity: Approx. 1500 k steps
- Instruction Speed: Min. 0.96 ns

## I/O & Communication:
- Max I/O Points: 3072 points for expansion
- Max Units: 16 units (expansion)

## Programming:
- Programming Language: Expanded ladder, KV Script, mnemonic
- Instructions: 80 classes, 181 instructions

## Physical:
- Weight: Approx. 340 g
```

### Session Lifecycle

```mermaid
graph TD
    A[Frontend generates UUID] --> B[Send initial request]
    B --> C[Assistant processes request]
    C --> D[Update project context]
    D --> E{More info needed?}
    E -->|Yes| F[Generate MCQ]
    E -->|No| G[Generate PLC Code]
    F --> H[User responds to MCQ]
    H --> C
    G --> I[Present final code]
    I --> J[Cleanup session]
```

## 🎯 Frontend Integration

### Session Management

Generate session IDs on the frontend using `crypto.randomUUID()`:

```javascript
const sessionId = crypto.randomUUID();
sessionStorage.setItem('plc-session-id', sessionId);
```

### File Upload

Include files in the same FormData as other parameters:

```javascript
const formData = new FormData();
formData.append('session_id', sessionId);
formData.append('current_context', JSON.stringify(context));
formData.append('current_stage', 'gathering_requirements');
formData.append('message', message);

// Add files
files.forEach(file => {
    formData.append('files', file);
});
```

### Session Cleanup

Clean up sessions when users finish:

```javascript
// Manual cleanup
await fetch('/api/v1/context/cleanup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_ids: [sessionId] })
});

// Automatic cleanup on page unload
window.addEventListener('beforeunload', () => {
    navigator.sendBeacon('/api/v1/context/cleanup', 
        JSON.stringify({ session_ids: [sessionId] }));
});
```

## 🏗️ Development

### Project Structure

```
plc-copilot/
├── app/
│   ├── api/
│   │   └── api_v1/
│   │       └── endpoints/
│   │           └── context.py          # Main API endpoint
│   ├── core/
│   │   ├── config.py                   # Configuration
│   │   ├── database.py                 # Database setup
│   │   └── logging.py                  # Logging configuration
│   ├── models/
│   │   └── base.py                     # Database models
│   ├── schemas/
│   │   └── context.py                  # Pydantic schemas
│   ├── services/
│   │   ├── assistant_service.py        # OpenAI Assistant interface
│   │   ├── simplified_context_service.py  # Main orchestration
│   │   └── vector_store_service.py     # File management
│   └── main.py                         # FastAPI application
├── st_code_library/                    # Sample PLC code library
├── requirements.txt                    # Python dependencies
├── docker-compose.yml                  # Docker configuration
└── README.md                          # This file
```

### Running Tests

The system includes basic health checks and monitoring:

```bash
# Basic functionality test
curl -X GET http://localhost:8001/api/v1/context/health

# Check session statistics
curl -X GET http://localhost:8001/api/v1/context/sessions/stats
```

### Development Server

```bash
# Development with auto-reload
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload

# Production-like
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🚀 Deployment

### Docker Deployment

```bash
# Build and run with Docker
docker-compose up --build

# Production deployment
docker-compose -f docker-compose.prod.yml up -d
```

### Environment-Specific Configuration

The application supports multiple deployment environments:

- **Development**: SQLite database, debug logging
- **Production**: PostgreSQL, structured logging
- **Docker**: Containerized with volume mounts

### Health Checks

The application provides health check endpoints:
- `GET /api/v1/context/health` - Basic health status
- `GET /api/v1/context/sessions/stats` - Session and resource monitoring

## 🔧 Configuration

### OpenAI Setup

1. **Create OpenAI Assistant**
   ```bash
   # Use OpenAI API or Dashboard to create an assistant
   # Configure with PLC programming instructions
   # Note the Assistant ID for configuration
   ```

2. **Create Vector Store**
   ```bash
   # Create a vector store for document processing
   # Associate with your assistant
   # Note the Vector Store ID for configuration
   ```

3. **Upload Sample Files**
   ```bash
   # Upload your PLC code library and documentation
   # to the vector store for enhanced responses
   ```

### Database Configuration

The application uses SQLAlchemy with support for multiple databases:

```python
# SQLite (development)
DATABASE_URL=sqlite:///./plc_copilot.db

# PostgreSQL (production)
DATABASE_URL=postgresql://user:password@localhost/plc_copilot
```

## �️ Troubleshooting

### Common Issues

#### "Request too large for gpt-4" Token Limit Error
**Problem**: File content exceeds OpenAI token limits when using vector store mode.

**Solution**: Switch to direct extraction mode:
```bash
# In .env file
USE_VECTOR_STORE=false
```

This enables intelligent content extraction that:
- Parses only key technical specifications
- Stays within token limits (~2000 tokens vs 30,000 limit)
- Provides immediate device constant extraction
- Avoids deferred analysis responses

#### Assistant Defers File Analysis
**Problem**: Assistant responds with "I will analyze..." instead of immediate extraction.

**Root Cause**: OpenAI Assistant API may defer complex file analysis by design.

**Solution**: Use direct extraction mode (`USE_VECTOR_STORE=false`) which bypasses this behavior.

#### PDF Text Extraction Fails
**Problem**: PDF files contain no extractable text or complex layouts.

**Troubleshooting**:
1. Check if PDF has text layers (not scanned images)
2. Try OCR preprocessing for scanned PDFs
3. Convert to text format before upload
4. Check logs for specific extraction errors

#### Session Cleanup Issues
**Problem**: Uploaded files not properly cleaned up.

**Solution**:
```bash
# Manual cleanup via API
curl -X POST http://localhost:8000/api/v1/context/cleanup \
  -H "Content-Type: application/json" \
  -d '{"session_ids": ["your-session-id"]}'

# Check session stats
curl http://localhost:8000/api/v1/context/sessions/stats
```

### Performance Optimization

#### For Large Documents
- Use vector store mode for documents > 10 pages
- Enable `USE_VECTOR_STORE=true` for complex multi-document queries
- Consider document preprocessing to extract key sections

#### For Fast Response Times
- Use direct extraction mode (`USE_VECTOR_STORE=false`)
- Upload single-page specification sheets
- Use concise, well-structured technical documents

## �📊 Monitoring & Analytics

### Session Statistics

Monitor application usage through the stats endpoint:

```json
{
    "stats": {
        "active_sessions": 5,
        "total_files_tracked": 23,
        "timeout_minutes": 30,
        "avg_session_age_minutes": 12.5
    }
}
```

### Logging

The application provides structured logging with configurable levels:

```python
# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Log format includes timestamps, levels, and context
{"timestamp": "2025-09-18T22:00:00Z", "level": "info", "message": "Session created", "session_id": "uuid"}
```

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Standards

- Follow PEP 8 for Python code style
- Use type hints for all function parameters and returns
- Include docstrings for all public methods
- Write comprehensive tests for new features

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for providing the Assistant API and vector store capabilities
- FastAPI for the excellent web framework
- The industrial automation community for inspiration and requirements

## 📞 Support

For questions, issues, or feature requests:

- Create an issue on GitHub
- Check the API documentation at `/docs` when the server is running
- Review the health check endpoint for system status

---

**Built with ❤️ for the industrial automation community**