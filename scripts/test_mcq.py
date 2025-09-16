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
    print()
    
    # Check new structured MCQ fields
    print("📊 MCQ STRUCTURE ANALYSIS:")
    print(f"   is_mcq: {response.is_mcq}")
    print(f"   mcq_question: {response.mcq_question}")
    print(f"   mcq_options: {response.mcq_options}")
    print()
    
    if response.is_mcq:
        print("✅ MCQ format successfully detected!")
        print("✅ Structured MCQ data available for frontend")
        print(f"   Question: {response.mcq_question}")
        print(f"   Options count: {len(response.mcq_options)}")
        for i, option in enumerate(response.mcq_options):
            print(f"     {chr(65+i)}) {option}")
    else:
        print("⚠️  No MCQ in this response")
        print("This might be normal if open questions were more appropriate")
        
        # Check for old format indicators
        mcq_indicators = ["A)", "B)", "C)", "**Options**", "**Question**"]
        has_old_mcq = any(indicator in response.response for indicator in mcq_indicators)
        if has_old_mcq:
            print("❌ Old MCQ format detected but not parsed!")
            print("The parsing logic may need adjustment.")


if __name__ == "__main__":
    asyncio.run(test_mcq_functionality())