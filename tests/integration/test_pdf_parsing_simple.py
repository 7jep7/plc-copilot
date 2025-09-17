#!/usr/bin/env python3
"""
Lightweight PDF parsing test - no database required.
Tests only the core PDF extraction and OpenAI analysis functionality.
"""

import sys
import os
import asyncio

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.services.document_service import DocumentService
from app.services.openai_service import OpenAIService
from app.models.document import Document

class MockDocument:
    """Mock document for testing without database."""
    def __init__(self, file_path, raw_text):
        self.id = "test-doc-id"
        self.file_path = file_path
        self.raw_text = raw_text
        self.filename = os.path.basename(file_path)

async def test_pdf_parsing_only(pdf_path: str):
    """Test PDF parsing without database dependencies."""
    print("🔍 Testing PDF Parsing (No Database)")
    print("=" * 50)
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    # Create service without database session
    service = DocumentService(db=None)
    
    # Test PDF extraction directly
    print(f"📄 Extracting text from: {os.path.basename(pdf_path)}")
    raw_text = await service._extract_text_from_pdf(pdf_path)
    
    print(f"\n📊 Extraction Results:")
    print(f"   Total characters: {len(raw_text)}")
    print(f"   Total lines: {len(raw_text.splitlines())}")
    print(f"   First 300 chars: {raw_text[:300]}...")
    
    # Test document classification  
    doc_type = service._classify_document_type(raw_text)
    print(f"   Document type: {doc_type}")
    
    # Test device info extraction
    device_info = service._extract_device_info(raw_text)
    print(f"   Device info: {device_info}")
    
    return raw_text

async def test_openai_analysis(raw_text: str):
    """Test OpenAI PLC analysis without database."""
    print(f"\n🤖 Testing OpenAI PLC Analysis")
    print("=" * 50)
    
    # Create mock document
    mock_doc = MockDocument("test.pdf", raw_text)
    
    # Test OpenAI analysis
    openai_service = OpenAIService()
    analysis = await openai_service.analyze_document_for_plc_context(mock_doc)
    
    if analysis:
        print(f"✅ OpenAI Analysis Complete")
        print(f"   Model used: {analysis.get('model_used', 'Unknown')}")
        analysis_text = analysis.get('analysis', 'No analysis available')
        print(f"   Analysis length: {len(analysis_text)} characters")
        print(f"   Analysis preview: {analysis_text[:400]}...")
        
        # Look for PLC-relevant keywords
        plc_keywords = ['I/O', 'input', 'output', 'control', 'interface', 'communication', 'protocol']
        found_keywords = [kw for kw in plc_keywords if kw.lower() in analysis_text.lower()]
        print(f"   PLC keywords found: {found_keywords}")
        
    else:
        print(f"❌ OpenAI Analysis Failed")
    
    return analysis

async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_pdf_parsing_simple.py <path_to_pdf>")
        return
    
    pdf_path = sys.argv[1]
    
    print("🧪 Simple PDF Parsing Test (No Database)")
    print("=" * 60)
    
    try:
        # Test 1: PDF extraction
        raw_text = await test_pdf_parsing_only(pdf_path)
        
        if raw_text and len(raw_text) > 100:
            # Test 2: OpenAI analysis  
            analysis = await test_openai_analysis(raw_text)
            
            print(f"\n🎉 Testing Complete!")
            print(f"📊 Summary:")
            print(f"   - PDF extraction: ✅ Success ({len(raw_text)} chars)")
            print(f"   - OpenAI analysis: {'✅ Success' if analysis else '❌ Failed'}")
            
        else:
            print(f"❌ PDF extraction failed or returned insufficient text")
            
    except Exception as e:
        print(f"💥 Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())