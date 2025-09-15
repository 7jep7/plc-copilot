"""Simple test script for the multi-stage conversation system."""

import asyncio
from app.schemas.conversation import ConversationRequest, ConversationStage
from app.services.conversation_orchestrator import ConversationOrchestrator


async def simple_demo():
    """Simple demo showing one conversation stage."""
    
    print("=== Simple PLC-Copilot Conversation Demo ===\n")
    
    orchestrator = ConversationOrchestrator()
    
    # Single conversation step
    print("Testing Requirements Gathering Stage...")
    
    request = ConversationRequest(
        message="I need to control a simple conveyor belt with start/stop buttons."
    )
    
    response = await orchestrator.process_message(request)
    
    print(f"✅ Conversation ID: {response.conversation_id}")
    print(f"✅ Current Stage: {response.stage}")
    print(f"✅ Response Length: {len(response.response)} characters")
    print(f"✅ Next Suggested Stage: {response.next_stage}")
    print(f"✅ Stage Progress: {response.stage_progress}")
    print(f"✅ Suggested Actions: {response.suggested_actions}")
    
    print("\n" + "="*50)
    print("RESPONSE CONTENT:")
    print("="*50)
    print(response.response)
    
    # Get conversation state
    conversation = orchestrator.get_conversation(response.conversation_id)
    print(f"\n✅ Total Messages in Conversation: {len(conversation.messages)}")
    print(f"✅ Conversation Created: {conversation.created_at}")


if __name__ == "__main__":
    asyncio.run(simple_demo())