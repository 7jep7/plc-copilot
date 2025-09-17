# PLC Copilot Backend

> **A FastAPI backend for automating PLC (Programmable Logic Controller) programming with context-centric AI assistance.**

🎯 **Context-Centric**: Transparent, editable project context eliminates hidden state  
🤖 **AI-Powered**: Converts natural language requirements into production-ready PLC code  
� **Immediate Processing**: Upload files and instantly extract device specifications  
🔧 **Code Library**: Industrial-grade ST code samples with intelligent search  
🚀 **Production Ready**: Deployed on Render.com with comprehensive monitoring

## Table of Contents

### Getting Started
- [Vision](#vision)
- [Features](#features)
- [Quick Start](#quick-start)

### For Developers
- [Frontend Quick Start](FRONTEND_QUICK_START.md) ⭐
- [API Reference](#api-reference)
- [User Workflow](#user-workflow)

### Operations
- [Deployment](#deployment)
- [Development](#development)

### Integration
- [Code Library](#code-library)
- [Dependencies](#dependencies)

## Vision

Create the copilot for Programmable Logic Controllers. Automate automating. Program, test, maintain, and redeploy robots and any PLC-powered assembly line and industrial process with complete transparency and user control.

## 🚀 What's New - Major Architecture Improvements

### **🎯 Context-Centric Refactor (Latest)**
- **Single Endpoint**: All interactions through `POST /api/v1/context/update`
- **Single LLM Call**: Eliminated multi-step latency - one comprehensive AI interaction per request
- **Conversation Continuity**: `previous_copilot_message` field enables natural conversation flow
- **Robust Error Handling**: JSON parsing retry with corrective prompts when LLM responses fail

### **🧠 Advanced Prompt Engineering**
- **Dual Template System**: Template A (user-only) vs Template B (file analysis) optimization
- **Conditional Logic**: MCQ/off-topic handling only mentioned when relevant (token optimization)
- **LLM-Driven Analysis**: AI determines topic coverage, progress, and next actions autonomously
- **Domain Expertise**: Industrial automation-specific prompt engineering

### **⚡ Performance & Reliability**
- **Immediate File Processing**: PDFs analyzed and integrated in single API call
- **Device Origin Tracking**: Track whether devices come from user input or file analysis
- **Async/Sync Compatibility**: Flexible deployment with comprehensive test coverage
- **Rate Limit Intelligence**: Automatic OpenAI model fallback (gpt-4o-mini → gpt-3.5-turbo → gpt-4o)

## Features

### 🏗️ **Robust Backend Architecture** 
1. **🎯 Context-Centric Design**: Single source of truth with transparent, editable project context
2. **⚡ Single LLM Call Per Interaction**: Eliminates latency from multiple API calls  
3. **🧠 Intelligent Prompt Engineering**: Dual template system (Template A/B) optimized for different scenarios
4. **🔄 Robust Error Handling**: JSON parsing retry logic with corrective prompts
5. **📄 Immediate File Processing**: Upload PDFs and instantly extract PLC-relevant specifications  

### 🤖 **AI-Powered Intelligence**
6. **🎯 LLM-Driven Requirements Analysis**: AI determines topic coverage and progress automatically
7. **📊 Smart Progress Tracking**: Automatic requirements completion estimation (0.0-1.0)
8. **❓ Conditional MCQ System**: AI generates questions only when needed, not prompted unnecessarily
9. **🔍 Context-Aware Responses**: Previous conversation context for natural flow
10. **🏭 Industrial Domain Expertise**: Specialized for PLC/automation engineering

### 🛠️ **Production-Ready Features**
- **Single Integration Point**: All interactions through `POST /api/v1/context/update`
- **Stateless Operation**: No hidden conversation state to debug
- **Type Safety**: Strong Pydantic schemas for reliable integration  
- **Async/Sync Compatibility**: Flexible for different deployment scenarios
- **Comprehensive Testing**: Full test suite with integration and unit tests
- **Device Origin Tracking**: Track whether devices come from user input or file analysis

### 🔧 **Additional Capabilities**
11. **Code Generation**: Convert natural language and context into production-ready Structured Text
12. **Digital Twin Testing**: Simple simulation functionality for code validation
13. **Code Library & Knowledge Base**: Industrial-grade ST code samples with intelligent search
14. **Direct AI Chat**: Stateless chat endpoint for quick questions
15. **File Extraction Results**: LLM-processed file content included in API responses

### 🏢 **Enterprise-Ready Architecture**
- **RESTful API**: Context-centric architecture with stateless endpoints
- **Production Deployment**: Ready for Render.com with comprehensive monitoring
- **Structured Logging**: Detailed logging for debugging and monitoring
- **Database Integration**: PostgreSQL with Alembic migrations
- **Background Processing**: Celery support for long-running tasks
- **Comprehensive Validation**: Request/response validation with clear error messages
- **Rate Limiting**: Intelligent OpenAI model fallback and cost management

### Rate Limiting & Cost Management 💡

**MVP Cost Optimization**: The system includes intelligent OpenAI model cascade fallback to manage costs while using free hackathon credits. Models are tried in order of cost-effectiveness: `gpt-4o-mini` → `gpt-3.5-turbo` → `gpt-4o`. The system includes session-based memory and daily reset logic, with email notifications when rate limits are reached (once per session). This temporary solution avoids upgrading to OpenAI Tier 1 until natural usage reaches the $5 threshold.

**Tier 0 Limits**: Before spending $5 (Tier 0), you are restricted to **200 requests per day per model**. The backend tracks usage and enforces these limits automatically. Once you reach the $5 spend threshold, higher limits apply.

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
- **New Context API**: http://localhost:8000/api/v1/context/update
- Health check: http://localhost:8000/health

### Quick Test with Context API

```bash
# Test the new unified endpoint
curl -X POST "http://localhost:8000/api/v1/context/update" \
  -F "message=I need to automate a conveyor belt system" \
  -F "current_context={\"device_constants\":{},\"information\":\"\"}" \
  -F "current_stage=gathering_requirements"
```

Example response:
```json
{
  "updated_context": {
    "device_constants": {},
    "information": "## Project: Conveyor Belt Automation\n- Basic conveyor control system required"
  },
  "chat_message": "Great! I'll help you design a conveyor belt control system. What type of items will the conveyor be handling?",
  "gathering_requirements_progress": 0.1,
  "current_stage": "gathering_requirements",
  "is_mcq": false,
  "mcq_options": []
}

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

### 🎯 **Context-Centric Architecture** ⭐

#### **Main Context API - Single Endpoint for Everything**
**`POST /api/v1/context/update`** - **Primary endpoint** for all user interactions
- **Unified Processing**: Messages, MCQ responses, file uploads, and context updates in one call
- **Single LLM Interaction**: Eliminates latency from multiple API calls per interaction
- **Intelligent Prompt Selection**: 
  - **Template A**: Optimized for user-only interactions (no files)
  - **Template B**: Optimized for file analysis with user context prioritization
- **Conversation Continuity**: Supports `previous_copilot_message` field for natural flow
- **Robust Error Handling**: JSON parsing retry with corrective prompts
- **File Processing**: Immediate PDF analysis with selective PLC-relevant extraction
- **Content-Type**: `multipart/form-data` for file uploads

#### **Key API Capabilities**
- **Context Management**: Transparent, editable project context with device origin tracking
- **Progress Estimation**: AI-driven requirements completion analysis (0.0-1.0)
- **MCQ Generation**: Conditional multiple-choice questions when needed
- **Stage Management**: Three-stage workflow (requirements → code → refinement)
- **File Integration**: Immediate processing with LLM-analyzed results in response

### 🧠 **Advanced Prompt Engineering**

#### **Dual Template System**
- **Template A**: Optimized for direct user interactions (text/MCQ only)
  - Streamlined prompts for faster processing
  - Focused on conversation flow and requirements gathering
  - Conditional logic - only mentions MCQ/off-topic handling when relevant
  
- **Template B**: Optimized for file analysis scenarios  
  - User input prioritized, files provide supplementary context
  - Intelligent file content integration
  - Selective PLC-relevant information extraction

#### **Intelligent Prompt Optimization**
- **Token Efficiency**: Conditional prompt sections reduce unnecessary token usage
- **Context-Aware**: Previous conversation context for natural flow
- **LLM-Driven Analysis**: AI determines topic coverage, progress, and next actions
- **Error Recovery**: Corrective prompts when JSON parsing fails
- **Domain Expertise**: Industrial automation-specific prompt engineering

#### **Legacy API Endpoints** (Available but not recommended for new projects)
*Use the Context API above for new integrations*

- **AI Chat**: `POST /api/v1/ai/chat` - Stateless chat interactions
- **PLC Code Management**: CRUD operations for generated code
- **Digital Twin**: Simulation configuration and testing  
- **Code Library**: Industrial ST code samples and search
- **System**: Health checks and API information

*Full endpoint documentation available at `/docs` when running locally*

## 🏗️ Backend Architecture

### **Service Layer Architecture**
```
📁 app/
├── 🎯 api/v1/endpoints/          # FastAPI route handlers
│   ├── context.py               # Main context-centric endpoint
│   ├── ai.py                    # Direct AI chat
│   ├── plc_code.py              # PLC code management
│   └── digital_twin.py          # Simulation endpoints
├── 🧠 services/                 # Business logic layer
│   ├── context_service.py       # Core context processing (NEW)
│   ├── prompt_templates.py      # Dual template system (NEW)
│   ├── openai_service.py        # LLM integration with fallback
│   └── document_service.py      # File processing utilities
├── 📊 schemas/                  # Pydantic data models
│   ├── context.py               # Context & workflow schemas (UPDATED)
│   ├── openai.py                # LLM request/response models
│   └── plc_code.py              # Code generation schemas
└── 🏭 models/                   # SQLAlchemy database models
    ├── conversation.py          # Chat history storage
    ├── plc_code.py              # Generated code storage
    └── document.py              # File metadata storage
```

### **Key Architecture Improvements**
- **🎯 Single Source of Truth**: `ContextService` orchestrates all interactions
- **⚡ Performance**: Single LLM call eliminates multi-step latency
- **🛡️ Robust Error Handling**: JSON parsing retry with corrective prompts
- **🧩 Modular Design**: Clean separation between API, services, and data layers
- **📈 Scalable**: Async/await patterns for high-concurrency deployment

## User Workflow

The PLC Copilot features a **unified context-centric approach** that simplifies frontend integration while providing powerful AI-driven automation project development.

## 🎯 New Context-Centric Workflow

### Single API Approach ⭐
**All user interactions now go through one powerful endpoint: `POST /api/v1/context/update`**

### Project Context Structure
The system maintains a unified context with two main components:

```json
{
  "device_constants": {
    "ConveyorSystem": {
      "Motor": {
        "Type": "AC Servo",
        "Power": "2.5kW",
        "Sensors": {
          "PositionEncoder": {"Resolution": "1024 PPR"},
          "ProximitySensor": {"Type": "Inductive", "Range": "8mm"}
        }
      }
    },
    "SafetySystem": {
      "EmergencyStops": {"Count": 3, "Type": "Category 3"},
      "LightCurtains": {"Height": "1800mm", "Resolution": "30mm"}
    }
  },
  "information": "Brief markdown summary of project requirements and decisions..."
}
```

### **Advanced Workflow Management**

#### **Three-Stage Process**
1. **📋 Gathering Requirements** - AI-driven requirements analysis with intelligent questioning
2. **⚙️ Code Generation** - Complete Structured Text generation from comprehensive context  
3. **🔧 Refinement & Testing** - Iterative improvement and validation

#### **Intelligent Stage Management**
- **🤖 AI-Driven Progress**: Automatic completion estimation (0.0-1.0 scale)
- **🎯 Context-Aware Transitions**: AI determines readiness for next stage
- **🚀 User Override**: Frontend can force stage transitions when needed
- **➡️ Forward-Only Flow**: Prevents confusion from backward navigation

#### **Smart File Processing**
- **⚡ Immediate Analysis**: Files processed and integrated in single API call
- **🎯 Selective Extraction**: AI identifies and extracts only PLC-relevant data
- **🏷️ Origin Tracking**: Device constants tagged as "user message" or "file" origin
- **💾 No Storage Required**: Documents processed and discarded (privacy-focused)

#### **Enhanced Context Management**
- **📊 Structured Data**: Device constants stored as structured objects with metadata
- **📝 Information Layer**: Markdown-formatted project requirements and decisions
- **🔄 Conversation Continuity**: Previous AI messages inform natural response flow
- **✏️ User Editable**: Complete transparency - users can view/edit all AI knowledge

## Context API Usage

### Request Format
```http
POST /api/v1/context/update
Content-Type: multipart/form-data

message: "I need optical sensors for detection"
mcq_responses: ["Emergency stop buttons only", "Light curtains"]  // JSON array
previous_copilot_message: "What safety measures does your system need?"  // Optional
current_context: {
  "device_constants": {...},
  "information": "project requirements..."
}
current_stage: "gathering_requirements"
files: [file1.pdf, file2.pdf]  // Optional file uploads
```

### Response Format
```json
{
  "updated_context": {
    "device_constants": {...},  // Updated with new information
    "information": "updated markdown summary"
  },
  "chat_message": "What's the operating voltage for your motors?",
  "gathering_requirements_progress": 0.7,  // Only in gathering_requirements stage
  "current_stage": "gathering_requirements",
  "is_mcq": true,
  "is_multiselect": false,
  "mcq_question": "What voltage do your motors require?",
  "mcq_options": ["24V DC", "230V AC", "400V AC", "Other"],
  "generated_code": null  // Only present when current_stage = "code_generation"
}
```

### Frontend Integration Examples

#### React/TypeScript Implementation
```typescript
interface ProjectContext {
  device_constants: Record<string, any>;
  information: string;
}

interface ContextResponse {
  updated_context: ProjectContext;
  chat_message: string;
  gathering_requirements_progress?: number;
  current_stage: 'gathering_requirements' | 'code_generation' | 'refinement_testing';
  is_mcq: boolean;
  is_multiselect: boolean;
  mcq_question?: string;
  mcq_options: string[];
  generated_code?: string;
}

async function updateContext(
  message?: string,
  mcqResponses?: string[],
  previousCopilotMessage?: string,
  context: ProjectContext,
  stage: string,
  files?: File[]
): Promise<ContextResponse> {
  const formData = new FormData();
  
  if (message) formData.append('message', message);
  if (mcqResponses?.length) formData.append('mcq_responses', JSON.stringify(mcqResponses));
  if (previousCopilotMessage) formData.append('previous_copilot_message', previousCopilotMessage);
  formData.append('current_context', JSON.stringify(context));
  formData.append('current_stage', stage);
  
  if (files) {
    files.forEach(file => formData.append('files', file));
  }
  
  const response = await fetch('/api/v1/context/update', {
    method: 'POST',
    body: formData
  });
  
  return response.json();
}

// Usage examples
const result = await updateContext(
  "I need to automate a conveyor belt system",
  undefined,
  undefined,  // No previous message for first interaction
  { device_constants: {}, information: "" },
  "gathering_requirements"
);

// Handle MCQ response with conversation continuity
const mcqResult = await updateContext(
  undefined,
  ["Emergency stop buttons only", "Light curtains"],
  result.chat_message,  // Pass previous AI response for context
  currentContext,
  "gathering_requirements"
);

// File upload with message and conversation context
const fileResult = await updateContext(
  "Here's the motor datasheet",
  undefined,
  lastCopilotMessage,  // Maintain conversation flow
  currentContext,
  "gathering_requirements",
  [motorDatasheet.pdf]
);

// Force code generation
const codeResult = await updateContext(
  undefined,
  undefined,
  lastCopilotMessage,
  currentContext,
  "code_generation"  // AI will generate Structured Text
);
```

#### Vue.js Implementation
```javascript
export default {
  data() {
    return {
      context: { device_constants: {}, information: "" },
      currentStage: "gathering_requirements",
      chatMessage: "",
      lastCopilotMessage: null,  // Track for conversation continuity
      isMcq: false,
      mcqOptions: [],
      progress: 0
    };
  },
  methods: {
    async sendMessage(message, files = null) {
      try {
        const formData = new FormData();
        formData.append('message', message);
        if (this.lastCopilotMessage) {
          formData.append('previous_copilot_message', this.lastCopilotMessage);
        }
        formData.append('current_context', JSON.stringify(this.context));
        formData.append('current_stage', this.currentStage);
        
        if (files) {
          Array.from(files).forEach(file => formData.append('files', file));
        }
        
        const response = await fetch('/api/v1/context/update', {
          method: 'POST',
          body: formData
        });
        
        const result = await response.json();
        
        // Update component state
        this.context = result.updated_context;
        this.currentStage = result.current_stage;
        this.chatMessage = result.chat_message;
        this.lastCopilotMessage = result.chat_message;  // Store for next interaction
        this.isMcq = result.is_mcq;
        this.mcqOptions = result.mcq_options || [];
        this.progress = result.gathering_requirements_progress || 0;
        
        if (result.generated_code) {
          this.showGeneratedCode(result.generated_code);
        }
        
      } catch (error) {
        console.error('Context update failed:', error);
      }
    }
  }
};
```

### Key Benefits of Context API

1. **Simplified Integration**: Single endpoint handles all interactions
2. **Intelligent File Processing**: Immediate extraction of PLC-relevant data
3. **AI-Driven Progress**: Automatic calculation of requirements completeness
4. **Flexible JSON Structure**: Supports complex nested device hierarchies
5. **Lean Context Management**: Focuses on essential information only
6. **Stage-Aware Responses**: Specialized AI behavior for each workflow stage
7. **MCQ Support**: Structured questions for standardized inputs

### Migration from Legacy APIs

If you're using the old conversation endpoints, migration is straightforward:

**Old Approach:**
```typescript
// Multiple endpoints and complex state management
POST /api/v1/conversations/ 
POST /api/v1/conversations/{id}/documents/upload
POST /api/v1/conversations/{id}/stage
GET /api/v1/conversations/{id}
```

**New Approach:**
```typescript
// Single endpoint for everything
POST /api/v1/context/update
```

The new Context API provides all the functionality of the legacy system with significantly simpler integration and more powerful AI capabilities.

## Legacy User Workflow (Deprecated)

*The following section describes the old 4-stage conversation system. Use the Context API above for new implementations.*

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

## 🧪 Testing & Reliability

### **Comprehensive Test Suite**
```bash
# Run all tests
python -m pytest tests/ -v

# Context API tests (core functionality)
python -m pytest tests/test_context_api.py -v

# Integration tests (full workflow)
python -m pytest tests/integration/ -v
```

### **Test Coverage**
- **✅ Context API**: Full workflow testing with mocked LLM responses
- **✅ File Processing**: PDF extraction and integration testing 
- **✅ Error Handling**: JSON parsing failures and retry logic
- **✅ Stage Transitions**: Requirements → Code → Refinement workflows
- **✅ MCQ System**: Question generation and response handling
- **✅ Async/Sync Compatibility**: Support for different deployment scenarios

### **Robust Error Handling**
- **🔄 JSON Parse Retry**: Automatic corrective prompts when LLM response fails to parse
- **🎯 Rate Limit Management**: Intelligent model fallback (gpt-4o-mini → gpt-3.5-turbo → gpt-4o)
- **📊 Structured Validation**: Pydantic schemas ensure type safety throughout
- **🛡️ Graceful Degradation**: Fallback responses when AI services are unavailable
- **📝 Comprehensive Logging**: Detailed error tracking for debugging

### **Interactive CLI Demo**
```bash
# Test the full workflow interactively
python scripts/cli_flow_demo.py --live

# Dry run (no API calls)
python scripts/cli_flow_demo.py
```

### **Production Readiness**
- **⚡ Performance**: Single LLM call per interaction (reduced latency)
- **🔄 Async Processing**: FastAPI async/await for high concurrency
- **📊 Monitoring**: Health checks and structured logging
- **🏭 Scalability**: Stateless design enables horizontal scaling
- **🛡️ Security**: Input validation and sanitization throughout

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
│   │   ├── models.py          # Model configuration and fallback cascade
│   │   └── logging.py         # Structured logging setup
│   ├── api/                   # API endpoints
│   │   └── api_v1/           # API version 1
│   │       ├── api.py        # Main API router
│   │       └── endpoints/    # Individual endpoint modules
│   ├── models/               # SQLAlchemy database models
│   │   ├── document.py       # Document/manual models
│   │   ├── plc_code.py      # PLC code models
│   │   ├── conversation.py   # Conversation models
│   │   └── digital_twin.py  # Simulation models
│   ├── schemas/              # Pydantic request/response schemas
│   ├── services/             # Business logic services
│   │   ├── openai_service.py           # OpenAI API integration
│   │   ├── document_service.py         # Document processing
│   │   ├── conversation_orchestrator.py # Multi-stage conversations
│   │   ├── notification_service.py     # Email notifications
│   │   ├── plc_service.py              # PLC code management
│   │   └── digital_twin_service.py     # Simulation logic
│   └── worker.py             # Celery worker configuration
├── docs/                     # Documentation
│   ├── api/                  # API documentation
│   │   ├── API_READY_FOR_FRONTEND.md
│   │   ├── FRONTEND_INTEGRATION_GUIDE.md
│   │   └── FINAL_API_STATUS_REPORT.md
│   ├── deployment/           # Deployment guides
│   │   └── DEPLOYMENT.md
│   ├── conversation_system.md # Conversation system architecture
│   └── COST_OPTIMIZATION.md  # Cost optimization strategies
├── tests/                    # Test suite
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── fixtures/             # Test fixtures and sample data
│       └── sample_documents/ # Sample PDFs for document parser testing
├── scripts/                  # Utility scripts
│   ├── dev_server.py         # Development server
│   ├── init_db.py           # Database initialization
│   └── demo_*.py            # Demo scripts
├── st_code_library/         # Industrial ST code samples
├── alembic/                 # Database migrations
├── requirements.txt         # Python dependencies
├── render.yaml             # Render.com deployment config
├── docker-compose.yml      # Local Docker development
├── Dockerfile              # Container configuration
└── README.md              # This file
```
├── st_code_library/          # ST code samples
├── user_uploads/             # User-uploaded files
├── alembic/                  # Database migrations
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
- **Deployment**: Render.com with Docker containerization

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
- Documents are truncated to **8000 characters** (≈8 KB) per document before being included in prompts to control token usage. This is characters, not tokens. 8000 characters roughly corresponds to **4–8 pages** of typical datasheet or marketing PDF content (page count depends on layout, tables and figures — estimate ~1000–2000 characters of readable text per page). If you need the entire document analysed, provide a short human-prepared summary or split the PDF into smaller parts; for more accurate token budgeting consider switching to a token-based truncation (e.g., via tiktoken).
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
TESTING=true python tests/integration/test_4_stage_system_efficient.py

# Test MCQ functionality
TESTING=true python tests/integration/test_mcq.py

# Test model cascade and fallback
python tests/integration/test_model_cascade.py
```

#### Comprehensive Testing
For full coverage (higher cost):
```bash
# Full test suite
python tests/integration/test_4_stage_system.py

# Test all endpoints
python tests/integration/test_all_endpoints.py

# Test document processing
python tests/integration/test_document_processing.py /path/to/sample.pdf
```

#### Unit Testing
```bash
# Run unit tests
pytest tests/unit/

# Run specific test
python tests/unit/test_ai_chat.py
```

Run the Code Library API test suite:
```bash
python tests/integration/test_code_library_api.py
```

> 💡 **Cost Tip**: Set `TESTING=true` to use gpt-4o-mini with reduced token limits. See [docs/COST_OPTIMIZATION.md](docs/COST_OPTIMIZATION.md) for details.

## Development

## Development

### **Development Workflow**
```bash
# Start development environment
conda activate plc-copilot  # or your preferred venv
python scripts/dev_server.py

# Run with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **Code Quality & Standards**
```bash
# Format code
black app/
isort app/

# Type checking
mypy app/

# Lint
flake8 app/

# Test suite
pytest tests/ -v
pytest tests/test_context_api.py -v  # Core functionality
pytest tests/integration/ -v        # Full workflows
```

### **Database Management**
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### **Interactive Development**
```bash
# Test context API interactively
python scripts/cli_flow_demo.py --live

# Test prompt templates
python -c "
from app.services.prompt_templates import PromptTemplates
from app.schemas.context import ProjectContext, Stage
# Test template generation...
"
```

### **Performance & Monitoring**
- **Health Endpoint**: `/health` - System status and dependencies
- **Structured Logging**: JSON logs with request correlation IDs
- **Metrics Ready**: Prometheus integration points available
- **Error Tracking**: Sentry integration (configure `SENTRY_DSN`)
- **Request Validation**: Comprehensive Pydantic schemas throughout

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
  "user_prompt": "Explain PLC ladder logic basics",
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
  "gathering_requirements_estimated_progress": 0.0,
  "stage_progress": { "requirements_identified": 2, "confidence": 0.7 },
  "suggested_actions": [
    "Provide conveyor speed requirements",
    "Specify safety sensor types"
  ],
  "is_mcq": false,
  "mcq_question": null,
  "mcq_options": [],
  "is_multiselect": false,
  "generated_code": null
}
```

**MCQ Response Example (gather_requirements stage):**
```json
{
  "conversation_id": "uuid-string",
  "stage": "gather_requirements",
  "response": "What safety features do you require for your conveyor system?",
  "next_stage": "gather_requirements",
  "gathering_requirements_estimated_progress": 0.6,
  "suggested_actions": ["Select your required safety features"],
  "is_mcq": true,
  "mcq_question": "What safety features do you require for your conveyor system?",
  "mcq_options": [
    "Emergency stop buttons only",
    "Light curtains for perimeter protection",
    "Safety mats for operator zones",
    "Comprehensive safety package (all features)"
  ],
  "is_multiselect": false,
  "generated_code": null
}
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

**🚀 Quick Start:** See the [Frontend Quick Start Guide](FRONTEND_QUICK_START.md) for a concise integration guide.

**📖 Complete Documentation:** Available at http://localhost:8000/docs

### Key Points
- **One Endpoint:** All interactions through `POST /api/v1/context/update`
- **Transparent Context:** No hidden state, everything visible and editable
- **File Processing:** Upload PDFs and get immediate analysis
- **MCQ Support:** Structured questions for faster data gathering

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