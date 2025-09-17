# 🚀 Frontend Integration Guide: Context-Centric Architecture

## 📋 Overview

The PLC-Copilot backend has been **completely redesigned** with a **context-centric architecture** that replaces the legacy conversation system with a single, unified endpoint for all user interactions.

## 🌟 **Key Architectural Change**

**BEFORE**: Multiple endpoints, conversation state management, separate file uploads  
**NOW**: Single endpoint, transparent context, integrated file processing

## 🎯 **Core Workflow Stages**

The system follows a simple progression:

1. **`gathering_requirements`** - Collect project requirements with AI assistance
2. **`code_generation`** - Generate Structured Text PLC code 
3. **`refinement_testing`** - Refine and improve generated code

## 🔌 **THE Primary API Endpoint**

### **Context Update - The One Endpoint to Rule Them All**
```http
POST /api/v1/context/update
Content-Type: multipart/form-data

# Form fields:
message: "User message or response"
mcq_responses: ["Selected", "Options"]  # JSON array as string  
current_context: {"device_constants": {}, "information": ""}  # JSON as string
current_stage: "gathering_requirements"  # Current workflow stage
files: [file1.pdf, file2.pdf]  # Optional file uploads
```

**This single endpoint handles ALL user interactions:**
- ✅ **Text messages** and user responses  
- ✅ **Multiple choice question (MCQ)** answers
- ✅ **File uploads** with immediate PDF processing
- ✅ **Context updates** with AI-driven improvements
- ✅ **Stage management** and transitions
- ✅ **Progress tracking** during requirements gathering
- ✅ **Code generation** when ready

**Response Structure:**
```typescript
interface ContextUpdateResponse {
  updated_context: {
    device_constants: {
      [deviceName: string]: {
        [property: string]: string | number | object
      }
    };
    information: string; // Markdown format
  };
  chat_message: string;
  current_stage: 'gathering_requirements' | 'code_generation' | 'refinement_testing';
  progress?: number; // 0.0-1.0 during requirements gathering
  is_mcq: boolean;
  mcq_question?: string;
  mcq_options?: string[];
  is_multiselect?: boolean;
  generated_code?: string; // Structured Text when ready
}
```
---

## 🎯 **Frontend Implementation Guide**

### **1. Context Tab Implementation**
The most important UI component is the **context tab** that displays the project context:

