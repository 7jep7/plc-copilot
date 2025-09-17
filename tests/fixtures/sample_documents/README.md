# Sample Documents for Testing

This directory contains sample datasheets and manuals for testing the document parsing and processing functionality.

## Directory Structure

```
sample_documents/
├── datasheets/          # Equipment datasheets
│   ├── cameras/         # Camera and vision system datasheets
│   ├── sensors/         # Sensor datasheets  
│   ├── motors/          # Motor and drive datasheets
│   └── plcs/           # PLC and controller datasheets
├── manuals/            # Equipment manuals
└── specifications/     # Technical specifications
```

## How to Use

### For Document Parser Testing

Place your sample PDFs in the appropriate subdirectory and test with:

```bash
# Test document processing with your sample
python tests/integration/test_document_processing.py tests/fixtures/sample_documents/datasheets/cameras/your_camera_datasheet.pdf
```

### For Conversation Integration Testing

1. Upload a document via API
2. Use the document_id in conversation or PLC generation
3. Verify the extracted context is properly integrated

```bash
# Example workflow test
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@tests/fixtures/sample_documents/datasheets/cameras/sample.pdf"

# Use returned document_id in PLC generation
curl -X POST "http://localhost:8000/api/v1/plc/generate" \
  -H "Content-Type: application/json" \
  -d '{"user_prompt":"Create camera control logic","document_id":"your-doc-id"}'
```

## Adding New Samples

When adding new sample documents:

1. **Ensure no sensitive information** - only use publicly available datasheets
2. **Keep file sizes reasonable** - prefer smaller PDFs for faster testing
3. **Use descriptive filenames** - include manufacturer/model when possible
4. **Add variety** - different formats, layouts, and content types help test robustness

## Current Samples

- *None yet* - Add your first sample document!

## File Format Support

Currently supported:
- ✅ PDF files (all formats)

Future support planned:
- 📋 Excel/CSV technical specifications
- 🖼️ Image-based datasheets (OCR)
- 📄 Word documents and text files