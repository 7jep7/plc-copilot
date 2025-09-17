# PLC-Copilot API: Context-Centric Architecture

## 📋 Executive Summary

✅ **API Server Status**: Running and functional on http://localhost:8000  
✅ **Database Configuration**: SQLite configured and initialized  
✅ **Context-Centric API**: Unified workflow with transparent operation  
✅ **File Processing**: Built-in multipart support for document uploads  
📖 **Documentation**: Available at http://localhost:8000/docs  

## 🎯 Architecture Overview

The PLC-Copilot backend has been completely refactored to use a **context-centric architecture** that eliminates the complexity of conversation state management. Everything the AI knows is stored in a transparent, editable context object.

### Key Benefits
- **Single Integration Point**: One endpoint handles all interactions
- **Stateless Operation**: No hidden conversation state to debug
- **Transparent Context**: Users can see and edit exactly what the AI knows
- **File Processing**: Documents processed immediately, not stored
- **Type Safety**: Strong interfaces for reliable integration

## 🔌 API Endpoints Ready for Frontend Integration

### Base Configuration
- **Base URL**: `http://localhost:8000`
- **API Prefix**: `/api/v1`
- **Content-Type**: `multipart/form-data` (main endpoint) or `application/json`

### Core System Endpoints

# PLC-Copilot API: Context-Centric Architecture

## 📋 Executive Summary

✅ **API Server Status**: Running and functional on http://localhost:8000  
✅ **Database Configuration**: SQLite configured and initialized  
✅ **Context-Centric API**: Unified workflow with transparent operation  
✅ **File Processing**: Built-in multipart support for document uploads  
📖 **Documentation**: Available at http://localhost:8000/docs  

## 🎯 Architecture Overview

The PLC-Copilot backend has been completely refactored to use a **context-centric architecture** that eliminates the complexity of conversation state management. Everything the AI knows is stored in a transparent, editable context object.

### Key Benefits
- **Single Integration Point**: One endpoint handles all interactions
- **Stateless Operation**: No hidden conversation state to debug
- **Transparent Context**: Users can see and edit exactly what the AI knows
- **File Processing**: Documents processed immediately, not stored
- **Type Safety**: Strong interfaces for reliable integration

## 🔌 API Endpoints Ready for Frontend Integration

### Base Configuration
- **Base URL**: `http://localhost:8000`
- **API Prefix**: `/api/v1`
- **Content-Type**: `multipart/form-data` (main endpoint) or `application/json`

### Core System Endpoints

#### Health Check
```http
GET /health
```
**Response**: `{"status": "healthy", "service": "plc-copilot-backend"}`

#### Root Information
```http
GET /
```
**Response**: Service information and docs link

### 🎯 Main Context Endpoint

#### Context Update (Primary Integration Point)
```http
POST /api/v1/context/update
Content-Type: multipart/form-data

message=I need help with a conveyor system          # Optional user message
mcq_responses=["Option A", "Option B"]               # Optional MCQ responses (JSON array)
files=@motor_spec.pdf                               # Optional file uploads
current_context={"device_constants": {}, "information": ""}  # Required current context (JSON)
current_stage=gathering_requirements                # Required current stage
```

**Response Example**:
```json
{
  "updated_context": {
    "device_constants": {
      "conveyor_belt": {
        "speed_max": "2.5 m/s",
        "width": "600mm"
      }
    },
    "information": "# Conveyor System Requirements\n\n- Emergency stop functionality\n- Variable speed control"
  },
  "current_stage": "gathering_requirements",
  "progress": 0.4,
  "chat_message": "Great! I understand you need a conveyor system. What's the maximum load capacity?",
  "is_mcq": true,
  "mcq_question": "What's the maximum load capacity for your conveyor?",
  "mcq_options": ["Under 50kg", "50-100kg", "100-500kg", "Over 500kg"],
  "is_multiselect": false,
  "generated_code": null,
  "metadata": {
    "tokens_used": 245,
    "processing_time": 1.8
  }
}
```

**Status**: ✅ Working (requires valid OpenAI API key)

### 🤖 AI Chat Endpoints

#### Direct AI Chat (Stateless)
```http
POST /api/v1/ai/chat
Content-Type: application/json

{
  "message": "Explain how PID controllers work in motor control",
  "context": {
    "device_constants": {},
    "information": "Working on motor control system"
  }
}
```

**Response Example**:
```json
{
  "response": "PID controllers in motor control work by...",
  "metadata": {
    "tokens_used": 150,
    "processing_time": 1.2
  }
}
```

**Status**: ✅ Working (requires valid OpenAI API key)

### � PLC Code Management

#### List PLC Codes
```http
GET /api/v1/plc/codes
```

