#!/usr/bin/env python3
"""
Interactive test script to verify OpenAI interaction fixes and conversation flow.

This script allows you to test all the improvements made to the conversation system:
1. MCQ chat messages without answer options
2. MCQ answer context persistence
3. Context window management
4. Structured Text focus
5. Concise questions and MCQ usage
6. Datasheet awareness
7. Demo project suggestions for non-industrial inputs

Usage: python test_conversation_flow.py
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any, Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.conversation_orchestrator import ConversationOrchestrator
from app.schemas.conversation import ConversationRequest, ConversationStage
from app.services.prompt_templates import PromptTemplateFactory


class ConversationTester:
    def __init__(self):
        self.orchestrator = ConversationOrchestrator()
        self.conversation_id = None
        self.message_count = 0
    
    def print_separator(self, title: str):
        """Print a visual separator with title."""
        print(f"\n{'='*80}")
        print(f"  {title}")
        print('='*80)
    
    def print_section(self, title: str):
        """Print a section header."""
        print(f"\n{'-'*60}")
        print(f"  {title}")
        print('-'*60)
    
    def display_conversation_state(self, conversation):
        """Display detailed conversation state information."""
        self.print_section("📊 CONVERSATION STATE")
        
        print(f"Conversation ID: {conversation.conversation_id}")
        print(f"Current Stage: {conversation.current_stage.value}")
        print(f"Total Messages: {len(conversation.messages)}")
        print(f"Created: {conversation.created_at}")
        print(f"Updated: {conversation.updated_at}")
        
        # Requirements state
        if conversation.requirements:
            print(f"\n📋 Requirements:")
            print(f"  User Query: {conversation.requirements.user_query}")
            print(f"  Identified Requirements: {len(conversation.requirements.identified_requirements)}")
            if conversation.requirements.identified_requirements:
                for i, req in enumerate(conversation.requirements.identified_requirements, 1):
                    print(f"    {i}. {req}")
            print(f"  Confidence Level: {conversation.requirements.confidence_level}")
        
        # Q&A state
        if conversation.qa:
            print(f"\n❓ Q&A State:")
            print(f"  Questions Asked: {len(conversation.qa.questions_asked)}")
            print(f"  Answers Received: {len(conversation.qa.answers_received)}")
            if conversation.qa.answers_received:
                print(f"  Recent Answers:")
                for i, answer in enumerate(conversation.qa.answers_received[-3:], 1):
                    print(f"    {i}. {answer}")
        
        # Generation state
        if conversation.generation:
            print(f"\n💻 Code Generation:")
            print(f"  Code Generated: {bool(conversation.generation.generated_code)}")
            if conversation.generation.generated_code:
                print(f"  Code Length: {len(conversation.generation.generated_code)} chars")
        
        # Refinement state
        if conversation.refinement:
            print(f"\n🔧 Refinement:")
            print(f"  Refinement Requests: {len(conversation.refinement.refinement_requests)}")
            print(f"  User Feedback: {len(conversation.refinement.user_feedback)}")
        
        # Document state
        if hasattr(conversation, 'extracted_documents') and conversation.extracted_documents:
            print(f"\n📄 Documents:")
            for doc in conversation.extracted_documents:
                print(f"  - {doc.get('filename', 'Unknown')} ({doc.get('document_type', 'UNKNOWN')})")
    
    def display_prompt_details(self, stage: ConversationStage, conversation, user_message: str):
        """Display the prompt details that will be sent to the LLM."""
        self.print_section("🤖 PROMPT DETAILS")
        
        template = PromptTemplateFactory.get_template(stage)
        system_prompt = template.build_system_prompt(conversation)
        user_prompt = template.build_user_prompt(user_message, conversation)
        model_config = template.get_model_config()
        
        print(f"Stage: {stage.value}")
        print(f"Template Class: {template.__class__.__name__}")
        print(f"Model Config: {model_config}")
        
        print(f"\n📝 SYSTEM PROMPT:")
        print('-'*40)
        print(system_prompt)
        
        print(f"\n👤 USER PROMPT:")
        print('-'*40)
        print(user_prompt)
        
        # Show message history context
        if conversation.messages:
            print(f"\n📚 MESSAGE HISTORY CONTEXT (last 5 messages):")
            print('-'*40)
            recent_messages = conversation.messages[-5:]
            for i, msg in enumerate(recent_messages, 1):
                print(f"{i}. [{msg.role.value}]: {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}")
    
    def display_api_response(self, response):
        """Display the API response details."""
        self.print_section("🌐 API RESPONSE")
        
        print(f"Conversation ID: {response.conversation_id}")
        print(f"Current Stage: {response.stage.value}")
        print(f"Next Stage: {response.next_stage.value if response.next_stage else 'None'}")
        
        print(f"\n💬 CHAT MESSAGE:")
        print('-'*40)
        print(response.response)
        
        # MCQ Details
        if response.is_mcq:
            print(f"\n❓ MCQ DETAILS:")
            print(f"  Is MCQ: {response.is_mcq}")
            print(f"  Is Multiselect: {response.is_multiselect}")
            print(f"  Question: {response.mcq_question}")
            print(f"  Options:")
            for i, option in enumerate(response.mcq_options, 1):
                print(f"    {chr(64+i)}) {option}")
        
        # Generated Code
        if response.generated_code:
            print(f"\n💻 GENERATED CODE:")
            print('-'*40)
            print(response.generated_code)
        
        # Stage Progress
        if response.stage_progress:
            print(f"\n📊 STAGE PROGRESS:")
            for key, value in response.stage_progress.items():
                print(f"  {key}: {value}")
        
        # Requirements Progress
        if hasattr(response, 'gathering_requirements_estimated_progress') and response.gathering_requirements_estimated_progress is not None:
            print(f"  Requirements Progress: {response.gathering_requirements_estimated_progress:.1%}")
        
        # Suggested Actions
        if response.suggested_actions:
            print(f"\n💡 SUGGESTED ACTIONS:")
            for i, action in enumerate(response.suggested_actions, 1):
                print(f"  {i}. {action}")
    
    def get_user_input(self, prompt: str = "Your message") -> str:
        """Get user input with a nice prompt."""
        print(f"\n{prompt}:")
        print("─" * len(prompt))
        return input(">>> ").strip()
    
    def get_mcq_response(self, question: str, options: list, is_multiselect: bool = False) -> Dict[str, Any]:
        """Handle MCQ response input."""
        print(f"\n❓ MCQ Response Required:")
        print(f"Question: {question}")
        print(f"Options:")
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
    
    async def run_conversation_test(self):
        """Run the interactive conversation test."""
        self.print_separator("🧪 PLC-COPILOT CONVERSATION FLOW TESTER")
        
        print("This test script allows you to verify all the OpenAI interaction improvements:")
        print("1. ✅ MCQ chat messages without answer options")
        print("2. ✅ MCQ answer context persistence")
        print("3. ✅ Context window management")
        print("4. ✅ Structured Text focus")
        print("5. ✅ Concise questions and MCQ usage")
        print("6. ✅ Datasheet awareness")
        print("7. ✅ Demo project suggestions for non-industrial inputs")
        
        print("\n💡 Try these test cases:")
        print("  - Industrial: 'I need to automate a conveyor system'")
        print("  - Non-industrial: 'I want to build a web application'")
        print("  - Vague: 'Help me with automation'")
        print("  - Device-specific: 'I have a temperature sensor that needs control'")
        
        while True:
            try:
                # Get user message
                user_message = self.get_user_input("Enter your message (or 'quit' to exit)")
                
                if user_message.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not user_message:
                    print("❌ Please enter a message.")
                    continue
                
                self.message_count += 1
                
                self.print_separator(f"📨 MESSAGE #{self.message_count}")
                
                # Create conversation request
                request = ConversationRequest(
                    conversation_id=self.conversation_id,
                    message=user_message
                )
                
                # If we have a conversation, show current state before processing
                if self.conversation_id and self.conversation_id in self.orchestrator.conversations:
                    conversation = self.orchestrator.conversations[self.conversation_id]
                    self.display_conversation_state(conversation)
                    self.display_prompt_details(conversation.current_stage, conversation, user_message)
                
                # Process the message
                print(f"\n⚙️ Processing message...")
                response = await self.orchestrator.process_message(request)
                
                # Store conversation ID for subsequent messages
                if not self.conversation_id:
                    self.conversation_id = response.conversation_id
                
                # Display the response
                self.display_api_response(response)
                
                # Get updated conversation state
                conversation = self.orchestrator.conversations[self.conversation_id]
                self.display_conversation_state(conversation)
                
                # Handle MCQ response if needed
                if response.is_mcq and response.mcq_question and response.mcq_options:
                    print(f"\n🎯 MCQ DETECTED - Testing MCQ answer context persistence...")
                    
                    # Get MCQ response from user
                    mcq_response_data = self.get_mcq_response(
                        response.mcq_question,
                        response.mcq_options,
                        response.is_multiselect
                    )
                    
                    # Get additional user message
                    additional_message = self.get_user_input("Any additional context (optional)")
                    
                    # Create follow-up request with MCQ response
                    followup_request = ConversationRequest(
                        conversation_id=self.conversation_id,
                        message=additional_message or "Thank you for the options.",
                        mcq_response=mcq_response_data
                    )
                    
                    self.message_count += 1
                    self.print_separator(f"📨 MCQ FOLLOW-UP #{self.message_count}")
                    
                    # Show the MCQ context that will be included
                    print(f"🔗 MCQ CONTEXT BEING ADDED:")
                    print(f"  Question: {mcq_response_data['question']}")
                    print(f"  Selected: {', '.join(mcq_response_data['selected_options'])}")
                    print(f"  Additional Message: {followup_request.message}")
                    
                    # Process follow-up
                    conversation_before_mcq = self.orchestrator.conversations[self.conversation_id]
                    self.display_prompt_details(conversation_before_mcq.current_stage, conversation_before_mcq, followup_request.message)
                    
                    followup_response = await self.orchestrator.process_message(followup_request)
                    
                    # Display follow-up response
                    self.display_api_response(followup_response)
                    
                    # Show how MCQ context was preserved
                    conversation_after_mcq = self.orchestrator.conversations[self.conversation_id]
                    print(f"\n🔍 MCQ CONTEXT VERIFICATION:")
                    if conversation_after_mcq.qa and conversation_after_mcq.qa.answers_received:
                        print("✅ MCQ answers found in conversation context:")
                        for answer in conversation_after_mcq.qa.answers_received[-2:]:
                            print(f"  - {answer}")
                    else:
                        print("❌ MCQ answers not found in conversation context!")
                
                print(f"\n🔄 Ready for next message...")
                
            except KeyboardInterrupt:
                print("\n\n👋 Conversation interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()
                print("\nContinuing...")


async def main():
    """Main entry point."""
    tester = ConversationTester()
    await tester.run_conversation_test()


if __name__ == "__main__":
    asyncio.run(main())