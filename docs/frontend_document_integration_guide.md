# Frontend Integration Guide: Document Upload API

This guide covers the conversation-level document upload API endpoints for integrating PDF document management into the PLC-Copilot frontend.

## Overview

Upload PDF documents (datasheets, manuals, specifications) directly to conversations. Documents are automatically processed and used to enhance AI responses throughout the conversation lifecycle.

## API Endpoints

### 1. Upload Document to Conversation

**Endpoint**: `POST /api/v1/conversations/{conversation_id}/documents/upload`

**Content-Type**: `multipart/form-data`

**Parameters**:
- `file`: PDF file (required)
- `analyze_with_openai`: boolean (optional, default: true)

**Response on Success (200)**:
```json
{
  "status": "uploaded",
  "document": {
    "filename": "camera_datasheet.pdf",
    "content_hash": "a1b2c3d4e5f6...",
    "document_type": "DATASHEET",
    "device_info": {
      "manufacturer": "Cognex",
      "model": "In-Sight-7000"
    },
    "plc_analysis": {
      "key_specifications": ["1920x1080 resolution", "Ethernet connectivity"],
      "io_requirements": ["Digital outputs", "Trigger input"],
      "plc_integration_points": ["I/O module connection", "Network integration"]
    },
    "file_size": 1048576,
    "content_length": 15420
  },
  "conversation_id": "uuid-string",
  "total_documents": 1
}
```

**Response on Duplicate (200)**:
```json
{
  "status": "duplicate", 
  "message": "Document 'camera_datasheet.pdf' with identical content already exists in this conversation",
  "document": { /* existing document data */ }
}
```

**Error Responses**:
- `400`: Invalid file type (only PDF allowed)
- `404`: Conversation not found
- `500`: Processing failed

### 2. List Conversation Documents

**Endpoint**: `GET /api/v1/conversations/{conversation_id}/documents`

**Response**:
```json
{
  "conversation_id": "uuid-string",
  "documents": [
    {
      "filename": "camera_datasheet.pdf",
      "content_hash": "a1b2c3d4e5f6...",
      "document_type": "DATASHEET",
      "device_info": {"manufacturer": "Cognex", "model": "In-Sight-7000"},
      "file_size": 1048576,
      "has_plc_analysis": true,
      "content_length": 15420
    }
  ],
  "total_count": 1
}
```

### 3. Get Specific Document Details

**Endpoint**: `GET /api/v1/conversations/{conversation_id}/documents/{content_hash}`

**Response**:
```json
{
  "conversation_id": "uuid-string",
  "document": {
    "filename": "camera_datasheet.pdf",
    "content_hash": "a1b2c3d4e5f6...",
    "document_type": "DATASHEET",
    "device_info": {"manufacturer": "Cognex", "model": "In-Sight-7000"},
    "plc_analysis": {
      "key_specifications": ["1920x1080 resolution"],
      "io_requirements": ["Digital outputs"],
      "plc_integration_points": ["I/O module connection"]
    },
    "raw_text": "Complete extracted text content...",
    "file_size": 1048576
  }
}
```

### 4. Remove Document from Conversation

**Endpoint**: `DELETE /api/v1/conversations/{conversation_id}/documents/{content_hash}`

**Response**:
```json
{
  "status": "removed",
  "conversation_id": "uuid-string", 
  "remaining_documents": 0
}
```

## JavaScript Implementation Example

```javascript
// Upload document
const uploadDocument = async (conversationId, file) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('analyze_with_openai', 'true');

  const response = await fetch(`/api/v1/conversations/${conversationId}/documents/upload`, {
    method: 'POST',
    body: formData,
  });

  return await response.json();
};

// List documents
const listDocuments = async (conversationId) => {
  const response = await fetch(`/api/v1/conversations/${conversationId}/documents`);
  const data = await response.json();
  return data.documents;
};

// Remove document
const removeDocument = async (conversationId, contentHash) => {
  await fetch(`/api/v1/conversations/${conversationId}/documents/${contentHash}`, {
    method: 'DELETE'
  });
};
```

## Document Types

- **DATASHEET** - Technical datasheets, specifications
- **MANUAL** - User guides, operation manuals  
- **SPECIFICATION** - Requirements, standards documents
- **DRAWING** - Schematics, diagrams, blueprints
- **UNKNOWN** - Unclassified documents

## Validation Rules

- **File Type**: Only PDF files allowed
- **File Size**: Recommended max 10MB
- **Duplicate Detection**: Based on content hash (SHA256)

## Testing

```bash
# Upload document
curl -X POST \
  "http://localhost:8000/api/v1/conversations/{conversation_id}/documents/upload" \
  -F "file=@datasheet.pdf"

# List documents
curl "http://localhost:8000/api/v1/conversations/{conversation_id}/documents"

# Remove document  
curl -X DELETE \
  "http://localhost:8000/api/v1/conversations/{conversation_id}/documents/{content_hash}"
```