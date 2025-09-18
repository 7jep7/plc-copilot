#!/usr/bin/env python3
"""
Test file upload with LLM failure to verify fallback mechanism.
"""
import sys
import os
sys.path.append('/home/jonas-petersen/dev/plc-copilot')

import logging
logging.basicConfig(level=logging.INFO)

import json
from io import BytesIO

# Mock the OpenAI service that fails
class FailingMockOpenAIService:
    async def chat_completion(self, request, messages):
        # Simulate LLM failure for file processing
        if "Extract PLC-relevant data" in messages[0]["content"]:
            raise Exception("Mock LLM service unavailable")
        else:
            # Still return proper response for main context processing
            return json.dumps({
                "updated_context": {
                    "device_constants": {},
                    "information": "File uploaded but could not be processed by AI. Raw content available for analysis."
                },
                "chat_message": "I received your file but encountered an issue processing it with AI. However, I can still see the content. What would you like me to help you with?",
                "is_mcq": False,
                "mcq_question": None,
                "mcq_options": [],
                "is_multiselect": False,
                "generated_code": None,
                "gathering_requirements_estimated_progress": 0.2,
                "file_extractions": []
            })

# Import after setting up the mock
from app.services.context_service import ContextProcessingService
from app.schemas.context import ContextUpdateRequest, ProjectContext, Stage

def create_test_text_file():
    """Create a simple test text file."""
    content = """Sensor Specification
    
Model: TEMP-SENSOR-001
Type: Temperature sensor
Range: -20°C to +150°C
Output: 4-20mA
Accuracy: ±0.1°C
"""
    return content.encode('utf-8')

async def test_fallback_processing():
    """Test file processing with LLM failure to verify fallback works."""
    print("🧪 Testing file processing with LLM failure (fallback test)...")
    
    # Create context service with failing OpenAI mock
    service = ContextProcessingService()
    service.openai_service = FailingMockOpenAIService()
    
    # Create simple test file
    file_bytes = create_test_text_file()
    file_data = BytesIO(file_bytes)
    
    # Create simple context and request
    context = ProjectContext(device_constants={}, information="")
    request = ContextUpdateRequest(
        message="Please analyze this sensor specification",
        mcq_responses=[],
        current_context=context,
        current_stage=Stage.GATHERING_REQUIREMENTS
    )
    
    print(f"📄 File size: {len(file_bytes)} bytes")
    print(f"📝 Message: {request.message}")
    print(f"🏗️ Stage: {request.current_stage}")
    
    try:
        # Test file processing with LLM failure
        result = await service.process_context_update(request, uploaded_files=[file_data])
        
        print("✅ Fallback processing completed!")
        print(f"📊 Updated context device constants: {len(result.updated_context.device_constants)}")
        print(f"📋 Updated context information length: {len(result.updated_context.information)}")
        print(f"💬 Chat message: {result.chat_message[:100]}...")
        print(f"📁 File extractions: {len(result.file_extractions)}")
        
        if result.file_extractions:
            for i, extraction in enumerate(result.file_extractions):
                print(f"  File {i+1}: {extraction.processing_summary}")
                print(f"    Devices: {len(extraction.extracted_devices)}")
                print(f"    Info length: {len(extraction.extracted_information)}")
        
        print(f"\n📄 Context Information:\n{result.updated_context.information}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(test_fallback_processing())