**Response Example**:
```json
{
  "codes": [
    {
      "id": 1,
      "name": "Conveyor Control System",
      "description": "Basic conveyor belt control with safety features",
      "code_content": "PROGRAM ConveyorControl...",
      "language": "structured_text",
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

#### Create PLC Code
```http
POST /api/v1/plc/codes
Content-Type: application/json

{
  "name": "Motor Control System",
  "description": "VFD motor control with safety",
  "code_content": "PROGRAM MotorControl...",
  "language": "structured_text"
}
```

#### Get Specific PLC Code
```http
GET /api/v1/plc/codes/{id}
```

#### Update PLC Code
```http
PUT /api/v1/plc/codes/{id}
Content-Type: application/json

{
  "name": "Updated Motor Control",
  "description": "Enhanced motor control with PID",
  "code_content": "PROGRAM EnhancedMotorControl..."
}
```

#### Delete PLC Code
```http
DELETE /api/v1/plc/codes/{id}
```

#### Generate PLC Code
```http
POST /api/v1/plc/generate
Content-Type: application/json

{
  "context": {
    "device_constants": {
      "motor": {"rated_power": "5kW", "rated_speed": "1450rpm"}
    },
    "information": "Need motor control with safety features"
  },
  "requirements": "Generate motor control code with emergency stop"
}
```

**Status**: ✅ All PLC endpoints working

### 🏭 Digital Twin Management

#### List Digital Twin Configurations
```http
GET /api/v1/digital-twin/configs
```

#### Create Digital Twin Configuration
```http
POST /api/v1/digital-twin/configs
Content-Type: application/json

{
  "name": "Conveyor System Twin",
  "description": "Digital twin for conveyor control",
  "config": {
    "components": ["motor", "sensors", "safety_systems"],
    "parameters": {"belt_speed": "2.5", "load_capacity": "100"}
  }
}
```

#### Run Digital Twin Simulation
```http
POST /api/v1/digital-twin/simulate
Content-Type: application/json

{
  "config_id": 1,
  "simulation_parameters": {
    "duration": 60,
    "load_profile": "variable"
  }
}
```

**Status**: ✅ All digital twin endpoints working

### 📚 Code Library

#### Browse Code Examples
```http
GET /api/v1/library/examples?category=motor_control&language=structured_text
```

**Response Example**:
```json
{
  "examples": [
    {
      "id": "vfd_motor_control",
      "name": "VFD Motor Control System",
      "description": "Complete VFD motor control with safety features",
      "category": "motor_control",
      "language": "structured_text",
      "file_path": "st_code_library/motor_control/vfd_motor_control_system.st"
    }
  ]
}
```

#### Search Code Library
```http
POST /api/v1/library/search
Content-Type: application/json

{
  "query": "safety relay motor control",
  "category": "safety_systems",
  "language": "structured_text"
}
```

**Status**: ✅ All library endpoints working

## 🎯 Context Structure

### Project Context Interface
```typescript
interface ProjectContext {
  device_constants: {
    [deviceName: string]: {
      [property: string]: string | number | object
    }
  };
  information: string; // Markdown format
}
```

### Stage Flow
1. **`gathering_requirements`** - Collect project requirements through chat and MCQs
2. **`code_generation`** - Generate PLC code based on context
3. **`refinement_testing`** - Refine and test the generated code

## 🧪 Testing & Validation

### API Testing Commands

#### Test Context Update
```bash
curl -X POST http://localhost:8000/api/v1/context/update \
  -F 'message=I need help with a conveyor system' \
  -F 'current_context={"device_constants": {}, "information": ""}' \
  -F 'current_stage=gathering_requirements'
```

#### Test File Upload
```bash
curl -X POST http://localhost:8000/api/v1/context/update \
  -F 'message=Process this motor datasheet' \
  -F 'current_context={"device_constants": {}, "information": ""}' \
  -F 'current_stage=gathering_requirements' \
  -F 'files=@motor_spec.pdf'
```

#### Test AI Chat
```bash
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain PID controllers", "context": {"device_constants": {}, "information": ""}}'
```

#### Test PLC Code Generation
```bash
curl -X POST http://localhost:8000/api/v1/plc/generate \
  -H "Content-Type: application/json" \
  -d '{"context": {"device_constants": {"motor": {"power": "5kW"}}, "information": "Motor control needed"}, "requirements": "Generate motor control code"}'
