# API Integration Guide

Quick reference for integrating with the PLC Copilot API.

## Base URL

```
http://localhost:8001/api/v1
```

## Authentication

No authentication required for development. Include OpenAI API key in backend configuration.

## Main Endpoint

### POST /context/update

Primary endpoint for all interactions.

**Request Format:**
```javascript
const formData = new FormData();
formData.append('session_id', crypto.randomUUID());
formData.append('current_context', JSON.stringify(context));
formData.append('current_stage', 'gathering_requirements');
formData.append('message', 'User message');
// Optional: files
files.forEach(file => formData.append('files', file));
```

**Response Format:**
```json
{
    "updated_context": { "device_constants": {}, "information": "..." },
    "chat_message": "Assistant response",
    "session_id": "uuid",
    "is_mcq": false,
    "mcq_question": null,
    "mcq_options": [],
    "is_multiselect": false,
    "generated_code": null,
    "current_stage": "gathering_requirements",
    "gathering_requirements_estimated_progress": 0.5
}
```

## Session Management

### Session Lifecycle
1. Generate UUID with `crypto.randomUUID()`
2. Include in all requests as `session_id`
3. Clean up with `/context/cleanup`

### POST /context/cleanup
```json
{
    "session_ids": ["uuid1", "uuid2"]
}
```

### GET /context/sessions/stats
Monitor active sessions and resource usage.

## Error Handling

- `200`: Success
- `413`: File too large (>50MB)
- `415`: Unsupported file type
- `500`: Server error

## File Uploads

Supported formats: PDF, TXT, DOC, DOCX
Max size: 50MB per file
Include in same FormData as other parameters.

## Complete Example

```javascript
class PLCCopilotClient {
    constructor(baseUrl = 'http://localhost:8001/api/v1') {
        this.baseUrl = baseUrl;
        this.sessionId = crypto.randomUUID();
    }
    
    async sendMessage(message, context, files = []) {
        const formData = new FormData();
        formData.append('session_id', this.sessionId);
        formData.append('current_context', JSON.stringify(context));
        formData.append('current_stage', 'gathering_requirements');
        formData.append('message', message);
        
        files.forEach(file => formData.append('files', file));
        
        const response = await fetch(`${this.baseUrl}/context/update`, {
            method: 'POST',
            body: formData
        });
        
        return await response.json();
    }
    
    async cleanup() {
        await fetch(`${this.baseUrl}/context/cleanup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_ids: [this.sessionId] })
        });
    }
}
```