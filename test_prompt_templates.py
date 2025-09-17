#!/usr/bin/env python3
"""
Simple test script to verify prompt templates and key functionality.

This script tests the prompt templates directly without requiring the full orchestrator setup.
"""

import sys
import os
from typing import List, Optional
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.prompt_templates import PromptTemplateFactory
from app.schemas.conversation import ConversationStage


# Mock conversation class for testing
class MockConversation:
    def __init__(self):
        self.conversation_id = "test-123"
        self.current_stage = ConversationStage.PROJECT_KICKOFF
        self.messages = []
        self.requirements = None
        self.qa = None
        self.generation = None
        self.refinement = None
        self.extracted_documents = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()


def print_separator(title: str):
    """Print a visual separator with title."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print('='*80)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'-'*60}")
    print(f"  {title}")
    print('-'*60)


def test_demo_project_suggestions():
    """Test demo project suggestions for non-industrial inputs."""
    print_separator("🎯 TESTING DEMO PROJECT SUGGESTIONS")
    
    # Create a mock conversation
    conversation = MockConversation()
    
    # Test with non-industrial input
    template = PromptTemplateFactory.get_template(ConversationStage.PROJECT_KICKOFF)
    
    test_inputs = [
        "I want to build a web application",
        "Help me with mobile app development", 
        "I need to create a game",
        "Can you help me with data analysis?",
        "I want to learn programming"
    ]
    
    for test_input in test_inputs:
        print_section(f"Testing input: '{test_input}'")
        
        system_prompt = template.build_system_prompt(conversation)
        user_prompt = template.build_user_prompt(test_input, conversation)
        
        print("🤖 SYSTEM PROMPT:")
        print('-'*40)
        print(system_prompt)
        
        print("\n👤 USER PROMPT:")
        print('-'*40)
        print(user_prompt)
        
        # Check for demo project mention
        if "demo project" in system_prompt.lower() or "example project" in system_prompt.lower():
            print("✅ Demo project suggestions are included in system prompt")
        else:
            print("❌ Demo project suggestions NOT found in system prompt")


def test_structured_text_focus():
    """Test that prompts emphasize Structured Text."""
    print_separator("🔧 TESTING STRUCTURED TEXT FOCUS")
    
    conversation = MockConversation()
    
    for stage in ConversationStage:
        print_section(f"Stage: {stage.value}")
        
        template = PromptTemplateFactory.get_template(stage)
        system_prompt = template.build_system_prompt(conversation)
        
        # Check for Structured Text mentions
        st_mentions = system_prompt.lower().count("structured text")
        plc_mentions = system_prompt.lower().count("programmable logic controller")
        
        print(f"Structured Text mentions: {st_mentions}")
        print(f"PLC mentions: {plc_mentions}")
        
        if st_mentions > 0:
            print("✅ Structured Text is mentioned")
        else:
            print("❌ Structured Text is NOT mentioned")
        
        # Show relevant parts of the prompt
        lines = system_prompt.split('\n')
        st_lines = [line for line in lines if 'structured text' in line.lower() or 'plc' in line.lower()]
        if st_lines:
            print("📝 Relevant lines:")
            for line in st_lines[:3]:  # Show first 3 relevant lines
                print(f"  - {line.strip()}")


def test_mcq_chat_message_format():
    """Test that MCQ prompts don't include answer options in chat messages."""
    print_separator("❓ TESTING MCQ CHAT MESSAGE FORMAT")
    
    conversation = MockConversation()
    
    # Test requirements gathering stage (most likely to have MCQs)
    template = PromptTemplateFactory.get_template(ConversationStage.GATHER_REQUIREMENTS)
    system_prompt = template.build_system_prompt(conversation)
    
    print("🤖 REQUIREMENTS GATHERING SYSTEM PROMPT:")
    print('-'*40)
    print(system_prompt)
    
    # Check for MCQ instructions
    if "mcq" in system_prompt.lower():
        print("✅ MCQ functionality is mentioned")
        
        # Look for instructions about not including options in chat message
        if "options below" in system_prompt.lower() or "don't include" in system_prompt.lower():
            print("✅ Instructions found to exclude options from chat message")
        else:
            print("❌ No clear instructions to exclude options from chat message")
    else:
        print("❌ MCQ functionality is NOT mentioned")


def test_datasheet_awareness():
    """Test that prompts mention datasheet requests."""
    print_separator("📄 TESTING DATASHEET AWARENESS")
    
    conversation = MockConversation()
    
    for stage in [ConversationStage.GATHER_REQUIREMENTS, ConversationStage.CODE_GENERATION]:
        print_section(f"Stage: {stage.value}")
        
        template = PromptTemplateFactory.get_template(stage)
        system_prompt = template.build_system_prompt(conversation)
        
        # Check for datasheet mentions
        if "datasheet" in system_prompt.lower():
            print("✅ Datasheet awareness is included")
            
            # Show datasheet-related lines
            lines = system_prompt.split('\n')
            datasheet_lines = [line for line in lines if 'datasheet' in line.lower()]
            for line in datasheet_lines:
                print(f"  📋 {line.strip()}")
        else:
            print("❌ Datasheet awareness is NOT included")


def test_concise_questions():
    """Test that prompts encourage concise questions."""
    print_separator("💬 TESTING CONCISE QUESTIONS INSTRUCTION")
    
    conversation = MockConversation()
    template = PromptTemplateFactory.get_template(ConversationStage.GATHER_REQUIREMENTS)
    system_prompt = template.build_system_prompt(conversation)
    
    print("🤖 REQUIREMENTS GATHERING SYSTEM PROMPT:")
    print('-'*40)
    print(system_prompt)
    
    # Check for concise instruction
    concise_keywords = ["concise", "short", "brief", "quick"]
    found_keywords = [kw for kw in concise_keywords if kw in system_prompt.lower()]
    
    if found_keywords:
        print(f"✅ Concise question instructions found: {', '.join(found_keywords)}")
    else:
        print("❌ No concise question instructions found")


def main():
    """Main test function."""
    print_separator("🧪 PLC-COPILOT PROMPT TEMPLATE TESTER")
    
    print("Testing key improvements in prompt templates:")
    print("1. Demo project suggestions for non-industrial inputs")
    print("2. Structured Text focus")
    print("3. MCQ chat message format")
    print("4. Datasheet awareness") 
    print("5. Concise questions instruction")
    
    try:
        test_demo_project_suggestions()
        test_structured_text_focus()
        test_mcq_chat_message_format()
        test_datasheet_awareness()
        test_concise_questions()
        
        print_separator("✅ ALL TESTS COMPLETED")
        
    except Exception as e:
        print(f"\n❌ Error running tests: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()