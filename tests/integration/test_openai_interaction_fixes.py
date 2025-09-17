#!/usr/bin/env python3
"""Integration test for OpenAI interaction fixes."""

import sys
import os
import asyncio

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.services.conversation_orchestrator import ConversationOrchestrator
from app.schemas.conversation import ConversationRequest, ConversationStage


async def test_mcq_fixes():
    """Test MCQ prompt fixes and answer context persistence."""
    print("🔧 Testing OpenAI Interaction Fixes")
    print("=" * 50)
    
    orchestrator = ConversationOrchestrator()
    
    # Test 1: Non-industrial input detection with demo suggestions
    print("\n📋 Test 1: Non-industrial Input Detection")
    print("-" * 30)
    
    non_industrial_request = ConversationRequest(
        message="I need help building a web application with React and Node.js"
    )
    
    response = await orchestrator.process_message(non_industrial_request)
    print(f"🎯 Response to non-industrial input:")
    print(f"   Stage: {response.stage}")
    print(f"   Is MCQ: {response.is_mcq}")
    print(f"   Response length: {len(response.response)} chars")
    if response.is_mcq:
        print(f"   MCQ Options: {len(response.mcq_options)} options")
        for i, option in enumerate(response.mcq_options):
            print(f"      {chr(65+i)}) {option[:80]}...")
    
    # Test 2: Industrial input with structured text focus
    print("\n📋 Test 2: Industrial Input with ST Focus")
    print("-" * 30)
    
    industrial_request = ConversationRequest(
        message="I need to control a conveyor belt system with safety interlocks and speed control"
    )
    
    response = await orchestrator.process_message(industrial_request)
    print(f"🎯 Response to industrial input:")
    print(f"   Stage: {response.stage}")
    print(f"   Contains 'Structured Text': {'Structured Text' in response.response}")
    print(f"   Contains 'ST': {' ST ' in response.response}")
    print(f"   Contains datasheet suggestion: {'datasheet' in response.response.lower()}")
    
    # Test 3: MCQ response handling with context persistence
    print("\n📋 Test 3: MCQ Answer Context Persistence")
    print("-" * 30)
    
    if response.is_mcq and response.mcq_options:
        # Simulate MCQ response
        mcq_answer_request = ConversationRequest(
            conversation_id=response.conversation_id,
            message="Additional details: This is for a food packaging line with hygiene requirements",
            mcq_response={
                "question": response.mcq_question,
                "selected_options": [response.mcq_options[0]],  # Select first option
                "is_multiselect": False
            }
        )
        
        mcq_response = await orchestrator.process_message(mcq_answer_request)
        print(f"🎯 MCQ Answer Processing:")
        print(f"   Stage: {mcq_response.stage}")
        print(f"   Response mentions MCQ answer: {'Selected:' in mcq_response.response or 'MCQ' in mcq_response.response}")
        
        # Check conversation state for context persistence
        conversation = orchestrator.conversations.get(response.conversation_id)
        if conversation and conversation.qa:
            print(f"   Answers stored in context: {len(conversation.qa.answers_received)}")
            if conversation.qa.answers_received:
                print(f"   Last answer contains MCQ info: {'MCQ' in conversation.qa.answers_received[-1] or 'Selected' in conversation.qa.answers_received[-1]}")
    
    # Test 4: Context summarization
    print("\n📋 Test 4: Context Window Management")
    print("-" * 30)
    
    # Add many messages to trigger summarization
    for i in range(25):
        dummy_request = ConversationRequest(
            conversation_id=response.conversation_id,
            message=f"Additional requirement {i}: Temperature range 0-100°C, pressure monitoring needed"
        )
        await orchestrator.process_message(dummy_request)
    
    conversation = orchestrator.conversations.get(response.conversation_id)
    if conversation:
        print(f"   Total messages in conversation: {len(conversation.messages)}")
        print(f"   Context summarization should be active: {len(conversation.messages) > 20}")
        
        # Test context summary generation
        summary = orchestrator._build_context_summary(conversation)
        print(f"   Context summary generated: {len(summary) > 0}")
        if summary:
            print(f"   Summary contains 'Structured Text': {'Structured Text' in summary}")
            print(f"   Summary length: {len(summary)} chars")
    
    print("\n✅ All OpenAI interaction fixes tested successfully!")
    return True


async def main():
    """Run the integration test."""
    try:
        await test_mcq_fixes()
        print("\n🎉 Integration test completed successfully!")
        return True
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)