# 🚀 Frontend Quick Start Guide

## One Endpoint. One Context. That's It.

### Main API Endpoint
```typescript
POST /api/v1/context/update
Content-Type: multipart/form-data
```

### Basic Usage
```typescript
const updateContext = async (
  message?: string,
  files?: File[],
  context: ProjectContext,
  stage: string,
  mcqResponses?: string[],
  previousCopilotMessage?: string
) => {
  const formData = new FormData();
  
  if (message) formData.append('message', message);
  if (mcqResponses?.length) {
    formData.append('mcq_responses', JSON.stringify(mcqResponses));
  }
  if (previousCopilotMessage) {
    formData.append('previous_copilot_message', previousCopilotMessage);
  }
  files?.forEach(file => formData.append('files', file));
  formData.append('current_context', JSON.stringify(context));
  formData.append('current_stage', stage);
  
  const response = await fetch('/api/v1/context/update', {
    method: 'POST',
    body: formData
  });
  
  return response.json();
};
```

### Context Structure
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

### Response Format
```typescript
interface ContextUpdateResponse {
  updated_context: ProjectContext;
  chat_message: string;
  current_stage: 'gathering_requirements' | 'code_generation' | 'refinement_testing';
  progress?: number; // 0.0-1.0 during requirements gathering
  is_mcq: boolean;
  mcq_question?: string;
  mcq_options?: string[];
  is_multiselect?: boolean;
  generated_code?: string; // Only present during code generation
}
```

### Stages
1. **`gathering_requirements`** - Ask questions, upload files, build context
2. **`code_generation`** - Generate PLC code from context  
3. **`refinement_testing`** - Iterate and improve

### Example Flow
```typescript
// 1. Start with empty context
let context = { device_constants: {}, information: "" };
let stage = "gathering_requirements";
let lastCopilotMessage = null;

// 2. User uploads motor datasheet
const response1 = await updateContext(
  "Analyze this motor datasheet", 
  [motorFile], 
  context, 
  stage
);

// 3. Context now has motor specs, AI asks MCQ
context = response1.updated_context;
lastCopilotMessage = response1.chat_message; // Store for continuity
if (response1.is_mcq) {
  // Show MCQ to user
}

// 4. User answers MCQ with conversation context
const response2 = await updateContext(
  null, // No message, just MCQ response
  null, 
  context, 
  stage,
  ["Option A"], // MCQ responses
  lastCopilotMessage // Previous AI message for context
);

// 5. Continue until ready for code generation
lastCopilotMessage = response2.chat_message;
if (response2.progress >= 0.8) {
  stage = "code_generation";
  const codeResponse = await updateContext(
    "Generate the PLC code",
    null,
    context,
    stage,
    null,
    lastCopilotMessage
  );
  // codeResponse.generated_code contains the ST code
}
```

### That's It! 
- One endpoint handles everything: chat, files, MCQs, code generation
- Context is always visible and editable  
- No conversation IDs or hidden state
- Files processed immediately, no storage needed

**Full docs at:** http://localhost:8000/docs