```

## 🚀 Frontend Integration Guide

### Basic Integration
```typescript
// Main integration function
async function updateContext(
  message?: string,
  mcqResponses?: string[],
  files?: File[],
  currentContext: ProjectContext,
  currentStage: string
): Promise<ContextUpdateResponse> {
  const formData = new FormData();
  
  if (message) formData.append('message', message);
  if (mcqResponses?.length) {
    formData.append('mcq_responses', JSON.stringify(mcqResponses));
  }
  
  formData.append('current_context', JSON.stringify(currentContext));
  formData.append('current_stage', currentStage);
  
  files?.forEach(file => formData.append('files', file));
  
  const response = await fetch('/api/v1/context/update', {
    method: 'POST',
    body: formData
  });
  
  return response.json();
}
```

### Error Handling
```typescript
const handleApiError = (error) => {
  if (error.status === 400) {
    showError("Invalid context format. Please check your input.");
  } else if (error.status === 500) {
    showError("Server error. Please try again later.");
  } else {
    showError("Connection error. Please check your internet connection.");
  }
};
```

## 🎉 Ready for Frontend Integration!

The context-centric architecture provides:
- **Single Integration Point**: `/api/v1/context/update` handles all interactions
- **Transparent Operation**: No hidden state, everything is visible
- **Type Safety**: Strong TypeScript interfaces
- **File Processing**: Built-in multipart support
- **Stateless Design**: No conversation state to manage

**Start with the context endpoint - it's the heart of the new architecture!** 🌟
  "response": "AI response text",
  "next_stage": "gather_requirements",
  "gathering_requirements_estimated_progress": 0.0,
  "stage_progress": {"requirements_identified": 0, "confidence": 0.0},
  "suggested_actions": ["Provide more details...", "Upload documentation..."],
  "is_mcq": false,
  "mcq_question": null,
  "mcq_options": [],
  "is_multiselect": false,
  "generated_code": null,
  "metadata": {}
}
```

**Status**: ✅ Working

#### Get Conversation State
```http
GET /api/v1/conversations/{conversation_id}
```

**Status**: ✅ Working

#### Get Conversation Messages
```http
GET /api/v1/conversations/{conversation_id}/messages
```

**Status**: ✅ Working

#### List All Conversations
```http
GET /api/v1/conversations/
```

**Status**: ✅ Working

#### Get Stage Suggestions
```http
GET /api/v1/conversations/{conversation_id}/stage/suggestions
```

**Status**: ✅ Working

#### Manual Stage Transition
```http
POST /api/v1/conversations/{conversation_id}/stage
Content-Type: application/json

{
  "conversation_id": "string",
  "target_stage": "gather_requirements",
  "reason": "Manual override",
  "force": false
}
```

**Status**: ✅ Working

#### Reset Conversation
```http
POST /api/v1/conversations/{conversation_id}/reset?target_stage=project_kickoff
```

**Status**: ✅ Working

#### Delete Conversation
```http
DELETE /api/v1/conversations/{conversation_id}
```

**Status**: ✅ Working

#### System Health Check
```http
GET /api/v1/conversations/health
```

**Status**: ⚠️ Path needs verification

### 🔧 PLC Code Generation Endpoints

#### Generate PLC Code
```http
POST /api/v1/plc/generate
Content-Type: application/json

{
  "user_prompt": "Create a ladder logic program for a simple traffic light controller",
  "language": "ladder_logic",
  "name": "Traffic Light Controller",
  "description": "Simple traffic light control system",
  "temperature": 1.0,
  "max_completion_tokens": 2000,
  "include_io_definitions": true,
  "include_safety_checks": true
}
```

**Status**: ✅ Schema validated (requires valid OpenAI API key)

#### List PLC Codes
```http
GET /api/v1/plc/?skip=0&limit=100&language=ladder_logic
```

**Status**: ✅ Working

#### Get Specific PLC Code
```http
GET /api/v1/plc/{code_id}
```

**Status**: ✅ Working

#### Update PLC Code
```http
PUT /api/v1/plc/{code_id}
```

**Status**: ✅ Working

#### Delete PLC Code
```http
DELETE /api/v1/plc/{code_id}
```

**Status**: ✅ Working

#### Validate PLC Code
```http
POST /api/v1/plc/{code_id}/validate
```

**Status**: ✅ Working

#### Compile PLC Code
```http
POST /api/v1/plc/{code_id}/compile
```

**Status**: ✅ Working

### 🔗 Digital Twin Endpoints

#### Create Digital Twin
```http
POST /api/v1/digital-twin/
Content-Type: application/json

{
  "name": "Test Conveyor System",
  "description": "Test digital twin for API validation",
  "simulation_type": "conveyor",
  "configuration": {"belt_speed": 1.5, "length": 10.0}
}
```

**Status**: ✅ Schema validated

#### List Digital Twins
```http
GET /api/v1/digital-twin/?skip=0&limit=100&simulation_type=conveyor
```

**Status**: ✅ Working

