#!/usr/bin/env python3
"""
Test PDF file upload processing.
"""
import sys
import os
sys.path.append('/home/jonas-petersen/dev/plc-copilot')

import logging
logging.basicConfig(level=logging.INFO)

import json
from io import BytesIO
from unittest.mock import MagicMock

# Mock the OpenAI service to avoid needing API keys
class MockOpenAIService:
    async def chat_completion(self, request, messages):
        # Mock response for file processing
        if "Extract PLC-relevant data" in messages[0]["content"]:
            return json.dumps({
                "devices": {
                    "KV-8000A": {
                        "Type": "PLC Controller",
                        "Model": "KV-8000A",
                        "Specifications": {"I/O Points": "512", "Memory": "2MB", "Communication": "Ethernet"}
                    }
                },
                "information": "PLC controller datasheet with specifications for I/O configuration and networking",
                "summary": "Extracted PLC controller specifications from PDF datasheet"
            })
        else:
            # Mock response for main context processing
            return json.dumps({
                "updated_context": {
                    "device_constants": {
                        "KV-8000A": {
                            "data": {"I/O Points": "512", "Memory": "2MB", "Communication": "Ethernet"},
                            "origin": "file"
                        }
                    },
                    "information": "KV-8000A PLC controller datasheet analyzed. This is a high-capacity controller suitable for complex automation systems."
                },
                "chat_message": "I've analyzed your KV-8000A PLC datasheet. This is a powerful controller with 512 I/O points. What type of system would you like to design?",
                "is_mcq": True,
                "mcq_question": "What type of automation system are you planning?",
                "mcq_options": ["Manufacturing Line", "Process Control", "Building Automation"],
                "is_multiselect": False,
                "generated_code": None,
                "gathering_requirements_estimated_progress": 0.4,
                "file_extractions": []
            })

# Import after setting up the mock
from app.services.context_service import ContextProcessingService
from app.schemas.context import ContextUpdateRequest, ProjectContext, Stage

def load_pdf_file():
    """Load the actual PDF file from uploads."""
    pdf_path = "/home/jonas-petersen/dev/plc-copilot/uploads/KV-8000A_Datasheet.pdf"
    try:
        with open(pdf_path, 'rb') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Could not load PDF file: {e}")
        return None

async def test_pdf_processing():
    """Test PDF file processing."""
    print("🧪 Testing PDF file processing...")
    
    # Load actual PDF file
    pdf_bytes = load_pdf_file()
    if not pdf_bytes:
        print("❌ Cannot test without PDF file")
        return None
    
    # Create context service with mocked OpenAI
    service = ContextProcessingService()
    service.openai_service = MockOpenAIService()
    
    # Create file data
    file_data = BytesIO(pdf_bytes)
    
    # Create simple context and request
    context = ProjectContext(device_constants={}, information="")
    request = ContextUpdateRequest(
        message="Please analyze this PLC datasheet",
        mcq_responses=[],
        current_context=context,
        current_stage=Stage.GATHERING_REQUIREMENTS
    )
    
    print(f"📄 PDF file size: {len(pdf_bytes)} bytes")
    print(f"📝 Message: {request.message}")
    print(f"🏗️ Stage: {request.current_stage}")
    
    try:
        # Test file processing
        result = await service.process_context_update(request, uploaded_files=[file_data])
        
        print("✅ PDF processing completed!")
        print(f"📊 Updated context device constants: {len(result.updated_context.device_constants)}")
        print(f"📋 Updated context information length: {len(result.updated_context.information)}")
        print(f"💬 Chat message: {result.chat_message[:100]}...")
        print(f"📁 File extractions: {len(result.file_extractions)}")
        
        if result.file_extractions:
            for i, extraction in enumerate(result.file_extractions):
                print(f"  File {i+1}: {extraction.processing_summary}")
                print(f"    Devices: {len(extraction.extracted_devices)}")
                print(f"    Info length: {len(extraction.extracted_information)}")
        
        if result.updated_context.device_constants:
            print("\n📋 Device Constants:")
            for device_name, device_info in result.updated_context.device_constants.items():
                print(f"  {device_name}: {device_info}")
        
        print(f"\n📄 Context Information:\n{result.updated_context.information}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(test_pdf_processing())