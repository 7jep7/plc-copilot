# PLC-Copilot API: Context-Centric Architecture

## 📋 Executive Summary

✅ **API Server Status**: Running and functional on http://localhost:8000  
✅ **Database Configuration**: SQLite configured and initialized  
✅ **Core Endpoints**: Context-centric unified workflow  
⚠️ **OpenAI Integration**: Requires valid API key for full functionality  
📖 **Documentation**: Available at http://localhost:8000/docs  

## 🎯 **NEW ARCHITECTURE: Context-Centric Workflow**

**🌟 BREAKING CHANGE**: The conversation system has been completely replaced with a **unified context-centric API** that provides a single endpoint for all user interactions.

## 🔌 API Endpoints Ready for Frontend Integration

### Base Configuration
- **Base URL**: `http://localhost:8000`
- **API Prefix**: `/api/v1`
- **Content-Type**: `multipart/form-data` (for context updates with file support)

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

---

## 🌟 **PRIMARY API: Context-Centric Workflow**

### **The ONE Endpoint to Rule Them All**

#### Context Update (Unified Workflow)
```http
POST /api/v1/context/update
Content-Type: multipart/form-data

# Form fields:
message: "Your message or response"
mcq_responses: ["Selected", "Options"]  // JSON array as string
current_context: {"device_constants": {}, "information": ""}  // JSON as string
current_stage: "gathering_requirements"  // or "code_generation", "refinement_testing"
files: [file1.pdf, file2.pdf]  // Optional file uploads
```

**This single endpoint handles:**
- ✅ **Text messages** and user responses  
- ✅ **Multiple choice question (MCQ)** answers
- ✅ **File uploads** with immediate PDF processing
- ✅ **Stage management** and transitions
- ✅ **Context updates** with AI-driven improvements
- ✅ **Progress tracking** during requirements gathering
- ✅ **Code generation** when ready

**Example Response**:
```json
{
  "updated_context": {
    "device_constants": {
      "ConveyorMotor": {
        "Type": "AC Servo",
        "Power": "2.5kW",
        "Voltage": "400V"
      },
      "SafetySystems": {
        "EmergencyStops": {"Count": 2},
        "LightCurtains": {"Height": "1800mm"}
      }
    },
    "information": "## Project Requirements\n- Conveyor belt control system\n- Safety requirements: emergency stops\n- Speed control needed"
  },
  "chat_message": "Great! I've added the motor specifications. What safety features do you need?",
  "current_stage": "gathering_requirements",
  "progress": 0.6,
  "is_mcq": true,
  "mcq_question": "What safety features do you require?",
  "mcq_options": [
    "Emergency stop buttons only",
    "Light curtains for perimeter protection", 
    "Safety mats for operator zones",
    "Comprehensive safety package"
  ],
  "is_multiselect": false,
  "generated_code": null
}
```

---

## 🔧 **Utility Endpoints** (Optional/Specialized)

### 🤖 AI Chat (Simple Stateless)
```http
POST /api/v1/ai/chat
Content-Type: application/json

{
  "user_prompt": "Simple question about PLC programming",
  "model": "gpt-4o-mini",
  "temperature": 1.0,
  "max_completion_tokens": 512
}
```

**Use Case**: Simple Q&A without context tracking  
**Status**: ✅ Working (requires valid OpenAI API key)

### 🔧 PLC Code Generation (CRUD Operations)
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

**Use Case**: Direct PLC code generation and CRUD operations  
**Status**: ✅ Working (requires valid OpenAI API key)

**Additional PLC endpoints**: GET, PUT, DELETE `/api/v1/plc/{code_id}`, validation, compilation

### 🔗 Digital Twin Simulation
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

**Use Case**: PLC code testing and simulation  
**Status**: ✅ Working

### 📚 Code Library (Templates)
```http
GET /api/v1/library/
```

**Use Case**: Access to pre-built PLC code templates  
**Status**: ✅ Working

---

## 🎯 **Frontend Integration Guide**

### **Context Tab Implementation** 
Your frontend should implement a **context tab** that displays the current context in an editable format:

```typescript
interface ProjectContext {
  device_constants: {
    [deviceName: string]: {
      [property: string]: string | number | object
    }
  };
  information: string; // Markdown format
}

interface ContextState {
  context: ProjectContext;
  stage: 'gathering_requirements' | 'code_generation' | 'refinement_testing';
  progress?: number; // 0.0-1.0 during requirements gathering
  is_mcq: boolean;
  mcq_question?: string;
  mcq_options?: string[];
  is_multiselect?: boolean;
}
```

### **Recommended Workflow**
1. **Initialize**: Start with empty context and `gathering_requirements` stage
2. **Context Tab**: Show device_constants as JSON editor + information as markdown
3. **Chat Interface**: Regular chat with MCQ support
4. **File Upload**: Drag & drop PDF processing
5. **Progress Bar**: Show progress during requirements gathering
6. **Stage Transitions**: Automatic or user-controlled
7. **Code Display**: Show generated Structured Text when ready

### **Example Implementation**
```typescript
async function updateContext(
  message?: string,
  mcqResponses?: string[],
  files?: File[]
): Promise<ContextState> {
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

---

## 🚀 **Getting Started**

### 1. Environment Setup
```bash
# Set required environment variables
export DATABASE_URL="sqlite:///./test.db" 
export SECRET_KEY="your-secret-key"
export OPENAI_API_KEY="your-openai-api-key"

# Start the server
conda activate plc-copilot
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Key Features
- **🎯 Single endpoint** for all user interactions
- **📄 Immediate file processing** - no separate upload step
- **🤖 AI-driven context updates** - keeps information concise and relevant
- **📊 Progress tracking** - automatic requirements completion calculation
- **🔄 Stage management** - user can control workflow transitions
- **💬 MCQ support** - structured input collection

### 3. Testing the Context API
```bash
# Basic context update
curl -X POST http://localhost:8000/api/v1/context/update \
  -F 'message=I need help with a conveyor system' \
  -F 'current_context={"device_constants": {}, "information": ""}' \
  -F 'current_stage=gathering_requirements'

# With file upload
curl -X POST http://localhost:8000/api/v1/context/update \
  -F 'message=Process this motor datasheet' \
  -F 'current_context={"device_constants": {}, "information": ""}' \
  -F 'current_stage=gathering_requirements' \
  -F 'files=@motor_spec.pdf'

# MCQ response
curl -X POST http://localhost:8000/api/v1/context/update \
  -F 'mcq_responses=["Emergency stop buttons", "Light curtains"]' \
  -F 'current_context={"device_constants": {...}, "information": "..."}' \
  -F 'current_stage=gathering_requirements'
```

---

## 📊 **Status Summary**

| Component | Status | Purpose |
|-----------|--------|---------|
| **Context API** | ✅ **PRIMARY** | Unified workflow endpoint |
| AI Chat | ✅ Utility | Simple stateless chat |
| PLC CRUD | ✅ Utility | Code generation & management |
| Digital Twin | ✅ Utility | Simulation & testing |
| Code Library | ✅ Utility | Template access |
| Database | ✅ Ready | SQLite configured |
| Documentation | ✅ Ready | Interactive docs at `/docs` |

## 🎉 **Ready for Frontend Integration!**

The API is now **streamlined and focused** around the context-centric workflow. Your frontend can build a powerful, transparent, and user-friendly interface around the single `/api/v1/context/update` endpoint.

**Key Advantage**: Users can see and edit their context directly, making the AI interaction completely transparent and debuggable! 🌟