#!/usr/bin/env python3
"""
Interactive Terminal Test with Real LLM Responses

This script provides a comprehensive terminal interface to test the PLC-Copilot conversation system
with actual LLM responses, showing:
1. Demo project suggestions for non-industrial inputs
2. MCQ format and context persistence  
3. Structured Text focus across stages
4. Real conversation flow with LLM responses
5. Stage progression and transitions

Usage: python interactive_llm_test.py
"""

import asyncio
import sys
import os
import json
from typing import Dict, Any, Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.conversation_orchestrator import ConversationOrchestrator
from app.schemas.conversation import ConversationRequest, ConversationStage


def print_header(title: str):
    """Print a nice header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'-'*50}")
    print(f"  {title}")
    print('-'*50)


def print_result(status: str, message: str):
    """Print a status result."""
    print(f"{status} {message}")


class InteractiveLLMTester:
    """Interactive tester with real LLM responses."""
    
    def __init__(self):
        self.orchestrator = ConversationOrchestrator()
        self.conversation_id = None
        self.message_count = 0
    
    def display_conversation_info(self, response):
        """Display conversation information."""
        print_section("📊 CONVERSATION INFO")
        print(f"Conversation ID: {response.conversation_id}")
        print(f"Current Stage: {response.stage.value}")
        print(f"Next Stage: {response.next_stage.value if response.next_stage else 'None'}")
        print(f"Message Count: {self.message_count}")
        
        if hasattr(response, 'stage_progress') and response.stage_progress:
            print(f"Stage Progress: {response.stage_progress}")
    
    def display_llm_response(self, response):
        """Display the LLM response details."""
        print_section("🤖 LLM RESPONSE & API FORMAT")
        
        # Color codes
        CYAN = '\033[96m'
        MAGENTA = '\033[95m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        GREEN = '\033[92m'
        RESET = '\033[0m'
        BOLD = '\033[1m'
        
        print(f"{CYAN}{BOLD}💬 Chat Message (what frontend displays):{RESET}")
        print(f"{CYAN}{'='*40}{RESET}")
        print(f"{CYAN}{response.response}{RESET}")
        print(f"{CYAN}{'='*40}{RESET}")
        
        # MCQ Details with enhanced formatting
        if response.is_mcq:
            print(f"\n{YELLOW}{BOLD}❓ MCQ DETECTED - API PARSING SUCCESSFUL!{RESET}")
            print(f"{YELLOW}{'='*50}{RESET}")
            print(f"{YELLOW}📋 Question: {response.mcq_question}{RESET}")
            print(f"{YELLOW}🔢 Is Multiselect: {response.is_multiselect}{RESET}")
            print(f"{YELLOW}📝 Options:{RESET}")
            for i, option in enumerate(response.mcq_options, 1):
                print(f"{YELLOW}    {chr(64+i)}) {option}{RESET}")
            print(f"{YELLOW}{'='*50}{RESET}")
            
            # Show API endpoint format
            print(f"\n{MAGENTA}{BOLD}🌐 API ENDPOINT FORMAT FOR FRONTEND:{RESET}")
            print(f"{MAGENTA}{{")
            print(f'  "conversation_id": "{response.conversation_id}",')
            print(f'  "stage": "{response.stage.value}",')
            print(f'  "response": "{response.response[:50]}...",')
            print(f'  "is_mcq": {str(response.is_mcq).lower()},')
            print(f'  "mcq_question": "{response.mcq_question}",')
            print(f'  "mcq_options": {response.mcq_options},')
            print(f'  "is_multiselect": {str(response.is_multiselect).lower()}')
            print(f"}}{RESET}")
            
        else:
            print(f"\n{RED}❌ NO MCQ DETECTED{RESET}")
            print(f"{RED}This should have been an MCQ for non-industrial input!{RESET}")
        
        # Generated Code
        if response.generated_code:
            print(f"\n{GREEN}{BOLD}💻 GENERATED CODE:{RESET}")
            print(f"{GREEN}{'='*40}{RESET}")
            print(f"{GREEN}{response.generated_code}{RESET}")
            print(f"{GREEN}{'='*40}{RESET}")
        
        # Suggested Actions
        if response.suggested_actions:
            print(f"\n💡 SUGGESTED ACTIONS:")
            for i, action in enumerate(response.suggested_actions, 1):
                print(f"  {i}. {action}")
    
    def display_prompt_details(self, conversation_id: str, user_message: str):
        """Display the prompts that will be sent to the LLM."""
        # Check non-industrial detection logic directly
        print_section("🔍 NON-INDUSTRIAL DETECTION ANALYSIS")
        
        from app.services.prompt_templates import ProjectKickoffTemplate
        template_instance = ProjectKickoffTemplate()
        is_non_industrial = template_instance._detect_non_industrial_input(user_message)
        
        print(f"📝 Input Message: '{user_message}'")
        print(f"🎯 Non-Industrial Detected: {is_non_industrial}")
        
        if is_non_industrial:
            demo_suggestions = template_instance._generate_demo_project_suggestions()
            print(f"✅ Demo Project MCQ Generated: {len(demo_suggestions)} chars")
            if "**MCQ_START**" in demo_suggestions:
                print("✅ MCQ format markers present")
            else:
                print("❌ MCQ format markers missing")
        else:
            print("❌ No demo projects generated (industrial input detected)")
        
        if not conversation_id or conversation_id not in self.orchestrator.conversations:
            print("⚠️ No conversation state available for full prompt display")
            return
        
        conversation = self.orchestrator.conversations[conversation_id]
        
        print_section("📝 PROMPT DETAILS SENT TO LLM")
        
        from app.services.prompt_templates import PromptTemplateFactory
        template = PromptTemplateFactory.get_template(conversation.current_stage)
        
        system_prompt = template.build_system_prompt(conversation)
        user_prompt = template.build_user_prompt(user_message, conversation)
        
        print(f"🎯 Stage: {conversation.current_stage.value}")
        print(f"📝 Template: {template.__class__.__name__}")
        print(f"📏 System Prompt Length: {len(system_prompt)} chars")
        print(f"📏 User Prompt Length: {len(user_prompt)} chars")
        
        # Color codes for better readability
        BLUE = '\033[94m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        RESET = '\033[0m'
        BOLD = '\033[1m'
        
        print(f"\n{BLUE}{BOLD}🤖 SYSTEM PROMPT:{RESET}")
        print(f"{BLUE}{'='*50}{RESET}")
        print(f"{BLUE}{system_prompt}{RESET}")
        
        print(f"\n{GREEN}{BOLD}👤 USER PROMPT:{RESET}")
        print(f"{GREEN}{'='*50}{RESET}")
        print(f"{GREEN}{user_prompt}{RESET}")
        
        # Check for demo project suggestions in user prompt
        if "demo project" in user_prompt.lower() or "mcq_start" in user_prompt.lower():
            print(f"\n{YELLOW}{BOLD}🎯 DEMO PROJECT MCQ DETECTED IN USER PROMPT!{RESET}")
            if "**MCQ_START**" in user_prompt:
                print(f"{YELLOW}✅ MCQ format markers found{RESET}")
            else:
                print(f"{RED}❌ MCQ format markers NOT found{RESET}")
        
        print(f"\n{BOLD}� PROMPT ANALYSIS:{RESET}")
        print(f"  • Non-industrial detection: {'Yes' if 'non-industrial' in user_prompt.lower() else 'No'}")
        print(f"  • Demo suggestions: {'Yes' if 'demo project' in user_prompt.lower() else 'No'}")
        print(f"  • MCQ format: {'Yes' if 'mcq_start' in user_prompt.lower() else 'No'}")
        print(f"  • Structured Text focus: {system_prompt.lower().count('structured text')} mentions")
    
    def get_mcq_response(self, question: str, options: list, is_multiselect: bool = False) -> Dict[str, Any]:
        """Handle MCQ response input."""
        print_section("❓ MCQ RESPONSE REQUIRED")
        print(f"Question: {question}")
        print("Options:")
        for i, option in enumerate(options, 1):
            print(f"  {chr(64+i)}) {option}")
        
        if is_multiselect:
            print("\n(Multiple selection allowed - enter letters separated by commas, e.g., A,C)")
            selection = input("Select options (A,B,C...): ").upper().strip()
            selected_letters = [s.strip() for s in selection.split(',') if s.strip()]
        else:
            print("\n(Single selection)")
            selection = input("Select option (A,B,C...): ").upper().strip()
            selected_letters = [selection] if selection else []
        
        # Convert letters to option text
        selected_options = []
        for letter in selected_letters:
            idx = ord(letter) - ord('A')
            if 0 <= idx < len(options):
                selected_options.append(options[idx])
        
        return {
            "question": question,
            "selected_options": selected_options,
            "is_multiselect": is_multiselect
        }
    
    async def process_message(self, user_message: str, mcq_response: Optional[Dict] = None):
        """Process a message and return the response."""
        request = ConversationRequest(
            conversation_id=self.conversation_id,
            message=user_message,
            mcq_response=mcq_response
        )
        
        self.message_count += 1
        
        print_header(f"📨 PROCESSING MESSAGE #{self.message_count}")
        
        # Show prompt details before processing
        if self.conversation_id:
            self.display_prompt_details(self.conversation_id, user_message)
        
        print(f"\n⚙️ Sending request to OpenAI...")
        print(f"📤 Message: {user_message}")
        if mcq_response:
            print(f"📋 MCQ Response: {mcq_response}")
        
        try:
            response = await self.orchestrator.process_message(request)
            
            # Store conversation ID for subsequent messages
            if not self.conversation_id:
                self.conversation_id = response.conversation_id
            
            self.display_conversation_info(response)
            self.display_llm_response(response)
            
            return response
            
        except Exception as e:
            print(f"❌ Error processing message: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    async def run_interactive_test(self):
        """Run the interactive test."""
        print_header("🧪 PLC-COPILOT INTERACTIVE LLM TESTER")
        
        print("This test shows real LLM responses for the conversation system:")
        print("✅ 1. Demo project suggestions for non-industrial inputs")
        print("✅ 2. MCQ format and context persistence")
        print("✅ 3. Structured Text focus across stages")
        print("✅ 4. Real conversation flow with OpenAI")
        print("✅ 5. Stage progression and transitions")
        
        print("\n💡 Test cases to try:")
        print("  - Non-industrial: 'I want to build a mobile app'")
        print("  - Industrial: 'I need to automate a conveyor system'")
        print("  - Vague: 'Help me with automation'")
        print("  - Specific: 'Create PLC code for temperature control'")
        
        print("\n🔧 Commands:")
        print("  - Type 'help' for guidance")
        print("  - Type 'status' to see conversation state")
        print("  - Type 'quit' to exit")
        
        while True:
            try:
                print(f"\n{'-'*50}")
                user_input = input("👤 Your message: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if user_input.lower() == 'help':
                    print("\n📋 HELP:")
                    print("- Enter any message to test the conversation system")
                    print("- Non-industrial requests will trigger demo project suggestions")
                    print("- Industrial requests will proceed with requirements gathering")
                    print("- MCQs will be presented for you to respond to")
                    print("- Watch how the conversation progresses through stages")
                    continue
                
                if user_input.lower() == 'status':
                    if self.conversation_id and self.conversation_id in self.orchestrator.conversations:
                        conv = self.orchestrator.conversations[self.conversation_id]
                        print(f"\n📊 CONVERSATION STATUS:")
                        print(f"  ID: {self.conversation_id}")
                        print(f"  Stage: {conv.current_stage.value}")
                        print(f"  Messages: {len(conv.messages)}")
                        if conv.requirements:
                            print(f"  Requirements: {len(conv.requirements.identified_requirements) if conv.requirements.identified_requirements else 0}")
                        if conv.qa and conv.qa.answers_received:
                            print(f"  Q&A Answers: {len(conv.qa.answers_received)}")
                    else:
                        print("No active conversation")
                    continue
                
                if not user_input:
                    print("❌ Please enter a message.")
                    continue
                
                # Process the message
                response = await self.process_message(user_input)
                
                if not response:
                    continue
                
                # Handle MCQ if present
                if response.is_mcq and response.mcq_question and response.mcq_options:
                    print(f"\n🎯 MCQ DETECTED - Testing MCQ context persistence...")
                    
                    # Get MCQ response from user
                    mcq_response_data = self.get_mcq_response(
                        response.mcq_question,
                        response.mcq_options,
                        response.is_multiselect
                    )
                    
                    # Get additional user message
                    print(f"\n💬 Any additional context? (or press Enter to continue)")
                    additional_message = input("Additional message: ").strip() or "Thank you for the options."
                    
                    # Process follow-up with MCQ response
                    followup_response = await self.process_message(additional_message, mcq_response_data)
                    
                    if followup_response:
                        print(f"\n🔍 MCQ CONTEXT VERIFICATION:")
                        # Check if the conversation state includes our MCQ answers
                        if self.conversation_id in self.orchestrator.conversations:
                            conv = self.orchestrator.conversations[self.conversation_id]
                            if conv.qa and conv.qa.answers_received:
                                print("✅ MCQ answers found in conversation context:")
                                for answer in conv.qa.answers_received[-2:]:
                                    print(f"  - {answer}")
                            else:
                                print("❌ MCQ answers not found in conversation context!")
                
                print(f"\n🔄 Ready for next message...")
                
            except KeyboardInterrupt:
                print("\n\n👋 Test interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()
                print("Continuing...")


async def main():
    """Main entry point."""
    tester = InteractiveLLMTester()
    await tester.run_interactive_test()


if __name__ == "__main__":
    print("🚀 Starting Interactive LLM Test...")
    print("This will make real API calls to OpenAI!")
    
    confirm = input("Continue? (y/N): ").strip().lower()
    if confirm in ['y', 'yes']:
        asyncio.run(main())
    else:
        print("Test cancelled.")