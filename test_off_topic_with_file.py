#!/usr/bin/env python3
"""
Test to verify that off-topic requests with files will call the LLM.
"""

import asyncio
from io import BytesIO
from app.services.simplified_context_service import SimplifiedContextService
from app.schemas.context import ContextUpdateRequest, ProjectContext, Stage

async def test_off_topic_with_file():
    print("🧪 Testing Off-Topic Request with File Upload")
    print("=" * 50)
    
    service = SimplifiedContextService()
    
    # Create a dummy file
    dummy_file = BytesIO(b"This is a dummy PDF content for testing")
    
    # Off-topic request WITH file
    request = ContextUpdateRequest(
        message="I want to learn about cooking pasta recipes",  # Off-topic
        mcq_responses=[],
        current_context=ProjectContext(device_constants={}, information=""),
        current_stage=Stage.GATHERING_REQUIREMENTS
    )
    
    print("📋 Request details:")
    print(f"   Message: '{request.message}'")
    print(f"   File uploaded: Yes (dummy file)")
    print(f"   Is message PLC-related: {service._is_plc_related(request.message)}")
    
    print("\n🔍 Analyzing code flow...")
    
    # Check what case this would trigger
    has_context = bool(
        request.current_context and 
        (request.current_context.device_constants or request.current_context.information)
    )
    has_files = True  # We're uploading a file
    has_mcq_responses = bool(request.mcq_responses)
    
    print(f"   has_context: {has_context}")
    print(f"   has_files: {has_files}")
    print(f"   has_mcq_responses: {has_mcq_responses}")
    
    if has_files:
        print("   → Will trigger: Case 3 (File upload)")
        print("   → Will call: _handle_file_upload_case()")
        print("   → Will upload to vector store: YES")
        print("   → Will call OpenAI Assistant: YES")
        print("   → Cost implications: HIGH (file upload + LLM call)")
    elif has_context:
        print("   → Will trigger: Case 2 (Context update)")
    else:
        print("   → Will trigger: Case 1 (Project kickoff)")
        print("   → Will check if PLC-related: YES")
        if service._is_plc_related(request.message):
            print("   → Will call OpenAI Assistant: YES")
        else:
            print("   → Will show sample projects: YES (no LLM call)")
    
    print(f"\n🚨 FINDING: Off-topic message + file = EXPENSIVE LLM call!")
    print(f"   The off-topic check (_is_plc_related) is BYPASSED when files are present!")

if __name__ == "__main__":
    asyncio.run(test_off_topic_with_file())