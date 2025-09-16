#!/usr/bin/env python3
"""Quick test for MCQ functionality in gather requirements stage."""

import asyncio
from app.schemas.conversation import ConversationRequest, ConversationStage
from app.services.conversation_orchestrator import ConversationOrchestrator


async def test_mcq_functionality():
    """Test MCQ functionality specifically."""
    
    orchestrator = ConversationOrchestrator()
    
    print("🧪 TESTING MCQ FUNCTIONALITY")
    print("=" * 50)
    
    # Create a conversation and force it into gather requirements stage
    request = ConversationRequest(
        message="I need a safety system for my production line but I'm not sure what safety rating I need.",
        force_stage=ConversationStage.GATHER_REQUIREMENTS
    )
    
    response = await orchestrator.process_message(request)
    
    print(f"Stage: {response.stage}")
    print(f"Response:\n{response.response}")
    
    # Check for MCQ indicators
    mcq_indicators = ["A)", "B)", "C)", "**Options**", "**Question**"]
    has_mcq = any(indicator in response.response for indicator in mcq_indicators)
    
    if has_mcq:
        print("\n✅ MCQ format successfully detected!")
    else:
        print("\n⚠️  MCQ format not used in this response")
        print("This might be normal if open questions were more appropriate")


if __name__ == "__main__":
    asyncio.run(test_mcq_functionality())