```typescript
interface ProjectContext {
  device_constants: {
    [deviceName: string]: {
      [property: string]: string | number | object
    }
  };
  information: string; // Markdown format
}

// Example context display
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

### **2. Main Integration Function**
```typescript
async function updateContext(
  message?: string,
  mcqResponses?: string[],
  files?: File[],
  currentContext: ProjectContext,
  currentStage: string
): Promise<ContextUpdateResponse> {
  const formData = new FormData();
  
  // Add text fields
  if (message) formData.append('message', message);
  if (mcqResponses?.length) {
    formData.append('mcq_responses', JSON.stringify(mcqResponses));
  }
  
  // Add context and stage
  formData.append('current_context', JSON.stringify(currentContext));
  formData.append('current_stage', currentStage);
  
  // Add files
  files?.forEach(file => formData.append('files', file));
  
  const response = await fetch('/api/v1/context/update', {
    method: 'POST',
    body: formData
  });
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }
  
  return response.json();
}
```

### **3. Chat Interface with MCQ Support**
```typescript
const ChatInterface = ({ 
  context, 
  stage, 
  onContextUpdate 
}) => {
  const [messages, setMessages] = useState([]);
  const [currentMcq, setCurrentMcq] = useState(null);
  
  const handleUserMessage = async (message: string) => {
    try {
      const response = await updateContext(
        message, 
        null, 
        null, 
        context, 
        stage
      );
      
      // Update context
      onContextUpdate(response.updated_context, response.current_stage);
      
      // Add chat message
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.chat_message
      }]);
      
      // Handle MCQ
      if (response.is_mcq) {
        setCurrentMcq({
          question: response.mcq_question,
          options: response.mcq_options,
          multiselect: response.is_multiselect
        });
      } else {
        setCurrentMcq(null);
      }
      
    } catch (error) {
      console.error('Context update failed:', error);
    }
  };
  
  const handleMcqResponse = async (selectedOptions: string[]) => {
    try {
      const response = await updateContext(
        null,
        selectedOptions,
        null,
        context,
        stage
      );
      
      // Update state...
      setCurrentMcq(null);
      
    } catch (error) {
      console.error('MCQ response failed:', error);
    }
  };
  
  return (
    <div className="chat-interface">
      {/* Message history */}
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
      </div>
      
      {/* MCQ Display */}
      {currentMcq && (
        <McqComponent 
          question={currentMcq.question}
          options={currentMcq.options}
          multiselect={currentMcq.multiselect}
          onResponse={handleMcqResponse}
        />
      )}
      
      {/* Input area */}
      <MessageInput onSend={handleUserMessage} />
    </div>
  );
};
```

### **4. File Upload Integration**
```typescript
const FileUploader = ({ onFilesUploaded, context, stage }) => {
  const handleFileSelect = async (files: File[]) => {
    try {
      const response = await updateContext(
        "Please process these uploaded files",
        null,
        files,
        context,
        stage
      );
      
      onFilesUploaded(response);
      
    } catch (error) {
      console.error('File upload failed:', error);
    }
  };
  
  return (
    <div className="file-uploader">
      <input 
        type="file" 
        multiple 
        accept=".pdf"
        onChange={(e) => handleFileSelect(Array.from(e.target.files))}
      />
      {/* Or drag & drop interface */}
    </div>
  );
};
```

### **5. Progress Tracking**
```typescript
const ProgressTracker = ({ stage, progress }) => {
  const getStageIndex = (stage) => {
    const stages = ['gathering_requirements', 'code_generation', 'refinement_testing'];
    return stages.indexOf(stage);
  };
  
  return (
    <div className="progress-tracker">
      <div className="stage-indicator">
        Current Stage: {stage.replace('_', ' ').toUpperCase()}
      </div>
      
      {stage === 'gathering_requirements' && progress !== undefined && (
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress * 100}%` }} />
          <span>{Math.round(progress * 100)}% Complete</span>
        </div>
      )}
      
      <div className="stage-nav">
        <button onClick={() => changeStage('gathering_requirements')}>
          Requirements
        </button>
        <button onClick={() => changeStage('code_generation')}>
          Code Generation
        </button>
        <button onClick={() => changeStage('refinement_testing')}>
          Refinement
        </button>
      </div>
    </div>
  );
};
```

---

## 🚀 **Complete Example Application**

```typescript
const PLCCopilotApp = () => {
  const [context, setContext] = useState<ProjectContext>({
    device_constants: {},
    information: ""
  });
  const [stage, setStage] = useState('gathering_requirements');
  const [progress, setProgress] = useState(0);
  
  const handleContextUpdate = (newContext, newStage, newProgress = progress) => {
    setContext(newContext);
    setStage(newStage);
    setProgress(newProgress);
  };
  
  return (
    <div className="plc-copilot-app">
      {/* Main Layout */}
      <div className="main-layout">
        
        {/* Left Panel - Context Tab */}
        <div className="left-panel">
          <ContextTab 
            context={context}
            onContextEdit={setContext}
          />
        </div>
        
        {/* Center Panel - Chat Interface */}
        <div className="center-panel">
          <ProgressTracker stage={stage} progress={progress} />
          
          <ChatInterface 
            context={context}
            stage={stage}
            onContextUpdate={handleContextUpdate}
          />
          
          <FileUploader 
            context={context}
            stage={stage}
            onFilesUploaded={(response) => {
              handleContextUpdate(
                response.updated_context,
                response.current_stage,
                response.progress
              );
            }}
          />
        </div>
        
        {/* Right Panel - Code Display */}
        <div className="right-panel">
          <CodeDisplay context={context} stage={stage} />
        </div>
        
      </div>
    </div>
  );
};
```

---

## � **Testing & Development**

### **1. Environment Setup**
```bash
# Backend
export OPENAI_API_KEY="your-key"
export DATABASE_URL="sqlite:///./test.db"
uvicorn app.main:app --reload

# Frontend (example with React)
npm create react-app plc-copilot-frontend
cd plc-copilot-frontend
npm install
```

### **2. API Testing**
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
```

### **3. Error Handling**
```typescript
const handleApiError = (error) => {
  if (error.status === 400) {
    // Bad request - invalid context format
    showError("Invalid context format. Please check your input.");
  } else if (error.status === 500) {
    // Server error
    showError("Server error. Please try again later.");
  } else {
    // Network error
    showError("Connection error. Please check your internet connection.");
  }
};
```

---

## 📊 **Key Benefits of Context-Centric Architecture**

### **For Developers:**
1. **Single Integration Point**: Only one endpoint to integrate
2. **Stateless**: No conversation state to manage
3. **Type Safety**: Strong TypeScript interfaces 
4. **File Handling**: Built-in multipart support
5. **Error Handling**: Consistent error responses

### **For Users:**
1. **Transparency**: See exactly what the AI knows
2. **Control**: Edit context directly
3. **Efficiency**: File processing in single step
4. **Flexibility**: Jump between stages freely
5. **No Surprises**: No hidden conversation state

---

## 🎉 **Ready to Build!**

The context-centric architecture provides everything you need to build a powerful, transparent, and user-friendly PLC programming assistant. The single endpoint design makes integration straightforward while the transparent context makes the AI interaction completely debuggable.

**Start with the context tab - it's the heart of the new architecture!** �