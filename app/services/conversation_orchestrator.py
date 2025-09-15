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
            response = await self._process_stage_message(conversation, request.message)
            
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
            current_stage=ConversationStage.REQUIREMENTS_GATHERING,
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
        if new_stage == ConversationStage.REQUIREMENTS_GATHERING and not conversation.requirements:
            conversation.requirements = RequirementsState(user_query="")
        elif new_stage == ConversationStage.QA_CLARIFICATION and not conversation.qa:
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
    
    async def _process_stage_message(self, conversation: ConversationState, message: str) -> ConversationResponse:
        """Process message according to current conversation stage."""
        
        stage = conversation.current_stage
        
        # Get appropriate prompt template
        template = PromptTemplateFactory.get_template(stage)
        
        # Build prompts
        system_prompt = template.build_system_prompt(conversation)
        user_prompt = template.build_user_prompt(message, conversation)
        
        # Get model configuration
        model_config = template.get_model_config()
        
        # Create request for OpenAI service
        class LLMRequest:
            def __init__(self, user_prompt: str, **config):
                self.user_prompt = user_prompt
                for key, value in config.items():
                    setattr(self, key, value)
        
        llm_request = LLMRequest(user_prompt, **model_config)
        
        # Call OpenAI with system message
        try:
            # For now, combine system and user prompts
            # TODO: Update OpenAI service to support system messages
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"
            llm_request.user_prompt = combined_prompt
            
            response_content, usage = await self.openai_service.chat_completion(llm_request)
            
        except Exception as e:
            logger.error("LLM call failed", error=str(e))
            response_content = f"I apologize, but I encountered an error processing your request: {str(e)}"
        
        # Update stage-specific state based on response
        await self._update_stage_state(conversation, message, response_content)
        
        # Determine next suggested stage
        next_stage = await self._suggest_next_stage(conversation)
        
        # Build response
        return ConversationResponse(
            conversation_id=conversation.conversation_id,
            stage=conversation.current_stage,
            response=response_content,
            next_stage=next_stage,
            stage_progress=self._get_stage_progress(conversation),
            suggested_actions=self._get_suggested_actions(conversation)
        )
    
    async def _update_stage_state(self, conversation: ConversationState, user_message: str, ai_response: str):
        """Update stage-specific state based on the interaction."""
        
        stage = conversation.current_stage
        
        if stage == ConversationStage.REQUIREMENTS_GATHERING:
            if not conversation.requirements:
                conversation.requirements = RequirementsState(user_query=user_message)
            else:
                conversation.requirements.user_query = user_message
        
        elif stage == ConversationStage.QA_CLARIFICATION:
            if not conversation.qa:
                conversation.qa = QAState()
            
            # Extract questions from AI response (simplified)
            if "?" in ai_response:
                questions = [q.strip() for q in ai_response.split("?") if q.strip()]
                conversation.qa.questions_asked.extend(questions)
            
            # Record user answer
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
        if current_stage == ConversationStage.REQUIREMENTS_GATHERING:
            # Check if we have enough requirements
            if (conversation.requirements and 
                len(conversation.requirements.identified_requirements) > 2):
                return ConversationStage.CODE_GENERATION
            else:
                return ConversationStage.QA_CLARIFICATION
        
        elif current_stage == ConversationStage.QA_CLARIFICATION:
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
        
        if stage == ConversationStage.REQUIREMENTS_GATHERING:
            return {
                "requirements_identified": len(conversation.requirements.identified_requirements) if conversation.requirements else 0,
                "confidence": conversation.requirements.confidence_level if conversation.requirements else 0.0
            }
        
        elif stage == ConversationStage.QA_CLARIFICATION:
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
        
        if stage == ConversationStage.REQUIREMENTS_GATHERING:
            return [
                "Provide more details about your control requirements",
                "Upload relevant documentation or datasheets",
                "Specify safety requirements and constraints"
            ]
        
        elif stage == ConversationStage.QA_CLARIFICATION:
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
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationState]:
        """Get conversation by ID."""
        return self.conversations.get(conversation_id)
    
    def get_conversation_history(self, conversation_id: str) -> List[ConversationMessage]:
        """Get conversation message history."""
        conversation = self.conversations.get(conversation_id)
        return conversation.messages if conversation else []