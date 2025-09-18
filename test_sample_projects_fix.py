#!/usr/bin/env python3
"""
Test script to verify the sample projects fix works correctly.

Tests:
1. Off-topic message without MCQ → sample projects returned
2. Off-topic message WITH MCQ → proceeds with assistant (not sample projects loop)
3. Random selection of 3 projects from 40
"""

import asyncio
import json
from app.services.simplified_context_service import SimplifiedContextService
from app.schemas.context import ContextUpdateRequest, ProjectContext, Stage

async def test_sample_projects_fix():
    print("🧪 Testing Sample Projects Fix")
    print("=" * 40)
    
    service = SimplifiedContextService()
    
    # Test 1: Off-topic message without MCQ → should get sample projects
    print("\n1️⃣ Test: Off-topic message without MCQ")
    request1 = ContextUpdateRequest(
        message="I want to learn about cooking pasta",
        mcq_responses=[],
        current_context=ProjectContext(device_constants={}, information=""),
        current_stage=Stage.GATHERING_REQUIREMENTS
    )
    
    response1 = await service.process_context_update(request1, session_id="test1")
    print(f"   Is MCQ: {response1.is_mcq}")
    print(f"   MCQ Options: {response1.mcq_options}")
    print(f"   ✅ Should show sample projects: {'✅' if response1.is_mcq else '❌'}")
    
    # Test 2: Off-topic message WITH MCQ → should proceed normally
    print("\n2️⃣ Test: Off-topic message WITH MCQ response")
    request2 = ContextUpdateRequest(
        message="I want to learn about cooking pasta",  # Still off-topic
        mcq_responses=["Conveyor Belt Control System with Safety Interlocks"],  # But has MCQ
        current_context=ProjectContext(device_constants={}, information=""),
        current_stage=Stage.GATHERING_REQUIREMENTS
    )
    
    response2 = await service.process_context_update(request2, session_id="test2")
    print(f"   Message contains: {response2.chat_message[:100]}...")
    print(f"   Should NOT be sample projects: {'✅' if 'sample projects' not in response2.chat_message.lower() else '❌'}")
    
    # Test 3: Verify random selection works
    print("\n3️⃣ Test: Random selection of sample projects")
    selections = []
    for i in range(5):
        response = await service.process_context_update(request1, session_id=f"random_test_{i}")
        selections.append(tuple(response.mcq_options))
    
    unique_selections = set(selections)
    print(f"   Generated {len(unique_selections)} unique combinations out of 5 tries")
    print(f"   Random selection working: {'✅' if len(unique_selections) > 1 else '❌'}")
    
    # Show some examples
    print("\n📋 Sample project examples:")
    for i, selection in enumerate(list(unique_selections)[:3], 1):
        print(f"   Set {i}: {', '.join(selection)}")

if __name__ == "__main__":
    asyncio.run(test_sample_projects_fix())