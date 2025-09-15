"""Test script demonstrating the multi-stage conversation system."""

import asyncio
import json
from app.schemas.conversation import ConversationRequest, ConversationStage
from app.services.conversation_orchestrator import ConversationOrchestrator


async def demo_conversation():
    """Demonstrate a complete multi-stage conversation flow."""
    
    orchestrator = ConversationOrchestrator()
    conversation_id = None
    
    print("=== PLC-Copilot Multi-Stage Conversation Demo ===\n")
    
    # Stage 1: Requirements Gathering
    print("1. REQUIREMENTS GATHERING STAGE")
    print("-" * 40)
    
    request1 = ConversationRequest(
        message="I need to control a conveyor belt system with start/stop functionality and safety interlocks."
    )
    
    response1 = await orchestrator.process_message(request1)
    conversation_id = response1.conversation_id
    
    print(f"Stage: {response1.stage}")
    print(f"Response: {response1.response[:200]}...")
    print(f"Next Stage: {response1.next_stage}")
    print()
    
    # Stage 2: Q&A Clarification  
    print("2. Q&A CLARIFICATION STAGE")
    print("-" * 40)
    
    request2 = ConversationRequest(
        conversation_id=conversation_id,
        message="The conveyor operates at 24V DC, has a maximum speed of 2 m/s, includes emergency stop buttons, and needs motor overload protection."
    )
    
    response2 = await orchestrator.process_message(request2)
    
    print(f"Stage: {response2.stage}")
    print(f"Response: {response2.response[:200]}...")
    print(f"Next Stage: {response2.next_stage}")
    print()
    
    # Stage 3: Force Code Generation
    print("3. CODE GENERATION STAGE")
    print("-" * 40)
    
    request3 = ConversationRequest(
        conversation_id=conversation_id,
        message="Please generate the Structured Text code for this conveyor system.",
        force_stage=ConversationStage.CODE_GENERATION
    )
    
    response3 = await orchestrator.process_message(request3)
    
    print(f"Stage: {response3.stage}")
    print(f"Response: {response3.response[:300]}...")
    print(f"Next Stage: {response3.next_stage}")
    print()
    
    # Stage 4: Refinement
    print("4. REFINEMENT & TESTING STAGE")
    print("-" * 40)
    
    request4 = ConversationRequest(
        conversation_id=conversation_id,
        message="Can you add a speed control feature and improve the emergency stop logic?"
    )
    
    response4 = await orchestrator.process_message(request4)
    
    print(f"Stage: {response4.stage}")
    print(f"Response: {response4.response[:300]}...")
    print(f"Next Stage: {response4.next_stage}")
    print()
    
    # Show final conversation state
    print("5. FINAL CONVERSATION STATE")
    print("-" * 40)
    
    final_conversation = orchestrator.get_conversation(conversation_id)
    print(f"Total Messages: {len(final_conversation.messages)}")
    print(f"Final Stage: {final_conversation.current_stage}")
    
    if final_conversation.requirements:
        print(f"Requirements Count: {len(final_conversation.requirements.identified_requirements)}")
    
    if final_conversation.generation and final_conversation.generation.generated_code:
        print("Code Generated: Yes")
    
    print(f"Created: {final_conversation.created_at}")
    print(f"Updated: {final_conversation.updated_at}")


async def demo_stage_detection():
    """Demonstrate automatic stage detection."""
    
    print("\n=== STAGE DETECTION DEMO ===\n")
    
    orchestrator = ConversationOrchestrator()
    
    # Create conversation with some history
    request = ConversationRequest(
        message="I need help with a packaging machine control system"
    )
    
    response = await orchestrator.process_message(request)
    conversation_id = response.conversation_id
    
    # Add more messages to build context
    messages = [
        "The machine needs to control 3 conveyor belts and a robotic arm",
        "It operates at 220V AC and needs safety light curtains",
        "The cycle time should be under 30 seconds per package"
    ]
    
    for msg in messages:
        request = ConversationRequest(
            conversation_id=conversation_id,
            message=msg
        )
        response = await orchestrator.process_message(request)
        print(f"Message: {msg[:50]}...")
        print(f"Detected Stage: {response.stage}")
        print(f"Stage Progress: {response.stage_progress}")
        print()


if __name__ == "__main__":
    asyncio.run(demo_conversation())
    asyncio.run(demo_stage_detection())