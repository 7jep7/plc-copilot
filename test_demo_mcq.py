#!/usr/bin/env python3
"""
Quick test to verify demo project MCQ generation and parsing.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.prompt_templates import PromptTemplateFactory
from app.schemas.conversation import ConversationStage

# Mock conversation state
class MockState:
    def __init__(self):
        self.current_stage = ConversationStage.PROJECT_KICKOFF
        self.messages = []
        self.extracted_documents = []
        self.requirements = None

def main():
    print("🧪 TESTING DEMO PROJECT MCQ GENERATION")
    print("="*60)
    
    # Test with non-industrial input
    user_message = "i want to sleep"
    state = MockState()
    
    template = PromptTemplateFactory.get_template(ConversationStage.PROJECT_KICKOFF)
    
    print(f"📤 User Message: '{user_message}'")
    print("\n🔍 Testing non-industrial detection...")
    
    # Check if _detect_non_industrial_input works
    is_non_industrial = template._detect_non_industrial_input(user_message)
    print(f"Non-industrial detected: {is_non_industrial}")
    
    if is_non_industrial:
        print("\n✅ Should trigger demo project suggestions!")
        demo_suggestions = template._generate_demo_project_suggestions()
        print("\n🎯 Generated Demo Project MCQ:")
        print("-" * 40)
        print(demo_suggestions)
        print("-" * 40)
        
        # Check MCQ format
        if "**MCQ_START**" in demo_suggestions and "**MCQ_END**" in demo_suggestions:
            print("\n✅ MCQ format is correct!")
        else:
            print("\n❌ MCQ format is missing!")
    else:
        print("\n❌ Should have triggered demo projects but didn't!")
    
    # Now test the full user prompt
    print(f"\n📝 FULL USER PROMPT GENERATION:")
    print("="*50)
    user_prompt = template.build_user_prompt(user_message, state)
    print(user_prompt)
    print("="*50)
    
    # Verify the user prompt contains demo suggestions
    if "DEMO PROJECT SUGGESTIONS:" in user_prompt:
        print("\n✅ Demo project suggestions are in user prompt!")
        if "**MCQ_START**" in user_prompt:
            print("✅ MCQ format is in user prompt!")
        else:
            print("❌ MCQ format is NOT in user prompt!")
    else:
        print("\n❌ Demo project suggestions are NOT in user prompt!")

if __name__ == "__main__":
    main()