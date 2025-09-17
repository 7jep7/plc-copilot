# Conversation-Level Document Integration

This document describes the new conversation-level document integration feature that allows users to upload and process PDF documents directly within conversations, providing contextual information throughout the multi-stage conversation workflow.

## Overview

The conversation-level document integration provides:

1. **Stateless Document Processing**: PDF parsing and analysis without database dependencies
2. **Conversation Context Storage**: Documents stored directly in conversation memory
3. **Multi-Stage Context Usage**: Document context available in all conversation stages
4. **Intelligent Content Analysis**: OpenAI-powered analysis of documents for PLC context
5. **Duplicate Detection**: Prevents re-processing of identical documents
6. **Proactive Suggestions**: AI suggests document uploads when helpful

## Architecture

### Components

1. **ConversationDocumentService** (`app/services/conversation_document_service.py`)
   - Stateless PDF processing and analysis
   - Content extraction using multiple PDF parsing methods
   - Device information extraction
   - OpenAI-powered PLC context analysis
   - Content-based deduplication

2. **Enhanced ConversationState** (`app/schemas/conversation.py`)
   - Added `extracted_documents` field for in-memory document storage
   - Maintains backward compatibility with existing `document_ids` field

3. **Document API Endpoints** (`app/api/api_v1/endpoints/conversations.py`)
   - Upload documents to conversations
   - List conversation documents
   - Retrieve specific documents
   - Remove documents from conversations

4. **Enhanced Prompt Templates** (`app/services/prompt_templates.py`)
   - Intelligent document context integration
   - Stage-specific document information inclusion
   - Automatic document upload suggestions

## API Endpoints

### Upload Document to Conversation
```http
POST /api/v1/conversations/{conversation_id}/documents/upload
Content-Type: multipart/form-data

file: PDF file
analyze_with_openai: boolean (default: true)
```

**Response:**
```json
{
  "status": "uploaded",
  "document": {
    "filename": "camera_datasheet.pdf",
    "content_hash": "sha256_hash",
    "document_type": "DATASHEET",
    "device_info": {"manufacturer": "Cognex", "model": "In-Sight"},
    "plc_analysis": {...},
    "file_size": 1024576,
    "raw_text": "extracted text content..."
  },
  "conversation_id": "uuid",
  "total_documents": 1
}
```

### List Conversation Documents
```http
GET /api/v1/conversations/{conversation_id}/documents
```

**Response:**
```json
{
  "conversation_id": "uuid",
  "documents": [
    {
      "filename": "camera_datasheet.pdf",
      "content_hash": "sha256_hash",
      "document_type": "DATASHEET",
      "device_info": {"manufacturer": "Cognex"},
      "file_size": 1024576,
      "has_plc_analysis": true,
      "content_length": 15000
    }
  ],
  "total_count": 1
}
```

### Get Specific Document
```http
GET /api/v1/conversations/{conversation_id}/documents/{content_hash}
```

### Remove Document
```http
DELETE /api/v1/conversations/{conversation_id}/documents/{content_hash}
```

## Document Processing Features

### PDF Text Extraction
Multiple extraction methods for robust text recovery:
1. **pdfplumber** - Best for tables and structured content
2. **PyMuPDF (fitz)** - Good for complex layouts  
3. **PyPDF2** - Fallback method

### Document Classification
Automatic classification based on content keywords:
- **MANUAL** - User guides, operation manuals
- **DATASHEET** - Technical datasheets, specifications
- **SPECIFICATION** - Requirements, standards documents
- **DRAWING** - Schematics, diagrams, blueprints
- **UNKNOWN** - Unclassified documents

### Device Information Extraction
Automatic extraction of:
- Manufacturer names (Siemens, Allen-Bradley, Cognex, etc.)
- Model numbers and part numbers
- Device series information

### PLC Context Analysis
OpenAI-powered analysis extracting:
- Key technical specifications
- I/O requirements
- PLC integration points
- Technical parameters
- Safety considerations

## Conversation Stage Integration

### Project Kickoff Stage
- Document context included in requirements analysis
- Proactive document upload suggestions
- Device information referenced in initial assessment

### Gather Requirements Stage  
- Technical specifications from documents inform questions
- Avoids asking for information already in documents
- I/O requirements and device details guide inquiries

### Code Generation Stage
- Device-specific parameters used in code generation
- Technical specifications ensure accuracy
- Integration points guide PLC code structure

### Refinement Testing Stage
- Document constraints validate code modifications
- Device specifications guide testing requirements
- Technical parameters ensure compliance

## Usage Examples

### Frontend Integration

```typescript
// Upload document to conversation
const uploadDocument = async (conversationId: string, file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('analyze_with_openai', 'true');
  
  const response = await fetch(`/api/v1/conversations/${conversationId}/documents/upload`, {
    method: 'POST',
    body: formData
  });
  
  return await response.json();
};

// Continue conversation with document context
const continueConversation = async (conversationId: string, message: string) => {
  const response = await fetch('/api/v1/conversations/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      conversation_id: conversationId,
      message: message
    })
  });
  
  return await response.json();
};
```

### Backend Usage

```python
from app.services.conversation_document_service import ConversationDocumentService
from app.services.conversation_orchestrator import ConversationOrchestrator

# Process document
doc_service = ConversationDocumentService()
doc_info = await doc_service.process_uploaded_document(uploaded_file)

# Add to conversation
orchestrator = ConversationOrchestrator()
conversation = orchestrator.get_conversation(conversation_id)
conversation.extracted_documents.append(doc_info.to_dict())

# Continue conversation with document context
response = await orchestrator.process_message(ConversationRequest(
    conversation_id=conversation_id,
    message="Generate code for the camera system"
))
```

## Benefits

### For Users
1. **Seamless Integration**: Upload documents directly in conversation flow
2. **Context Persistence**: Document information available throughout conversation
3. **Intelligent Questions**: AI asks better questions with document context
4. **Accurate Code**: Generated code uses specific device parameters

### For Developers
1. **No Database Dependencies**: Stateless processing for MVP
2. **Flexible Storage**: Documents stored in conversation memory
3. **Easy Testing**: Simple test workflows without database setup
4. **Clean Architecture**: Separation of concerns between services

### For System Performance
1. **Efficient Parsing**: Multiple PDF extraction methods ensure content recovery
2. **Duplicate Prevention**: Hash-based deduplication avoids reprocessing
3. **Memory Management**: Documents cleaned up with conversation lifecycle
4. **Scalable Design**: Ready for future database integration

## Testing

Run the comprehensive integration test:

```bash
python tests/integration/test_conversation_document_integration.py [path_to_pdf]
```

This test verifies:
- Document upload and processing
- Conversation context integration
- Multi-stage document usage
- Duplicate detection
- Prompt template enhancement
- End-to-end workflow

## Migration Path

This implementation provides a clear migration path for future enhancements:

1. **Current (MVP)**: In-memory document storage in conversations
2. **Phase 2**: Optional database persistence with conversation linking
3. **Phase 3**: Document versioning and history tracking
4. **Phase 4**: Advanced document analysis and cross-referencing

The current design maintains full compatibility for future database integration while providing immediate value for the MVP.