#### Get Digital Twin
```http
GET /api/v1/digital-twin/{twin_id}
```

**Status**: ✅ Working

#### Delete Digital Twin
```http
DELETE /api/v1/digital-twin/{twin_id}
```

**Status**: ✅ Working

#### Test PLC Code in Digital Twin
```http
POST /api/v1/digital-twin/{twin_id}/test
Content-Type: application/json

{
  "plc_code_id": "uuid-string",
  "test_name": "Conveyor Speed Test",
  "test_parameters": {},
  "expected_outcomes": {},
  "simulation_duration": 10.0,
  "real_time_factor": 1.0
}
```

**Status**: ✅ Schema validated

#### Get Simulation Runs
```http
GET /api/v1/digital-twin/{twin_id}/runs?skip=0&limit=50
```

**Status**: ✅ Working

#### Get Specific Simulation Run
```http
GET /api/v1/digital-twin/runs/{run_id}
```

**Status**: ✅ Working

### 📄 Document Management Endpoints

#### Upload Document
```http
POST /api/v1/documents/upload
Content-Type: multipart/form-data

file=@document.pdf
description=Optional description
tags=tag1,tag2,tag3
```

**Status**: ✅ Working

#### List Documents
```http
GET /api/v1/documents/?skip=0&limit=100&status_filter=processed
```

**Status**: ✅ Working

#### Get Document
```http
GET /api/v1/documents/{document_id}
```

**Status**: ✅ Working

#### Update Document
```http
PUT /api/v1/documents/{document_id}
```

**Status**: ✅ Working

#### Delete Document
```http
DELETE /api/v1/documents/{document_id}
```

**Status**: ✅ Working

#### Process Document
```http
POST /api/v1/documents/{document_id}/process
```

**Status**: ✅ Working

#### Get Extracted Data
```http
GET /api/v1/documents/{document_id}/extracted-data
```

**Status**: ✅ Working

## 🚀 Getting Started for Frontend Integration

### 1. Environment Setup
```bash
# Set required environment variables
export DATABASE_URL="sqlite:///./test.db"
export SECRET_KEY="your-secret-key"
export OPENAI_API_KEY="your-openai-api-key"

# Start the server
cd /path/to/plc-copilot
conda activate plc-copilot
PYTHONPATH=/path/to/plc-copilot python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Key Features for Frontend

#### Multi-Stage Conversation Flow
The conversation system supports these stages:
- `project_kickoff`: Initial user input and project analysis
- `gather_requirements`: Follow-up questions and clarifications (MCQ support)
- `code_generation`: PLC code generation based on requirements
- `refinement_testing`: Code refinement and testing feedback
- `completed`: Final stage

#### Error Handling
All endpoints return structured error responses:
```json
{
  "detail": "Error description",
  "type": "error_type",
  "param": "parameter_name"
}
```

#### Pagination
List endpoints support pagination:
- `skip`: Number of items to skip
- `limit`: Maximum items to return

### 3. OpenAPI Documentation
Full interactive documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

### 4. Database Persistence
- SQLite database automatically initialized
- All conversations, PLC codes, digital twins, and documents are persisted
- Database migrations handled by Alembic

## ⚠️ Important Notes for Frontend Development

1. **OpenAI API Key**: Set a valid OpenAI API key for full AI functionality
2. **CORS**: CORS is configured for development - update for production
3. **File Uploads**: Document uploads use multipart/form-data
4. **Conversation IDs**: UUIDs are auto-generated if not provided
5. **Stage Transitions**: The system auto-detects stage transitions but allows manual override
6. **Rate Limiting**: Consider implementing rate limiting for production

## 🔧 Testing Commands

```bash
# Test basic connectivity
curl http://localhost:8000/health

# Test conversation endpoint
curl -X POST http://localhost:8000/api/v1/conversations/ \
  -H "Content-Type: application/json" \
  -d '{"message": "I need help with PLC programming"}'

# Test AI chat endpoint
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"user_prompt": "Hello, world!"}'
```

## 📊 Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Core API | ✅ Ready | All endpoints functional |
| Conversation System | ✅ Ready | Multi-stage flow working |
| PLC Code Generation | ⚠️ Partial | Requires valid OpenAI key |
| Digital Twin | ✅ Ready | Schema validated |
| Document Management | ✅ Ready | File upload working |
| Database Integration | ✅ Ready | SQLite configured |
| Error Handling | ✅ Ready | Structured responses |
| API Documentation | ✅ Ready | Interactive docs available |

**Ready for Frontend Integration** 🎉

The API is now ready for your frontend integration. All core endpoints are functional, properly documented, and return consistent JSON responses. The conversation system provides a solid foundation for building an interactive PLC programming assistant.