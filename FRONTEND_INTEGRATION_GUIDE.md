# 🚀 Backend API Integration Guide: Context-Centric Architecture

## 📋 Overview

The PLC-Copilot backend has been completely refactored to use a **context-centric architecture** that provides transparent, stateless operation with a unified workflow. This guide shows you how to integrate with the new streamlined API.

## 🎯 Key Benefits

### **For Developers:**
- **Single Integration Point**: Only one endpoint to integrate
- **Stateless**: No conversation state to manage  
- **Type Safety**: Strong TypeScript interfaces
- **File Handling**: Built-in multipart support

### **For Users:**
- **Transparency**: See exactly what the AI knows
- **Control**: Edit context directly
- **Efficiency**: File processing in single step
- **No Hidden State**: Everything is visible and editable

## 🔌 Primary API Endpoints

### 1. Context Update (Main Endpoint)
```http
POST /api/v1/context/update
Content-Type: multipart/form-data

message=I need help with a conveyor system          # Optional user message
mcq_responses=["Option A", "Option B"]               # Optional MCQ responses (JSON array)
files=@motor_spec.pdf                               # Optional file uploads
# 🚀 Backend API Integration Guide: Context-Centric Architecture

## 📋 Overview

The PLC-Copilot backend has been completely refactored to use a **context-centric architecture** that provides transparent, stateless operation with a unified workflow. This guide shows you how to integrate with the new streamlined API.

## 🎯 Key Benefits

### **For Developers:**
- **Single Integration Point**: Only one endpoint to integrate
- **Stateless**: No conversation state to manage  
- **Type Safety**: Strong TypeScript interfaces
- **File Handling**: Built-in multipart support

### **For Users:**
- **Transparency**: See exactly what the AI knows
- **Control**: Edit context directly
- **Efficiency**: File processing in single step
- **No Hidden State**: Everything is visible and editable

## 🔌 Primary API Endpoints

### 1. Context Update (Main Endpoint)
```http
POST /api/v1/context/update
Content-Type: multipart/form-data

message=I need help with a conveyor system          # Optional user message
mcq_responses=["Option A", "Option B"]               # Optional MCQ responses (JSON array)
files=@motor_spec.pdf                               # Optional file uploads
current_context={"device_constants": {}, "information": ""}  # Required current context (JSON)
current_stage=gathering_requirements                # Required current stage
```

**Response:**
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

### 2. Direct AI Chat (Stateless)
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

### 3. PLC Code Endpoints
```http
GET /api/v1/plc/codes              # List all generated codes
POST /api/v1/plc/codes             # Create new code
GET /api/v1/plc/codes/{id}         # Get specific code
PUT /api/v1/plc/codes/{id}         # Update code
DELETE /api/v1/plc/codes/{id}      # Delete code
POST /api/v1/plc/generate          # Generate new code
```

### 4. Digital Twin Management
```http
GET /api/v1/digital-twin/configs    # List twin configurations
POST /api/v1/digital-twin/configs   # Create twin config
POST /api/v1/digital-twin/simulate  # Run simulation
```

### 5. Code Library
```http
GET /api/v1/library/examples        # Browse code examples
POST /api/v1/library/search         # Search code library
```

## 🎯 Context-Centric Workflow

### Project Context Structure
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

## 🎮 Frontend Implementation

### Basic Integration
```typescript
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

### Context Display Component
```typescript
const ContextTab = ({ context, onContextEdit }) => {
  return (
    <div className="context-tab">
      <h3>Project Context</h3>
      
      {/* Device Constants - JSON Editor */}
      <section>
        <h4>Device Constants</h4>
        <JsonEditor 
          value={context.device_constants}
          onChange={(newConstants) => onContextEdit({
            ...context, 
            device_constants: newConstants
          })}
        />
      </section>
      
      {/* Information - Markdown Editor */}
      <section>
        <h4>Project Information</h4>
        <MarkdownEditor
          value={context.information}
          onChange={(newInfo) => onContextEdit({
            ...context,
            information: newInfo
          })}
        />
      </section>
    </div>
  );
};
```

