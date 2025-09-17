#!/usr/bin/env python3
"""
Interactive Terminal Test for PLC-Copilot Conversation System

This script provides a simple terminal interface to test:
1. Demo project suggestions for non-industrial inputs
2. MCQ format and context persistence  
3. Structured Text focus
4. Stage progression
5. Datasheet awareness
6. Concise questions

Usage: python interactive_test.py
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.prompt_templates import PromptTemplateFactory
from app.schemas.conversation import ConversationStage


def print_header(title: str):
    """Print a nice header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print('-'*40)


class SimpleConversation:
    """Simple conversation for testing."""
    def __init__(self):
        self.current_stage = ConversationStage.PROJECT_KICKOFF
        self.messages = []
        self.qa_answers = []
        self.extracted_documents = []
        self.requirements = None
        self.qa = None
        self.generation = None
        self.refinement = None


def test_user_input(user_input: str, stage: ConversationStage = ConversationStage.PROJECT_KICKOFF):
    """Test a user input and show the results."""
    print_header(f"TESTING: '{user_input}'")
    
    conversation = SimpleConversation()
    conversation.current_stage = stage
    
    # Add some mock Q&A answers if testing context persistence
    if "context" in user_input.lower() or "mcq" in user_input.lower():
        conversation.qa_answers = [
            "Safety interlocks with emergency stops",
            "VFD motor control",
            "Photoelectric sensors for detection"
        ]
    
    template = PromptTemplateFactory.get_template(stage)
    
    print(f"🎯 Stage: {stage.value}")
    print(f"📝 Template: {template.__class__.__name__}")
    
    try:
        system_prompt = template.build_system_prompt(conversation)
        user_prompt = template.build_user_prompt(user_input, conversation)
        
        print_section("🤖 SYSTEM PROMPT")
        print(system_prompt)
        
        print_section("👤 USER PROMPT")  
        print(user_prompt)
        
        # Analysis
        print_section("📊 ANALYSIS")
        
        combined_text = (system_prompt + " " + user_prompt).lower()
        
        # Check for key features
        checks = [
            ("Structured Text mentions", "structured text" in combined_text),
            ("Demo project suggestions", "demo project" in user_prompt.lower() or "example project" in user_prompt.lower()),
            ("MCQ format", "**mcq_start**" in combined_text and "**mcq_end**" in combined_text),
            ("Chat message format", "<chat_message>" in combined_text),
            ("Datasheet awareness", "datasheet" in combined_text),
            ("Concise instructions", any(word in combined_text for word in ["concise", "short", "brief", "focused"])),
            ("Safety focus", "safety" in combined_text),
            ("PLC focus", "plc" in combined_text or "programmable logic" in combined_text)
        ]
        
        for check_name, result in checks:
            status = "✅" if result else "❌"
            print(f"{status} {check_name}")
        
        # Count key terms
        st_count = combined_text.count("structured text")
        plc_count = combined_text.count("plc") + combined_text.count("programmable logic controller")
        mcq_count = combined_text.count("mcq")
        
        print(f"\n📈 METRICS:")
        print(f"  Structured Text mentions: {st_count}")
        print(f"  PLC mentions: {plc_count}")
        print(f"  MCQ mentions: {mcq_count}")
        print(f"  System prompt length: {len(system_prompt)} chars")
        print(f"  User prompt length: {len(user_prompt)} chars")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def interactive_mode():
    """Run interactive mode."""
    print_header("🧪 PLC-COPILOT INTERACTIVE TESTER")
    
    print("This tool tests the conversation system improvements:")
    print("1. ✅ MCQ chat messages without answer options")
    print("2. ✅ MCQ answer context persistence")
    print("3. ✅ Context window management")
    print("4. ✅ Structured Text focus")
    print("5. ✅ Concise questions and MCQ usage")
    print("6. ✅ Datasheet awareness")
    print("7. ✅ Demo project suggestions for non-industrial inputs")
    
    print("\n💡 Try these test cases:")
    print("  - Non-industrial: 'I want to build a web app'")
    print("  - Industrial: 'Automate conveyor with safety'")
    print("  - Vague: 'Help with automation'")
    print("  - MCQ context: 'Add safety to mcq context'")
    
    stages = {
        "1": ConversationStage.PROJECT_KICKOFF,
        "2": ConversationStage.GATHER_REQUIREMENTS,
        "3": ConversationStage.CODE_GENERATION,
        "4": ConversationStage.REFINEMENT_TESTING
    }
    
    while True:
        print(f"\n{'-'*40}")
        user_input = input("👤 Enter your message (or 'quit' to exit): ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        
        if not user_input:
            continue
        
        print("\n🎯 Select conversation stage:")
        print("1. Project Kickoff (initial user request)")
        print("2. Gather Requirements (asking questions)")
        print("3. Code Generation (creating ST code)")
        print("4. Refinement Testing (improving code)")
        
        stage_choice = input("Stage (1-4, default 1): ").strip() or "1"
        
        if stage_choice in stages:
            test_user_input(user_input, stages[stage_choice])
        else:
            print("❌ Invalid stage choice, using Project Kickoff")
            test_user_input(user_input, ConversationStage.PROJECT_KICKOFF)


def preset_tests():
    """Run preset tests for key scenarios."""
    print_header("🎪 PRESET TESTS")
    
    test_cases = [
        ("Non-industrial input", "I want to build a mobile app", ConversationStage.PROJECT_KICKOFF),
        ("Industrial input", "Automate conveyor with VFD control", ConversationStage.PROJECT_KICKOFF),
        ("Requirements gathering", "What safety features do you need?", ConversationStage.GATHER_REQUIREMENTS),
        ("Code generation", "Generate the PLC code", ConversationStage.CODE_GENERATION),
        ("Refinement", "Add emergency stop logic", ConversationStage.REFINEMENT_TESTING),
    ]
    
    for test_name, test_input, stage in test_cases:
        print(f"\n{test_name.upper()}:")
        test_user_input(test_input, stage)
        
        input("\nPress Enter to continue to next test...")


def main():
    """Main function."""
    print("🧪 PLC-Copilot Conversation System Tester")
    print("\nChoose testing mode:")
    print("1. Interactive mode (enter your own messages)")
    print("2. Preset tests (run predefined test cases)")
    
    choice = input("\nEnter choice (1-2, default 1): ").strip() or "1"
    
    if choice == "2":
        preset_tests()
    else:
        interactive_mode()


if __name__ == "__main__":
    main()