#!/usr/bin/env python3
"""
Simple debug script to test file upload processing in isolation.
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
                    "AC-SERVO-500": {
                        "Type": "3-phase AC servo motor",
                        "Model": "AC-SERVO-500",
                        "Specifications": {"Power": "2.5 kW", "Voltage": "480V AC", "Speed": "3000 RPM"}
                    }
                },
                "information": "Motor specification document with power, voltage, and speed requirements",
                "summary": "Extracted motor specifications from document"
            })
        else:
            # Mock response for main context processing
            return json.dumps({
                "updated_context": {
                    "device_constants": {
                        "AC-SERVO-500": {
                            "data": {"Power": "2.5 kW", "Voltage": "480V AC", "Speed": "3000 RPM"},
                            "origin": "file"
                        }
                    },
                    "information": "Motor specification document analyzed. Requirements include 3-phase AC servo motor with 2.5 kW power rating."
                },
                "chat_message": "I've analyzed your motor specification document. I found details about the AC-SERVO-500 motor. What type of control system would you like to implement?",
                "is_mcq": True,
                "mcq_question": "What type of motor control do you need?",
                "mcq_options": ["Start/Stop Control", "Speed Control", "Position Control"],
                "is_multiselect": False,
                "generated_code": None,
                "gathering_requirements_estimated_progress": 0.3,
                "file_extractions": []
            })

# Import after setting up the mock
from app.services.context_service import ContextProcessingService
from app.schemas.context import ContextUpdateRequest, ProjectContext, Stage

def create_test_text_file():
    """Create a simple test text file."""
    content = """Motor Specification Document
    
Model: AC-SERVO-500
Type: 3-phase AC servo motor
Power: 2.5 kW
Voltage: 480V AC
Speed: 3000 RPM
Torque: 8 Nm

Control Requirements:
- Start/Stop via digital input
- Speed control via analog input 0-10V
- Emergency stop safety circuit
- Overload protection
"""
    return content.encode('utf-8')

async def test_file_processing():
    """Test file processing in isolation."""
    print("🧪 Testing file processing...")
    
    # Create context service with mocked OpenAI
    service = ContextProcessingService()
    service.openai_service = MockOpenAIService()
    
    # Create simple test file
    file_bytes = create_test_text_file()
    file_data = BytesIO(file_bytes)
    
    # Create simple context and request
    context = ProjectContext(device_constants={}, information="")
    request = ContextUpdateRequest(
        message="Please analyze this motor specification",
        mcq_responses=[],
        current_context=context,
        current_stage=Stage.GATHERING_REQUIREMENTS
    )
    
    print(f"📄 File size: {len(file_bytes)} bytes")
    print(f"📝 Message: {request.message}")
    print(f"🏗️ Stage: {request.current_stage}")
    
    try:
        # Test file processing
        result = await service.process_context_update(request, uploaded_files=[file_data])
        
        print("✅ Processing completed!")
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
    result = asyncio.run(test_file_processing())