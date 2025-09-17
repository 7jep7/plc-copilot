# Frontend Integration Guide: Context-Centric File Processing

This guide covers the new context-centric file processing API for integrating PDF document management into the PLC-Copilot frontend.

## Overview

The new architecture processes PDF documents (datasheets, manuals, specifications) **immediately** as part of the context update process. No separate upload step is needed - files are processed and integrated into the project context in a single API call.

## Key Benefits

- **Immediate Processing**: Files are analyzed and context updated in one step
- **No File Storage**: Documents are processed and discarded, no file management needed
- **Context Integration**: File content becomes part of the transparent project context
- **Simplified Workflow**: Single endpoint handles all interactions

## API Integration

### Context Update with File Processing

**Endpoint**: `POST /api/v1/context/update`

**Content-Type**: `multipart/form-data`

**Parameters**:
- `message`: string (optional) - User message about the files
- `files`: File[] (optional) - PDF files to process
- `current_context`: JSON string (required) - Current project context
- `current_stage`: string (required) - Current workflow stage
- `mcq_responses`: JSON array (optional) - MCQ responses if applicable

**Example Request**:
```typescript
const formData = new FormData();
formData.append('message', 'Please analyze this motor datasheet');
formData.append('files', motorDatasheetFile);
formData.append('current_context', JSON.stringify({
  device_constants: {},
  information: ""
}));
formData.append('current_stage', 'gathering_requirements');

const response = await fetch('/api/v1/context/update', {
  method: 'POST',
  body: formData
});
**Response Example**:
```json
{
  "updated_context": {
    "device_constants": {
      "motor_M1": {
        "rated_power": "5.5kW",
        "rated_voltage": "400V",
        "rated_current": "11.2A",
        "rated_speed": "1450rpm",
        "mounting": "B3",
        "connection": "Star/Delta"
      }
    },
    "information": "# Motor Specification Analysis\n\n## Motor M1 - Main Drive\n- **Manufacturer**: Siemens\n- **Type**: 1LA7 series\n- **Protection**: IP55\n- **Insulation Class**: F\n\n## Key Features\n- Variable frequency drive compatible\n- Thermal protection built-in\n- Suitable for conveyor applications"
  },
  "current_stage": "gathering_requirements",
  "progress": 0.6,
  "chat_message": "I've analyzed the motor datasheet and extracted the key specifications. Based on this 5.5kW motor, what type of control system do you need?",
  "is_mcq": true,
  "mcq_question": "What type of control do you need for this motor?",
  "mcq_options": [
    "Simple on/off control",
    "Variable speed control (VFD)",
    "Soft starter control",
    "Full automation with feedback"
  ],
  "is_multiselect": false,
  "generated_code": null,
  "metadata": {
    "files_processed": 1,
    "tokens_used": 1240,
    "processing_time": 3.2
  }
}
```

## Frontend Implementation

### File Upload Component
```typescript
const FileUploader = ({ onFilesProcessed, context, stage }) => {
  const [uploading, setUploading] = useState(false);
  
  const handleFileSelect = async (files: File[]) => {
    setUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('message', 'Please analyze these uploaded files');
      
      files.forEach(file => formData.append('files', file));
      
      formData.append('current_context', JSON.stringify(context));
      formData.append('current_stage', stage);
      
      const response = await fetch('/api/v1/context/update', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status}`);
      }
      
      const result = await response.json();
      onFilesProcessed(result);
      
    } catch (error) {
      console.error('File processing failed:', error);
    } finally {
      setUploading(false);
    }
  };
  
  return (
    <div className="file-uploader">
      <input 
        type="file" 
        multiple 
        accept=".pdf"
        disabled={uploading}
        onChange={(e) => handleFileSelect(Array.from(e.target.files))}
      />
      {uploading && <div>Processing files...</div>}
    </div>
  );
};
```

### Drag & Drop Interface
```typescript
const DropZone = ({ onFilesProcessed, context, stage }) => {
  const [dragOver, setDragOver] = useState(false);
  
  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    
    const files = Array.from(e.dataTransfer.files).filter(
      file => file.type === 'application/pdf'
    );
    
    if (files.length > 0) {
      await processFiles(files);
    }
  };
  
  const processFiles = async (files: File[]) => {
    const formData = new FormData();
    formData.append('message', `Processing ${files.length} file(s)`);
    
    files.forEach(file => formData.append('files', file));
    formData.append('current_context', JSON.stringify(context));
    formData.append('current_stage', stage);
    
    const response = await fetch('/api/v1/context/update', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    onFilesProcessed(result);
  };
  
  return (
    <div 
      className={`drop-zone ${dragOver ? 'drag-over' : ''}`}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
    >
      Drop PDF files here to analyze
    </div>
  );
};
```

### Context Display After File Processing
```typescript
const ContextDisplay = ({ context }) => {
  return (
    <div className="context-display">
      <h3>Project Context</h3>
      
      {/* Device Constants */}
      {Object.keys(context.device_constants).length > 0 && (
        <section className="device-constants">
          <h4>Device Constants</h4>
          {Object.entries(context.device_constants).map(([device, specs]) => (
            <div key={device} className="device-spec">
              <h5>{device}</h5>
              <ul>
                {Object.entries(specs).map(([key, value]) => (
                  <li key={key}>
                    <strong>{key}:</strong> {value}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </section>
      )}
      
      {/* Information (Markdown) */}
      {context.information && (
        <section className="context-information">
          <h4>Project Information</h4>
          <ReactMarkdown>{context.information}</ReactMarkdown>
        </section>
      )}
    </div>
  );
};
```

## Error Handling

### File Processing Errors
```typescript
const handleFileProcessingError = (error) => {
  if (error.status === 400) {
    showError("Invalid file format. Only PDF files are supported.");
  } else if (error.status === 413) {
    showError("File too large. Please use files under 10MB.");
  } else if (error.status === 500) {
    showError("File processing failed. Please try again.");
  } else {
    showError("Upload failed. Please check your connection.");
  }
};
```

### File Validation
```typescript
const validateFiles = (files: File[]) => {
  const maxSize = 10 * 1024 * 1024; // 10MB
  const validTypes = ['application/pdf'];
  
  for (const file of files) {
    if (!validTypes.includes(file.type)) {
      throw new Error(`Invalid file type: ${file.name}. Only PDF files are supported.`);
    }
    
    if (file.size > maxSize) {
      throw new Error(`File too large: ${file.name}. Maximum size is 10MB.`);
    }
  }
};
```

## Best Practices

### 1. User Feedback
- Show upload progress for large files
- Display processing status
- Provide clear error messages
- Show what was extracted from files

### 2. Performance
- Process multiple files in single request
- Show immediate feedback on file selection
- Cache context updates locally

### 3. User Experience
- Support drag & drop
- Accept multiple files
- Show file names before processing
- Display extracted information clearly

## Migration from Legacy System

The new context-centric file processing replaces the old conversation-document system:

### Old Approach (Removed)
```typescript
// ❌ Legacy conversation-document upload (REMOVED)
const uploadToConversation = async (conversationId, file) => {
  // This endpoint no longer exists
  return fetch(`/api/v1/conversations/${conversationId}/documents/upload`, ...);
};
```

### New Approach (Current)
```typescript
// ✅ Context-centric file processing
const processFilesWithContext = async (files, context, stage) => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  formData.append('current_context', JSON.stringify(context));
  formData.append('current_stage', stage);
  
  return fetch('/api/v1/context/update', {
    method: 'POST',
    body: formData
  });
};
```

## 🎉 Benefits of New Architecture

1. **Immediate Processing**: Files analyzed and context updated instantly
2. **No File Management**: No need to track uploaded files or clean up storage
3. **Transparent Operation**: File content becomes part of visible context
4. **Simplified Integration**: Single endpoint for all interactions
5. **Better UX**: Users see exactly what was extracted from their files

The context-centric file processing provides a much simpler and more transparent way to handle document analysis in PLC-Copilot! 🚀
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