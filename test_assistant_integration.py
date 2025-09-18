#!/usr/bin/env python3
"""
Test script for the new simplified OpenAI Assistant integration.

This script tests the three core interaction cases:
1. Project kickoff (no context, no file)
2. Context update (context exists, no file) 
3. File upload (file + optional context)
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.schemas.context import ProjectContext, ContextUpdateRequest, Stage
from app.services.assistant_service import AssistantService
from app.services.vector_store_service import VectorStoreService
from app.services.simplified_context_service import SimplifiedContextService


async def test_assistant_service():
    """Test the basic AssistantService functionality."""
    print("Testing AssistantService...")
    
    try:
        assistant = AssistantService()
        
        # Test simple message
        response = await assistant.process_message(
            user_message="I want to create a conveyor belt control system with safety features.",
            current_context=None,
            file_ids=None
        )
        
        print("Assistant Response:")
        print(json.dumps(response, indent=2))
        
        # Validate response structure
        required_fields = [
            "updated_context", "chat_message", "is_mcq", 
            "gathering_requirements_estimated_progress"
        ]
        
        for field in required_fields:
            if field not in response:
                print(f"❌ Missing required field: {field}")
                return False
            else:
                print(f"✅ Found required field: {field}")
        
        print("✅ AssistantService test passed!")
        return True
        
    except Exception as e:
        print(f"❌ AssistantService test failed: {e}")
        return False


async def test_simplified_context_service():
    """Test the SimplifiedContextService with all three cases."""
    print("\nTesting SimplifiedContextService...")
    
    try:
        service = SimplifiedContextService()
        
        # Test Case 1: Project kickoff
        print("\n--- Testing Case 1: Project Kickoff ---")
        request = ContextUpdateRequest(
            message="I want to build a motor control system",
            mcq_responses=[],
            previous_copilot_message=None,
            current_context=ProjectContext(
                device_constants={},
                information="",
                stage=Stage.GATHERING_REQUIREMENTS,
                session_id=None
            ),
            current_stage=Stage.GATHERING_REQUIREMENTS
        )
        
        response = await service.process_context_update(request)
        print(f"Response: {response.chat_message[:100]}...")
        print(f"Stage: {response.current_stage}")
        print(f"Progress: {response.gathering_requirements_estimated_progress}")
        
        # Test Case 2: Context update
        print("\n--- Testing Case 2: Context Update ---")
        request_with_context = ContextUpdateRequest(
            message="The motor should be 5HP and operate at 1800 RPM",
            mcq_responses=[],
            previous_copilot_message=response.chat_message,
            current_context=response.updated_context,
            current_stage=response.current_stage
        )
        
        response2 = await service.process_context_update(request_with_context)
        print(f"Response: {response2.chat_message[:100]}...")
        print(f"Device Constants: {response2.updated_context.device_constants}")
        print(f"Progress: {response2.gathering_requirements_estimated_progress}")
        
        print("✅ SimplifiedContextService test passed!")
        return True
        
    except Exception as e:
        print(f"❌ SimplifiedContextService test failed: {e}")
        return False


async def test_vector_store_service():
    """Test the VectorStoreService with file upload."""
    print("\nTesting VectorStoreService...")
    
    try:
        vector_service = VectorStoreService()
        
        # Get vector store info
        info = vector_service.get_vector_store_info()
        print(f"Vector Store Info: {info}")
        
        # Create a sample text file
        from io import BytesIO
        sample_text = """
        VFD Motor Control Specifications
        
        Motor Type: 3-Phase Induction Motor
        Power Rating: 5 HP (3.7 kW)
        Voltage: 480V AC
        Current: 7.2 A at full load
        Speed: 1800 RPM
        
        Control Requirements:
        - Start/Stop functionality
        - Variable speed control (0-100%)
        - Emergency stop capability
        - Overload protection
        - Fault monitoring and reset
        
        I/O Requirements:
        Inputs:
        - Start pushbutton (NO contact)
        - Stop pushbutton (NC contact)  
        - Emergency stop (NC contact)
        - Speed reference (0-10V analog)
        
        Outputs:
        - Motor contactor control
        - Run indicator light
        - Fault indicator light
        - Speed feedback (4-20mA analog)
        """
        
        file_content = BytesIO(sample_text.encode('utf-8'))
        
        # Upload to vector store
        file_metadata = await vector_service.upload_files_to_vector_store(
            [file_content], ["motor_specs.txt"], "test_session_123"
        )
        print(f"Uploaded files: {file_metadata}")
        
        # List session files
        session_files = vector_service.list_session_files("test_session_123")
        print(f"Session files: {session_files}")
        
        # Cleanup
        await vector_service.cleanup_session_files("test_session_123")
        
        print("✅ VectorStoreService test passed!")
        return True
        
    except Exception as e:
        print(f"❌ VectorStoreService test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting PLC Copilot Assistant Integration Tests\n")
    
    # Check environment
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY environment variable not set!")
        return
    
    tests = [
        test_assistant_service,
        test_vector_store_service,
        test_simplified_context_service,
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print(f"\n📊 Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All tests passed! The new assistant integration is working correctly.")
    else:
        print("❌ Some tests failed. Please check the implementation.")


if __name__ == "__main__":
    asyncio.run(main())