### MCQ Handling
```typescript
const ChatInterface = ({ context, stage, onContextUpdate }) => {
  const [currentMcq, setCurrentMcq] = useState(null);
  
  const handleUserMessage = async (message: string) => {
    const response = await updateContext(message, null, null, context, stage);
    
    onContextUpdate(response.updated_context, response.current_stage);
    
    if (response.is_mcq) {
      setCurrentMcq({
        question: response.mcq_question,
        options: response.mcq_options,
        multiselect: response.is_multiselect
      });
    }
  };
  
  const handleMcqResponse = async (selectedOptions: string[]) => {
    const response = await updateContext(null, selectedOptions, null, context, stage);
    setCurrentMcq(null);
    onContextUpdate(response.updated_context, response.current_stage);
  };
  
  return (
    <div className="chat-interface">
      {currentMcq && (
        <McqComponent 
          question={currentMcq.question}
          options={currentMcq.options}
          multiselect={currentMcq.multiselect}
          onResponse={handleMcqResponse}
        />
      )}
      <MessageInput onSend={handleUserMessage} />
    </div>
  );
};
```

## 🧪 Testing

### Environment Setup
```bash
export OPENAI_API_KEY="your-key"
export DATABASE_URL="sqlite:///./test.db"
uvicorn app.main:app --reload
```

### API Testing
```bash
# Test basic context update
curl -X POST http://localhost:8000/api/v1/context/update \
  -F 'message=I need help with a conveyor system' \
  -F 'current_context={"device_constants": {}, "information": ""}' \
  -F 'current_stage=gathering_requirements'

# Test file upload
curl -X POST http://localhost:8000/api/v1/context/update \
  -F 'message=Process this motor datasheet' \
  -F 'current_context={"device_constants": {}, "information": ""}' \
  -F 'current_stage=gathering_requirements' \
  -F 'files=@motor_spec.pdf'

# Test direct AI chat
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain PID controllers", "context": {"device_constants": {}, "information": ""}}'
```

## 🎉 Key Advantages

### Architecture Benefits
1. **Transparent Operation**: Users can see and edit exactly what the AI knows
2. **Stateless Design**: No hidden conversation state to debug
3. **Single Integration Point**: One endpoint handles all interactions
4. **File Processing**: Documents processed immediately, not stored
5. **Type Safety**: Strong interfaces for reliable integration

### User Experience
1. **No Surprises**: Context is always visible and editable
2. **Direct Control**: Jump between stages freely
3. **Efficient**: File uploads processed in single step
4. **Debuggable**: No hidden state makes troubleshooting easy

## 🚀 Ready to Build!

The context-centric architecture provides everything you need to build a powerful, transparent, and user-friendly PLC programming assistant. Start with the context tab - it's the heart of the new architecture! 🌟
```

**Response:**
```json
{
  "conversation_id": "uuid-string",
  "stage": "project_kickoff",
  "response": "I'll help you design a conveyor belt control system. Let me start by understanding your specific requirements...",
  "next_stage": "gather_requirements",
  "gathering_requirements_estimated_progress": 0.0,
  "stage_progress": {
    "requirements_identified": 0,
    "confidence": 0.8
  },
  "suggested_actions": [
    "Provide more details about your conveyor specifications",
    "Upload any existing documentation"
  ],
  "is_mcq": false,
  "mcq_question": null,
  "mcq_options": [],
  "is_multiselect": false,
  "generated_code": null,
  "metadata": {
    "tokens_used": 150,
    "processing_time": 2.3
  },
  "is_mcq": false,
  "mcq_question": null,
  "mcq_options": [],
  "is_multiselect": false,
  "generated_code": null
}
```

### 2. Get Conversation State
```http
GET /api/v1/conversations/{conversation_id}
```

**Response:**
```json
{
  "conversation_id": "uuid-string",
  "current_stage": "gather_requirements",
  "created_at": "2025-09-16T07:00:00Z",
  "updated_at": "2025-09-16T07:05:00Z",
  "gathering_requirements_estimated_progress": 0.4,
  "project_context": {
    "project_type": "conveyor_control",
    "requirements": ["emergency_stop", "variable_speed"],
    "generated_code": null
  },
  "messages": [
    {
      "role": "user",
      "content": "I need help with a conveyor belt...",
      "timestamp": "2025-09-16T07:00:00Z"
    },
    {
      "role": "assistant", 
      "content": "I'll help you design...",
      "timestamp": "2025-09-16T07:00:15Z"
    }
  ]
}
```

### 3. Force Stage Transition
```http
POST /api/v1/conversations/{conversation_id}/stage
Content-Type: application/json

