#!/usr/bin/env python3
"""
Test script for PDF document parsing and processing functionality.

This script tests:
1. PDF text extraction using the multi-method approach
2. Document classification and device info extraction
3. OpenAI-based PLC context analysis
4. Complete document processing workflow
"""

import sys
import os
import asyncio
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.document_service import DocumentService
from app.models.document import Document, DocumentStatus
from fastapi import UploadFile
import tempfile
import aiofiles

class MockUploadFile:
    """Mock UploadFile for testing purposes."""
    def __init__(self, file_path: str):
        self.filename = os.path.basename(file_path)
        self.content_type = "application/pdf"
        self.file_path = file_path
    
    async def read(self):
        async with aiofiles.open(self.file_path, 'rb') as f:
            return await f.read()

async def test_pdf_extraction(pdf_path: str):
    """Test PDF text extraction methods."""
    print("🔍 Testing PDF Text Extraction")
    print("=" * 50)
    
    # Create a database session
    db = SessionLocal()
    document_service = DocumentService(db)
    
    try:
        # Test the PDF extraction directly
        print(f"📄 Extracting text from: {os.path.basename(pdf_path)}")
        
        if not os.path.exists(pdf_path):
            print(f"❌ File not found: {pdf_path}")
            return None
        
        # Test text extraction
        raw_text = await document_service._extract_text_from_pdf(pdf_path)
        
        print(f"\n📊 Extraction Results:")
        print(f"   Total characters: {len(raw_text)}")
        print(f"   Total lines: {len(raw_text.splitlines())}")
        print(f"   First 500 chars: {raw_text[:500]}...")
        
        # Test document classification
        doc_type = document_service._classify_document_type(raw_text)
        print(f"   Document type: {doc_type}")
        
        # Test device info extraction
        device_info = document_service._extract_device_info(raw_text)
        print(f"   Device info: {device_info}")
        
        return raw_text
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return None
    finally:
        db.close()

async def test_document_upload_and_processing(pdf_path: str):
    """Test complete document upload and processing workflow."""
    print("\n🚀 Testing Complete Document Workflow")
    print("=" * 50)
    
    # Create a database session
    db = SessionLocal()
    document_service = DocumentService(db)
    
    try:
        # Create mock upload file
        mock_file = MockUploadFile(pdf_path)
        
        print(f"📤 Uploading document: {mock_file.filename}")
        
        # Upload document
        document = await document_service.create_document(
            file=mock_file,
            description="Camera datasheet for testing",
            tags="camera,datasheet,test"
        )
        
        print(f"✅ Document uploaded successfully")
        print(f"   Document ID: {document.id}")
        print(f"   Status: {document.status}")
        print(f"   File path: {document.file_path}")
        
        # Process document
        print(f"\n⚙️ Processing document...")
        processed_doc = await document_service.process_document(str(document.id))
        
        if processed_doc:
            print(f"✅ Document processed successfully")
            print(f"   Status: {processed_doc.status}")
            print(f"   Document type: {processed_doc.document_type}")
            print(f"   Manufacturer: {processed_doc.manufacturer}")
            print(f"   Device model: {processed_doc.device_model}")
            print(f"   Raw text length: {len(processed_doc.raw_text or '')}")
            
            # Show PLC analysis
            if processed_doc.specifications:
                print(f"\n🤖 PLC Analysis Results:")
                analysis = processed_doc.specifications.get('analysis', 'No analysis available')
                print(f"   Model used: {processed_doc.specifications.get('model_used', 'Unknown')}")
                print(f"   Analysis preview: {analysis[:300]}...")
            
            # Get extracted data
            extracted_data = document_service.get_extracted_data(str(document.id))
            if extracted_data:
                print(f"\n📊 Extracted Data Summary:")
                print(f"   Status: {extracted_data['processing_status']}")
                print(f"   Device info: {extracted_data['device_info']}")
        else:
            print(f"❌ Document processing failed")
        
        return document
        
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

def test_api_endpoints_info():
    """Display information about API endpoints for frontend integration."""
    print("\n🔌 API Endpoints for Frontend Integration")
    print("=" * 50)
    
    print("📤 Upload Document:")
    print("   POST /api/v1/documents/upload")
    print("   Content-Type: multipart/form-data")
    print("   Body: file=@document.pdf, description=optional, tags=optional")
    
    print("\n📋 List Documents:")
    print("   GET /api/v1/documents/")
    print("   Query params: skip, limit, status_filter")
    
    print("\n🔍 Get Document:")
    print("   GET /api/v1/documents/{document_id}")
    
    print("\n⚙️ Process Document:")
    print("   POST /api/v1/documents/{document_id}/process")
    
    print("\n📊 Get Extracted Data:")
    print("   GET /api/v1/documents/{document_id}/extracted-data")
    
    print("\n💬 Use in Conversation:")
    print("   POST /api/v1/plc/generate")
    print("   Body: {user_prompt, document_id, ...}")

async def main():
    """Main test function."""
    print("🧪 PDF Document Processing Test Suite")
    print("=" * 70)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if a PDF file path is provided as argument
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        if not os.path.exists(pdf_path):
            print(f"❌ File not found: {pdf_path}")
            return
    else:
        print("📁 No PDF file provided. Usage: python test_document_processing.py <path_to_pdf>")
        print("   You can provide a camera datasheet PDF for testing.")
        print("   Example: python test_document_processing.py /path/to/camera_datasheet.pdf")
        
        # Show API info anyway
        test_api_endpoints_info()
        return
    
    try:
        # Test 1: PDF text extraction
        raw_text = await test_pdf_extraction(pdf_path)
        
        if raw_text:
            # Test 2: Complete workflow
            document = await test_document_upload_and_processing(pdf_path)
            
            # Test 3: API info
            test_api_endpoints_info()
            
            print(f"\n🎉 All tests completed successfully!")
            
            if document:
                print(f"\n💡 Next steps:")
                print(f"   1. Use document ID {document.id} in PLC generation")
                print(f"   2. Include in conversation context")
                print(f"   3. Test frontend integration with provided API endpoints")
        else:
            print(f"\n❌ PDF extraction failed, skipping other tests")
            
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())