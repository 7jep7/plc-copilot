"""Conversation orchestrator for multi-stage PLC-Copilot interactions."""

import uuid
import structlog
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.schemas.conversation import (
    ConversationStage,
    ConversationState,
    ConversationMessage,
    ConversationRequest,
    ConversationResponse,
    MessageRole,
    RequirementsState,
    QAState,
    GenerationState,
    RefinementState,
    StageDetectionRequest
)
from app.services.stage_detection_service import StageDetectionService, StageTransitionRules
from app.services.prompt_templates import PromptTemplateFactory
from app.services.openai_service import OpenAIService

logger = structlog.get_logger()


class ConversationOrchestrator:
    """Orchestrates multi-stage PLC-Copilot conversations."""
    
    def __init__(self):
        self.stage_detector = StageDetectionService()
        self.openai_service = OpenAIService()
        self.conversations: Dict[str, ConversationState] = {}  # In-memory storage for now
    
    async def process_message(self, request: ConversationRequest) -> ConversationResponse:
        """
        Process a user message and return appropriate response based on conversation stage.
        
        Main entry point for conversation handling.
        """
        try:
            # Get or create conversation
            conversation = await self._get_or_create_conversation(request.conversation_id)
            
            # Add user message to history
            user_message = ConversationMessage(
                role=MessageRole.USER,
                content=request.message,
                attachments=request.attachments or []
            )
            
            # If this is an MCQ response, format the message to include selected options
            if request.mcq_response:
                mcq_data = request.mcq_response
                question = mcq_data.get("question", "")
                selected_options = mcq_data.get("selected_options", [])
                
                if selected_options:
                    if len(selected_options) == 1:
                        formatted_response = f"Selected: {selected_options[0]}"
                    else:
                        formatted_response = f"Selected: {', '.join(selected_options)}"
                    
                    # Include both the question context and the selection
                    if question:
                        user_message.content = f"Question: {question}\n{formatted_response}\n\nUser message: {request.message}"
                    else:
                        user_message.content = f"{formatted_response}\n\nUser message: {request.message}"
            
            conversation.messages.append(user_message)
            
            # Detect current stage (if not forced)
            if request.force_stage:
                target_stage = request.force_stage
                logger.info("Stage forced by user", stage=target_stage)
            else:
                target_stage = await self._detect_and_transition_stage(conversation)
            
            # Update conversation stage if needed
            if target_stage != conversation.current_stage:
                await self._transition_to_stage(conversation, target_stage)
            
            # Process message in current stage
            response = await self._process_stage_message(conversation, request)
            
            # Add assistant response to history
            assistant_message = ConversationMessage(
                role=MessageRole.ASSISTANT,
                content=response.response
            )
            conversation.messages.append(assistant_message)
            
            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()
            
            # Store updated conversation
            self.conversations[conversation.conversation_id] = conversation
            
            logger.info(
                "Message processed successfully",
                conversation_id=conversation.conversation_id,
                stage=conversation.current_stage,
                response_length=len(response.response)
            )
            
            return response
            
        except Exception as e:
            logger.error("Failed to process message", error=str(e))
            raise
    
    async def _get_or_create_conversation(self, conversation_id: Optional[str]) -> ConversationState:
        """Get existing conversation or create a new one."""
        
        if conversation_id and conversation_id in self.conversations:
            return self.conversations[conversation_id]
        
        # Create new conversation
        new_id = conversation_id or str(uuid.uuid4())
        conversation = ConversationState(
            conversation_id=new_id,
            current_stage=ConversationStage.PROJECT_KICKOFF,
            requirements=RequirementsState(user_query=""),
            qa=QAState(),
            generation=GenerationState(),
            refinement=RefinementState()
        )
        
        self.conversations[new_id] = conversation
        
        logger.info("Created new conversation", conversation_id=new_id)
        return conversation
    
    async def _detect_and_transition_stage(self, conversation: ConversationState) -> ConversationStage:
        """Detect appropriate stage based on conversation context."""
        
        # Get recent messages for context
        recent_messages = conversation.messages[-5:]  # Last 5 messages
        
        detection_request = StageDetectionRequest(
            conversation_id=conversation.conversation_id,
            recent_messages=recent_messages,
            current_stage=conversation.current_stage
        )
        
        detection_result = await self.stage_detector.detect_stage(detection_request)
        
        # Check if transition is valid and ready
        if (detection_result.transition_ready and 
            detection_result.suggested_stage != conversation.current_stage and
            StageTransitionRules.is_valid_transition(
                conversation.current_stage, 
                detection_result.suggested_stage
            )):
            
            logger.info(
                "Stage transition detected",
                from_stage=conversation.current_stage,
                to_stage=detection_result.suggested_stage,
                confidence=detection_result.confidence,
                reasoning=detection_result.reasoning
            )
            
            return detection_result.suggested_stage
        
        return conversation.current_stage
    
    async def _transition_to_stage(self, conversation: ConversationState, new_stage: ConversationStage):
        """Handle transition to a new conversation stage."""
        
        old_stage = conversation.current_stage
        conversation.current_stage = new_stage
        
        # Initialize stage-specific state if needed
        if new_stage == ConversationStage.PROJECT_KICKOFF and not conversation.requirements:
            conversation.requirements = RequirementsState(user_query="")
        elif new_stage == ConversationStage.GATHER_REQUIREMENTS and not conversation.qa:
            conversation.qa = QAState()
        elif new_stage == ConversationStage.CODE_GENERATION and not conversation.generation:
            conversation.generation = GenerationState()
        elif new_stage == ConversationStage.REFINEMENT_TESTING and not conversation.refinement:
            conversation.refinement = RefinementState()
        
        logger.info(
            "Stage transition completed",
            conversation_id=conversation.conversation_id,
            from_stage=old_stage,
            to_stage=new_stage
        )
    
    async def _process_stage_message(self, conversation: ConversationState, request: ConversationRequest) -> ConversationResponse:
        """Process message according to current conversation stage."""
        
        stage = conversation.current_stage
        
        # Get appropriate prompt template
        template = PromptTemplateFactory.get_template(stage)
        
        # Build prompts
        system_prompt = template.build_system_prompt(conversation)
        user_prompt = template.build_user_prompt(request.message, conversation)
        
        # Get model configuration
        model_config = template.get_model_config()
        
        # Create request for OpenAI service
        class LLMRequest:
            def __init__(self, user_prompt: str, **config):
                self.user_prompt = user_prompt
                for key, value in config.items():
                    setattr(self, key, value)
        
        llm_request = LLMRequest(user_prompt, **model_config)
        
        # Prepare structured messages with full conversation history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation history for context (last 10 messages)
        recent_messages = conversation.messages[-10:]  # Limit to avoid token overflow
        
        # TODO: Build intelligent context summary if conversation is getting long
        # This will be implemented later using LLMs for better summarization
        # if len(conversation.messages) > 20:
        #     context_summary = self._build_context_summary(conversation)
        #     if context_summary:
        #         messages.append({"role": "system", "content": f"CONTEXT SUMMARY:\n{context_summary}"})
        
        for msg in recent_messages[:-1]:  # Exclude the current message we just added
            messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        # Add current user message
        messages.append({"role": "user", "content": user_prompt})
        
        # Call OpenAI with structured messages
        try:
            # Create a request object that includes conversation context
            llm_request.conversation_id = conversation.conversation_id  # Add conversation ID for fallback tracking
            
            response_content, usage = await self.openai_service.chat_completion(
                llm_request, 
                messages=messages
            )
            
        except Exception as e:
            logger.error("LLM call failed", error=str(e))
            response_content = f"I apologize, but I encountered an error processing your request: {str(e)}"
        
        # Update stage-specific state based on response
        await self._update_stage_state(conversation, request, response_content)
        
        # Parse MCQ information if present
        mcq_data = self._parse_mcq_from_response(response_content)
        
        # Parse structured code and chat message if present
        parsed_content = self._parse_structured_response(response_content)
        
        # Parse requirements gathering progress
        progress_data = self._parse_requirements_progress(response_content, conversation.current_stage)
        
        # For MCQ responses, use the parsed chat message (which should exclude options)
        # If no chat_message tags found, fall back to the question text only
        final_chat_message = parsed_content["chat_message"]
        if mcq_data["is_mcq"] and not parsed_content.get("chat_message_found", False):
            # If no explicit chat_message was provided, use just the question
            final_chat_message = mcq_data["question"]
        
        # Determine next suggested stage
        next_stage = await self._suggest_next_stage(conversation)
        
        # Build response
        response = ConversationResponse(
            conversation_id=conversation.conversation_id,
            stage=conversation.current_stage,
            response=final_chat_message,  # Use simplified chat message for MCQ
            next_stage=next_stage,
            stage_progress=self._get_stage_progress(conversation),
            suggested_actions=self._get_suggested_actions(conversation),
            is_mcq=mcq_data["is_mcq"],
            mcq_question=mcq_data["question"],
            mcq_options=mcq_data["options"],
            is_multiselect=mcq_data["is_multiselect"],
            generated_code=parsed_content["code"],
            gathering_requirements_estimated_progress=progress_data["progress"]
        )
        
        return response
    
    async def _update_stage_state(self, conversation: ConversationState, request: ConversationRequest, ai_response: str):
        """Update stage-specific state based on the interaction."""
        
        stage = conversation.current_stage
        user_message = request.message
        
        if stage == ConversationStage.PROJECT_KICKOFF:
            if not conversation.requirements:
                conversation.requirements = RequirementsState(user_query=user_message)
            else:
                conversation.requirements.user_query = user_message
        
        elif stage == ConversationStage.GATHER_REQUIREMENTS:
            if not conversation.qa:
                conversation.qa = QAState()
            
            # Extract questions from AI response (simplified)
            if "?" in ai_response:
                questions = [q.strip() for q in ai_response.split("?") if q.strip()]
                conversation.qa.questions_asked.extend(questions)
            
            # Record user answer with MCQ context if available
            if request.mcq_response:
                mcq_data = request.mcq_response
                question = mcq_data.get("question", "")
                selected_options = mcq_data.get("selected_options", [])
                
                # Format MCQ answer for better context
                if selected_options:
                    if len(selected_options) == 1:
                        formatted_answer = f"MCQ Answer: {selected_options[0]}"
                    else:
                        formatted_answer = f"MCQ Answers: {', '.join(selected_options)}"
                    
                    if question:
                        formatted_answer = f"Q: {question} | A: {', '.join(selected_options)}"
                    
                    conversation.qa.answers_received.append(formatted_answer)
                    
                    # Also store the original message if it adds context
                    if user_message.strip() and user_message.strip() != formatted_answer:
                        conversation.qa.answers_received.append(f"Additional context: {user_message}")
                else:
                    conversation.qa.answers_received.append(user_message)
            else:
                # Regular non-MCQ answer
                conversation.qa.answers_received.append(user_message)
        
        elif stage == ConversationStage.CODE_GENERATION:
            if not conversation.generation:
                conversation.generation = GenerationState()
            
            # Extract generated code (simplified)
            if "```st" in ai_response or "```" in ai_response:
                conversation.generation.generated_code = ai_response
                conversation.generation.explanation = ai_response
        
        elif stage == ConversationStage.REFINEMENT_TESTING:
            if not conversation.refinement:
                conversation.refinement = RefinementState()
            
            conversation.refinement.refinement_requests.append(user_message)
            conversation.refinement.user_feedback.append(user_message)
    
    async def _suggest_next_stage(self, conversation: ConversationState) -> Optional[ConversationStage]:
        """Suggest the next logical stage based on current state."""
        
        current_stage = conversation.current_stage
        valid_transitions = StageTransitionRules.get_valid_transitions(current_stage)
        
        # Simple heuristics for stage progression
        if current_stage == ConversationStage.PROJECT_KICKOFF:
            # Check if we have enough requirements
            if (conversation.requirements and 
                len(conversation.requirements.identified_requirements) > 2):
                return ConversationStage.CODE_GENERATION
            else:
                return ConversationStage.GATHER_REQUIREMENTS
        
        elif current_stage == ConversationStage.GATHER_REQUIREMENTS:
            # Check if Q&A seems complete
            if (conversation.qa and 
                len(conversation.qa.answers_received) >= 3):
                return ConversationStage.CODE_GENERATION
        
        elif current_stage == ConversationStage.CODE_GENERATION:
            return ConversationStage.REFINEMENT_TESTING
        
        elif current_stage == ConversationStage.REFINEMENT_TESTING:
            # Could suggest completion or more refinement
            return None
        
        return None
    
    def _get_stage_progress(self, conversation: ConversationState) -> Dict[str, Any]:
        """Get progress information for the current stage."""
        
        stage = conversation.current_stage
        
        if stage == ConversationStage.PROJECT_KICKOFF:
            return {
                "requirements_identified": len(conversation.requirements.identified_requirements) if conversation.requirements else 0,
                "confidence": conversation.requirements.confidence_level if conversation.requirements else 0.0
            }
        
        elif stage == ConversationStage.GATHER_REQUIREMENTS:
            return {
                "questions_asked": len(conversation.qa.questions_asked) if conversation.qa else 0,
                "answers_received": len(conversation.qa.answers_received) if conversation.qa else 0
            }
        
        elif stage == ConversationStage.CODE_GENERATION:
            return {
                "code_generated": bool(conversation.generation.generated_code) if conversation.generation else False
            }
        
        elif stage == ConversationStage.REFINEMENT_TESTING:
            return {
                "refinement_cycles": len(conversation.refinement.refinement_requests) if conversation.refinement else 0
            }
        
        return {}
    
    def _get_suggested_actions(self, conversation: ConversationState) -> List[str]:
        """Get suggested actions for the user based on current stage."""
        
        stage = conversation.current_stage
        
        if stage == ConversationStage.PROJECT_KICKOFF:
            return [
                "Provide more details about your control requirements",
                "Upload relevant documentation or datasheets",
                "Specify safety requirements and constraints"
            ]
        
        elif stage == ConversationStage.GATHER_REQUIREMENTS:
            return [
                "Answer the technical questions provided",
                "Provide specific values and ranges",
                "Clarify any ambiguous requirements"
            ]
        
        elif stage == ConversationStage.CODE_GENERATION:
            return [
                "Review the generated code",
                "Test the code logic",
                "Proceed to refinement if changes needed"
            ]
        
        elif stage == ConversationStage.REFINEMENT_TESTING:
            return [
                "Request specific code modifications",
                "Report testing results",
                "Ask for additional features or optimizations"
            ]
        
        return []
    
    def _parse_mcq_from_response(self, response: str) -> Dict[str, Any]:
        """
        Parse MCQ information from AI response.
        
        Returns:
            dict: {
                "is_mcq": bool,
                "question": str or None,
                "options": List[str],
                "is_multiselect": bool
            }
        """
        import re
        
        # Initialize default response
        mcq_data = {
            "is_mcq": False,
            "question": None,
            "options": [],
            "is_multiselect": False
        }
        
        # Look for MCQ markers (both old and new formats)
        mcq_pattern = r'\*\*MCQ_START\*\*(.*?)\*\*MCQ_END\*\*'
        mcq_match = re.search(mcq_pattern, response, re.DOTALL)
        
        if mcq_match:
            mcq_content = mcq_match.group(1).strip()
            
            # Extract question
            question_pattern = r'\*\*Question\*\*:\s*(.*?)(?=\*\*Options\*\*:)'
            question_match = re.search(question_pattern, mcq_content, re.DOTALL)
            
            if question_match:
                mcq_data["question"] = question_match.group(1).strip()
            
            # Extract options
            options_pattern = r'\*\*Options\*\*:\s*(.*?)(?=\*\*|$)'
            options_match = re.search(options_pattern, mcq_content, re.DOTALL)
            
            if options_match:
                options_text = options_match.group(1).strip()
                # Parse individual options (A), B), C), etc.)
                option_lines = re.findall(r'^[A-Z]\)\s*(.+)$', options_text, re.MULTILINE)
                
                if option_lines:
                    mcq_data["is_mcq"] = True
                    mcq_data["options"] = [option.strip() for option in option_lines]
                    
                    # Check for multiselect indicators
                    multiselect_indicators = [
                        "select all that apply",
                        "multiple answers",
                        "choose multiple",
                        "more than one",
                        "all applicable"
                    ]
                    
                    full_content = (mcq_content + " " + mcq_data["question"] or "").lower()
                    mcq_data["is_multiselect"] = any(indicator in full_content for indicator in multiselect_indicators)
        
        # Also check for informal MCQ format (like the one in the test output)
        if not mcq_data["is_mcq"]:
            # Look for Question: ... Options: pattern
            informal_question_pattern = r'\*\*Question\*\*:\s*(.*?)(?=\*\*Options\*\*:)'
            informal_question_match = re.search(informal_question_pattern, response, re.DOTALL)
            
            if informal_question_match:
                mcq_data["question"] = informal_question_match.group(1).strip()
                
                # Look for options after the question
                informal_options_pattern = r'\*\*Options\*\*:\s*(.*?)(?=\*\*|$)'
                informal_options_match = re.search(informal_options_pattern, response, re.DOTALL)
                
                if informal_options_match:
                    options_text = informal_options_match.group(1).strip()
                    option_lines = re.findall(r'^[A-Z]\)\s*(.+)$', options_text, re.MULTILINE)
                    
                    if option_lines:
                        mcq_data["is_mcq"] = True
                        mcq_data["options"] = [option.strip() for option in option_lines]
        
        return mcq_data
    
    def _parse_structured_response(self, response: str) -> Dict[str, Any]:
        """
        Parse structured response with <code> and <chat_message> tags.
        
        Returns:
            dict: {
                "code": str or None,
                "chat_message": str (cleaned response),
                "chat_message_found": bool (whether explicit chat_message tags were found)
            }
        """
        import re
        
        # Initialize default response
        parsed_data = {
            "code": None,
            "chat_message": response,  # Default to full response
            "chat_message_found": False
        }
        
        # Extract code block
        code_pattern = r'<code>(.*?)</code>'
        code_match = re.search(code_pattern, response, re.DOTALL)
        
        if code_match:
            parsed_data["code"] = code_match.group(1).strip()
        
        # Extract chat message
        chat_pattern = r'<chat_message>(.*?)</chat_message>'
        chat_match = re.search(chat_pattern, response, re.DOTALL)
        
        if chat_match:
            parsed_data["chat_message"] = chat_match.group(1).strip()
            parsed_data["chat_message_found"] = True
        elif code_match:
            # If we have code but no chat_message tag, remove the code tags from response
            cleaned_response = re.sub(code_pattern, '', response, flags=re.DOTALL)
            parsed_data["chat_message"] = cleaned_response.strip()
        
        # Always clean any remaining tags from the chat message
        if parsed_data["chat_message"]:
            # Remove any remaining <code> and <chat_message> tags
            cleaned = re.sub(r'</?code>', '', parsed_data["chat_message"])
            cleaned = re.sub(r'</?chat_message>', '', cleaned)
            
            # Remove MCQ content from chat message since it's shown separately
            mcq_pattern = r'\*\*MCQ_START\*\*(.*?)\*\*MCQ_END\*\*'
            cleaned = re.sub(mcq_pattern, '', cleaned, flags=re.DOTALL)
            
            # Clean up extra whitespace
            cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
            parsed_data["chat_message"] = cleaned.strip()
        
        return parsed_data
    
    # TODO: Implement LLM-based context summarization in the future
    # def _build_context_summary(self, conversation: ConversationState) -> str:
    #     """Build intelligent context summary preserving key Structured Text information."""
    #     summary_parts = []
    #     
    #     # Project Overview
    #     if conversation.requirements and conversation.requirements.user_query:
    #         summary_parts.append(f"PROJECT: {conversation.requirements.user_query}")
    #     
    #     # Key Requirements (from Q&A)
    #     if conversation.qa and conversation.qa.answers_received:
    #         key_answers = []
    #         for answer in conversation.qa.answers_received[-10:]:  # Last 10 answers
    #             if any(keyword in answer.lower() for keyword in [
    #                 'safety', 'voltage', 'current', 'speed', 'temperature', 'pressure',
    #                 'protocol', 'plc', 'input', 'output', 'sensor', 'actuator', 'motor'
    #             ]):
    #                 key_answers.append(answer)
    #         
    #         if key_answers:
    #             summary_parts.append(f"KEY REQUIREMENTS:\n- " + "\n- ".join(key_answers[:5]))
    #     
    #     # Document Context
    #     if conversation.extracted_documents:
    #         doc_summaries = []
    #         for doc_data in conversation.extracted_documents:
    #             filename = doc_data.get('filename', 'Unknown')
    #             doc_type = doc_data.get('document_type', 'UNKNOWN')
    #             device_info = doc_data.get('device_info', {})
    #             
    #             if device_info.get('manufacturer') or device_info.get('model'):
    #                 device_str = f"{device_info.get('manufacturer', '')} {device_info.get('model', '')}".strip()
    #                 doc_summaries.append(f"{filename} ({doc_type}): {device_str}")
    #             else:
    #                 doc_summaries.append(f"{filename} ({doc_type})")
    #         
    #         if doc_summaries:
    #             summary_parts.append(f"DOCUMENTS:\n- " + "\n- ".join(doc_summaries))
    #     
    #     # Generated Code Status
    #     if conversation.generation and conversation.generation.generated_code:
    #         summary_parts.append("STATUS: Structured Text code has been generated")
    #     
    #     # Current Stage Progress
    #     stage_info = f"STAGE: {conversation.current_stage.value}"
    #     summary_parts.append(stage_info)
    #     
    #     return "\n\n".join(summary_parts) if summary_parts else ""

    def _parse_requirements_progress(self, response: str, current_stage) -> Dict[str, Any]:
        """
        Parse requirements gathering progress from AI response.
        
        Returns:
            dict: {
                "progress": float (0.0 to 1.0)
            }
        """
        import re
        from app.schemas.conversation import ConversationStage
        
        # Default progress values based on stage
        if current_stage == ConversationStage.PROJECT_KICKOFF:
            default_progress = 0.0
        elif current_stage == ConversationStage.GATHER_REQUIREMENTS:
            default_progress = 0.5  # Default to halfway if no specific progress found
        else:  # CODE_GENERATION, REFINEMENT_TESTING, COMPLETED
            default_progress = 1.0
        
        progress_data = {"progress": default_progress}
        
        # Only try to parse progress for GATHER_REQUIREMENTS stage
        if current_stage == ConversationStage.GATHER_REQUIREMENTS:
            # Look for progress patterns like "1/5", "2/10", etc.
            progress_pattern = r'\*\*PROGRESS\*\*:\s*(\d+)/(\d+)'
            progress_match = re.search(progress_pattern, response)
            
            if progress_match:
                current = int(progress_match.group(1))
                total = int(progress_match.group(2))
                if total > 0:
                    progress_data["progress"] = min(current / total, 1.0)  # Cap at 1.0
        
        return progress_data
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationState]:
        """Get conversation by ID."""
        return self.conversations.get(conversation_id)
    
    def get_conversation_history(self, conversation_id: str) -> List[ConversationMessage]:
        """Get conversation message history."""
        conversation = self.conversations.get(conversation_id)
        return conversation.messages if conversation else []