{
  "target_stage": "gather_requirements",
  "reason": "User wants to add more requirements",
  "force": false
}
```

**Response:**
```json
{
  "success": true,
  "previous_stage": "project_kickoff",
  "new_stage": "gather_requirements",
  "message": "Stage transition completed successfully"
}
```

### 4. Reset Conversation
```http
POST /api/v1/conversations/{conversation_id}/reset?target_stage=project_kickoff
```

### 5. Delete Conversation
```http
DELETE /api/v1/conversations/{conversation_id}
```

## 🎯 MCQ (Multiple Choice Question) Functionality

### Structured MCQ Response Format

The system now provides structured MCQ data in the API response for easier frontend integration:

**Example MCQ Response (Focused Requirements Gathering):**
```json
{
  "conversation_id": "uuid-string",
  "stage": "gather_requirements", 
  "response": "What safety features do you require for your conveyor system?",
  "next_stage": "gather_requirements",
  "gathering_requirements_estimated_progress": 0.3,
  "suggested_actions": [
    "Select your required safety features from the options below"
  ],
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

### ⚠️ Important: MCQ Field Usage for Frontend

**CRITICAL**: When `is_mcq` is true, display ONLY the `mcq_question` and `mcq_options` to the user for interaction. The `response` field contains additional context but should not overwhelm the user interface.

**Best Practice MCQ Handling:**

```typescript
// ✅ CORRECT: Use structured MCQ fields for user interaction
const handleApiResponse = (response: ConversationResponse) => {
  if (response.is_mcq) {
    // Display ONLY the focused MCQ question and options
    displayFocusedMCQ({
      question: response.mcq_question,
      options: response.mcq_options
    });
    
    // Optional: Show response context in a collapsible section
    displayContextualInfo(response.response, { collapsible: true });
  } else {
    // Display regular response
    displayRegularResponse(response.response);
  }
};

// ✅ Focused MCQ component - keeps user experience clean
const renderFocusedMCQ = (question: string, options: string[]) => {
  return (
    <div className="mcq-container">
      <h3 className="mcq-question">{question}</h3>
      <div className="mcq-options">
        {options.map((option, index) => (
          <button 
        ))}
      </div>
    </div>
  );
};

// ❌ AVOID: Don't overwhelm users with complex MCQ + full response
const avoidComplexMCQDisplay = (response) => {
  // This creates cognitive overload for users
  return `${response.response}\n\nQuestion: ${response.mcq_question}...`;
};
```

### User Experience Principles

1. **Single Focus**: Each `gather_requirements` response contains exactly one focused question
2. **Clean Interface**: MCQ questions stand alone without competing text 
3. **Progressive Disclosure**: Additional context available but not forced on user
4. **Clear Action**: Users know exactly what to do next

### MCQ Response Format

When responding to MCQ questions, send the selected option:

```http
POST /api/v1/conversations/
Content-Type: application/json

{
  "message": "Comprehensive safety package (all features)",
  "conversation_id": "existing-uuid"
}
```

### MCQ Detection Rules

- **MCQ Trigger**: Only in `gather_requirements` stage
- **Format**: Uses `**MCQ_START**` and `**MCQ_END**` markers for reliable parsing
- **Limitation**: Maximum one MCQ per response for clarity
- **Options**: Labeled with A), B), C), D) format

## 📊 Stage-Specific Behavior

### Stage 1: Project Kickoff
- **Purpose**: Initial project analysis
- **Behavior**: Analyzes user requirements and suggests next steps
- **Auto-transition**: Usually transitions to `gather_requirements`

**Example Request:**
```json
{
  "message": "I need help designing a conveyor belt control system for a manufacturing line"
}
```

