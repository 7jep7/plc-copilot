#!/usr/bin/env python3
"""
Lightweight test script demonstrating PLC-Copilot API endpoint functionality across all stages.

This script demonstrates:
1. Starting a conversation (project_kickoff)
2. Gathering requirements with MCQ functionality 
3. Code generation with structured parsing
4. Refinement and testing with structured code updates
5. Parsing and displaying all structured responses

Usage:
    python scripts/test_enhanced_prompts.py
"""

import asyncio
import json
import sys
from pathlib import Path

# ANSI color codes for better readability
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    # Custom colors for different types of content
    USER_MSG = '\033[96m'      # Cyan for user messages
    SYSTEM_PROMPT = '\033[95m'  # Magenta for system prompts
    LLM_RESPONSE = '\033[92m'   # Green for LLM responses
    API_RESPONSE = '\033[94m'   # Blue for API responses
    HISTORY = '\033[93m'        # Yellow for conversation history

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.conversation_orchestrator import ConversationOrchestrator
from app.services.prompt_templates import PromptTemplateFactory
from app.schemas.conversation import ConversationRequest, ConversationStage


class PromptTestDemonstrator:
    """Demonstrates enhanced prompt functionality across all conversation stages."""
    
    def __init__(self):
        self.orchestrator = ConversationOrchestrator()
        self.conversation_id = None
        
    def _display_detailed_response(self, stage_name: str, user_message: str, response, conversation=None):
        """Display detailed information about the LLM interaction."""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{stage_name}{Colors.ENDC}")
        print(Colors.HEADER + "=" * len(stage_name) + Colors.ENDC)
        
        # Show user message
        print(f"{Colors.USER_MSG}{Colors.BOLD}📝 User Message:{Colors.ENDC}")
        print(f"{Colors.USER_MSG}   {user_message}{Colors.ENDC}")
        print()
        
        # Show conversation history if available
        if conversation and len(conversation.messages) > 1:
            print(f"{Colors.HISTORY}{Colors.BOLD}📚 Conversation History Sent to LLM:{Colors.ENDC}")
            # Get last 10 messages (excluding the current one)
            recent_messages = conversation.messages[-10:]
            for i, msg in enumerate(recent_messages[:-1]):  # Exclude current message
                role_icon = "👤" if msg.role.value == "user" else "🤖"
                print(f"{Colors.HISTORY}   {i+1}. {role_icon} {msg.role.value}: {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}{Colors.ENDC}")
            print()
        
        # Get conversation to show system prompt
        if conversation:
            try:
                template = PromptTemplateFactory.get_template(conversation.current_stage)
                system_prompt = template.build_system_prompt(conversation)
                user_prompt = template.build_user_prompt(user_message, conversation)
                
                print(f"{Colors.SYSTEM_PROMPT}{Colors.BOLD}🔧 System Prompt Sent to LLM:{Colors.ENDC}")
                # Show first 300 chars of system prompt
                truncated_prompt = system_prompt[:300] + "..." if len(system_prompt) > 300 else system_prompt
                print(f"{Colors.SYSTEM_PROMPT}   {truncated_prompt}{Colors.ENDC}")
                print()
                
                print(f"{Colors.SYSTEM_PROMPT}{Colors.BOLD}👤 User Prompt Sent to LLM:{Colors.ENDC}")
                print(f"{Colors.SYSTEM_PROMPT}   {user_prompt}{Colors.ENDC}")
                print()
            except Exception as e:
                print(f"   [Could not extract prompts: {e}]")
                print()
        
        # Show parsed API response
        print(f"{Colors.API_RESPONSE}{Colors.BOLD}🤖 Parsed API Response (Chat Message):{Colors.ENDC}")
        print(f"{Colors.API_RESPONSE}   {response.response}{Colors.ENDC}")
        print()
        
        if response.generated_code:
            print(f"{Colors.LLM_RESPONSE}{Colors.BOLD}💻 Generated Code:{Colors.ENDC}")
            # Show first 300 chars of code
            truncated_code = response.generated_code[:300] + "..." if len(response.generated_code) > 300 else response.generated_code
            print(f"{Colors.LLM_RESPONSE}   {truncated_code}{Colors.ENDC}")
            print()
        
        print(f"{Colors.BOLD}📊 API Response Fields:{Colors.ENDC}")
        print(f"   ✓ Stage: {Colors.CYAN}{response.stage}{Colors.ENDC}")
        print(f"   ✓ Chat message for frontend: {Colors.GREEN}{response.response[:100]}{'...' if len(response.response) > 100 else ''}{Colors.ENDC}")
        print(f"   ✓ Requirements gathering progress: {Colors.YELLOW}{response.gathering_requirements_estimated_progress:.1%}{Colors.ENDC}")
        print(f"   ✓ MCQ detected: {Colors.GREEN if response.is_mcq else Colors.RED}{response.is_mcq}{Colors.ENDC}")
        if response.is_mcq:
            print(f"   ✓ MCQ Question: {Colors.YELLOW}{response.mcq_question}{Colors.ENDC}")
            print(f"   ✓ MCQ Options: {Colors.YELLOW}{response.mcq_options}{Colors.ENDC}")
            print(f"   ✓ Is Multiselect: {Colors.GREEN if response.is_multiselect else Colors.RED}{response.is_multiselect}{Colors.ENDC}")
        print(f"   ✓ Generated code present: {Colors.GREEN if response.generated_code else Colors.RED}{response.generated_code is not None}{Colors.ENDC}")
        if response.generated_code:
            print(f"   ✓ Generated code length: {Colors.CYAN}{len(response.generated_code)} chars{Colors.ENDC}")
        print(f"   ✓ Next stage: {Colors.CYAN}{response.next_stage}{Colors.ENDC}")
        print(f"   ✓ Conversation ID: {Colors.CYAN}{response.conversation_id}{Colors.ENDC}")
        
        # Show the complete frontend payload
        print(f"\n{Colors.BOLD}🎯 Complete Frontend Payload:{Colors.ENDC}")
        frontend_payload = {
            "conversation_id": response.conversation_id,
            "stage": response.stage.value,
            "chat_message": response.response,
            "next_stage": response.next_stage.value if response.next_stage else None,
            "gathering_requirements_estimated_progress": response.gathering_requirements_estimated_progress,
            "is_mcq": response.is_mcq,
            "mcq_question": response.mcq_question,
            "mcq_options": response.mcq_options,
            "is_multiselect": response.is_multiselect,
            "generated_code": response.generated_code,
            "stage_progress": response.stage_progress,
            "suggested_actions": response.suggested_actions
        }
        
        # Display as pretty JSON
        import json
        payload_json = json.dumps(frontend_payload, indent=2, default=str)
        for line in payload_json.split('\n'):
            print(f"{Colors.CYAN}   {line}{Colors.ENDC}")
        print()
    
    async def run_full_demo(self):
        """Run a complete demonstration of all conversation stages."""
        print(f"{Colors.BOLD}{Colors.HEADER}🤖 PLC-Copilot Enhanced Prompt System Demo{Colors.ENDC}")
        print(Colors.HEADER + "=" * 50 + Colors.ENDC)
        
        # Test each stage in sequence
        await self._test_project_kickoff()
        await self._test_gather_requirements()
        await self._test_code_generation()
        await self._test_refinement_testing()
        
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ All stages tested successfully!{Colors.ENDC}")
        print(f"{Colors.GREEN}🎯 Enhanced prompt system working correctly with structured parsing{Colors.ENDC}")
    
    async def _test_project_kickoff(self):
        """Test project kickoff stage."""
        message = "I need to create a simple conveyor belt control system for a warehouse automation project."
        
        request = ConversationRequest(
            message=message,
            force_stage=ConversationStage.PROJECT_KICKOFF
        )
        
        response = await self.orchestrator.process_message(request)
        self.conversation_id = response.conversation_id
        
        # Get conversation for detailed display
        conversation = self.orchestrator.get_conversation(self.conversation_id)
        
        self._display_detailed_response("📋 PROJECT_KICKOFF Stage", message, response, conversation)
    
    async def _test_gather_requirements(self):
        """Test requirements gathering stage with MCQ."""
        message = "The conveyor should handle boxes up to 50kg and run at variable speeds."
        
        request = ConversationRequest(
            conversation_id=self.conversation_id,
            message=message,
            force_stage=ConversationStage.GATHER_REQUIREMENTS
        )
        
        response = await self.orchestrator.process_message(request)
        conversation = self.orchestrator.get_conversation(self.conversation_id)
        
        self._display_detailed_response("❓ GATHER_REQUIREMENTS Stage", message, response, conversation)
        
        if response.is_mcq:
            # Simulate MCQ answer
            mcq_message = "A) ISO 13849-1 (Safety-related Parts of Control Systems)"
            mcq_answer_request = ConversationRequest(
                conversation_id=self.conversation_id,
                message=mcq_message,
                force_stage=ConversationStage.GATHER_REQUIREMENTS
            )
            
            mcq_response = await self.orchestrator.process_message(mcq_answer_request)
            conversation = self.orchestrator.get_conversation(self.conversation_id)
            
            self._display_detailed_response("❓ MCQ Answer Processing", mcq_message, mcq_response, conversation)
    
    async def _test_code_generation(self):
        """Test code generation stage with structured parsing."""
        message = "Generate the PLC code for the conveyor control system based on our requirements."
        
        request = ConversationRequest(
            conversation_id=self.conversation_id,
            message=message,
            force_stage=ConversationStage.CODE_GENERATION
        )
        
        response = await self.orchestrator.process_message(request)
        conversation = self.orchestrator.get_conversation(self.conversation_id)
        
        self._display_detailed_response("🔧 CODE_GENERATION Stage", message, response, conversation)
    
    async def _test_refinement_testing(self):
        """Test refinement and testing stage with structured parsing."""
        message = "Add better error handling and status indicators to the conveyor code."
        
        request = ConversationRequest(
            conversation_id=self.conversation_id,
            message=message,
            force_stage=ConversationStage.REFINEMENT_TESTING
        )
        
        response = await self.orchestrator.process_message(request)
        conversation = self.orchestrator.get_conversation(self.conversation_id)
        
        self._display_detailed_response("🔍 REFINEMENT_TESTING Stage", message, response, conversation)
    
    def _display_conversation_summary(self):
        """Display a summary of the conversation."""
        if not self.conversation_id:
            return
            
        conversation = self.orchestrator.get_conversation(self.conversation_id)
        if conversation:
            print(f"\n📊 Conversation Summary")
            print(f"   ID: {conversation.conversation_id}")
            print(f"   Stage: {conversation.current_stage}")
            print(f"   Messages: {len(conversation.messages)}")
            print(f"   Created: {conversation.created_at}")


async def main():
    """Main entry point for the demonstration."""
    demonstrator = PromptTestDemonstrator()
    
    try:
        await demonstrator.run_full_demo()
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)