### Stage 2: Gather Requirements  
- **Purpose**: Technical clarification with MCQ support
- **Behavior**: Asks targeted questions, uses MCQ for standardized choices
- **MCQ Topics**: Safety features, voltages, communication protocols, etc.

**Example MCQ Response Pattern:**
```
What communication protocol do you prefer?
**Options**:
A) Modbus RTU
B) Ethernet/IP  
C) Profinet
D) No specific preference
```

### Stage 3: Code Generation
- **Purpose**: Generate PLC code based on requirements
- **Behavior**: Creates structured text (ST) code with comments
- **Output**: Complete PLC program with I/O definitions

**Example Request:**
```json
{
  "message": "Generate the PLC code based on our requirements",
  "force_stage": "code_generation"
}
```

### Stage 4: Refinement & Testing
- **Purpose**: Code modifications and testing feedback
- **Behavior**: Iterative improvements based on user feedback
- **Features**: Code review, optimization suggestions, testing scenarios

## 🔧 API Features

### Intelligent Stage Detection
- Automatic stage progression based on conversation context
- Confidence scoring for stage transitions
- Manual override capability with `force_stage`

### File Attachments Support
```http
POST /api/v1/conversations/
Content-Type: multipart/form-data

message: "Please analyze this PLC documentation"
file: [attached PDF/document]
conversation_id: "existing-uuid"
```

### Error Handling
All endpoints return structured error responses:
```json
{
  "detail": "Error description",
  "error_code": "INVALID_STAGE_TRANSITION", 
  "suggestions": ["Try transitioning to gather_requirements first"]
}
```

### Rate Limiting & Cost Optimization
- Environment-based model selection
- Token limit optimization for development
- Built-in rate limiting protection

## 💰 Environment Configuration

### Development Environment
```bash
export ENVIRONMENT=development
# Uses gpt-4o-mini for cost efficiency
```

### Testing Environment  
```bash
export TESTING=true
# Uses gpt-4o-mini with reduced token limits (~80% cost reduction)
```

### Production Environment
```bash
export ENVIRONMENT=production  
# Uses gpt-4o for document analysis, gpt-4o-mini for conversations
```

## 🧪 Testing Endpoints

### Cost-Efficient Testing
```bash
# Run efficient test suite
TESTING=true python scripts/test_4_stage_system_efficient.py

# Test MCQ functionality specifically
TESTING=true python scripts/test_mcq.py
```

### Full API Testing
```bash
# Test all endpoints
python scripts/test_all_endpoints.py

# Test 4-stage system comprehensively  
python scripts/test_4_stage_system.py
```

## 📝 Integration Checklist

### Basic Integration
1. **✅ Implement conversation start** - POST to `/api/v1/conversations/`
2. **✅ Handle stage progression** - Parse `stage` and `next_stage` fields
3. **✅ Display AI responses** - Render `response` field (supports Markdown)
4. **✅ Show suggested actions** - Present `suggested_actions` array

### Advanced Features  
5. **✅ MCQ detection** - Check `is_mcq` boolean field
6. **✅ MCQ rendering** - Use `mcq_question` and `mcq_options` for structured display
7. **✅ Stage forcing** - Allow manual stage transitions
8. **✅ File uploads** - Support document attachments
9. **✅ Conversation state** - Retrieve and display conversation history
10. **✅ Error handling** - Handle API errors gracefully
11. **✅ Cost optimization** - Set appropriate environment variables

## 🚀 Quick Start

1. **Start new conversation:**
```bash
curl -X POST "http://localhost:8000/api/v1/conversations/" \
  -H "Content-Type: application/json" \
  -d '{"message": "I need help with PLC programming"}'
```

2. **Continue conversation:**
```bash
curl -X POST "http://localhost:8000/api/v1/conversations/" \
  -H "Content-Type: application/json" \
  -d '{"message": "I need emergency stop functionality", "conversation_id": "uuid-from-step-1"}'
```

3. **Get conversation state:**
```bash
curl -X GET "http://localhost:8000/api/v1/conversations/{conversation_id}"
```

---

The backend is **production-ready** with comprehensive 4-stage conversation support, intelligent MCQ handling, and cost-optimized operation! 🎉