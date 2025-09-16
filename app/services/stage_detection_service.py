"""Stage detection service for multi-stage PLC-Copilot conversations."""

import structlog
from typing import List, Dict, Any
from app.schemas.conversation import (
    ConversationStage,
    ConversationMessage,
    StageDetectionRequest,
    StageDetectionResponse,
    MessageRole
)
from app.services.openai_service import OpenAIService
from app.core.models import ModelConfig

logger = structlog.get_logger()


class StageDetectionService:
    """Service for detecting conversation stage transitions using lightweight LLM."""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        
    async def detect_stage(self, request: StageDetectionRequest) -> StageDetectionResponse:
        """
        Analyze conversation context and determine appropriate stage.
        
        Uses a fast, lightweight model for low-latency stage classification.
        """
        try:
            # Build context for stage detection
            context = self._build_detection_context(request)
            
            # Create a lightweight request for stage detection
            class DetectionRequest:
                user_prompt = context
                model = ModelConfig.CONVERSATION_MODEL
                temperature = ModelConfig.STAGE_DETECTION_CONFIG["temperature"]
                max_tokens = ModelConfig.STAGE_DETECTION_CONFIG["max_tokens"]
                max_completion_tokens = ModelConfig.STAGE_DETECTION_CONFIG["max_completion_tokens"]
            
            # Get stage classification from LLM
            response_content, usage = await self.openai_service.chat_completion(DetectionRequest())
            
            # Parse the response to extract stage decision
            stage_response = self._parse_stage_response(response_content, request.current_stage)
            
            logger.info(
                "Stage detection completed",
                conversation_id=request.conversation_id,
                current_stage=request.current_stage,
                suggested_stage=stage_response.suggested_stage,
                confidence=stage_response.confidence
            )
            
            return stage_response
            
        except Exception as e:
            logger.error("Stage detection failed", error=str(e))
            # Fallback: suggest staying in current stage
            return StageDetectionResponse(
                suggested_stage=request.current_stage,
                confidence=0.5,
                reasoning=f"Stage detection failed: {str(e)}. Staying in current stage.",
                transition_ready=False,
                required_actions=["Resolve stage detection issue"]
            )
    
    def _build_detection_context(self, request: StageDetectionRequest) -> str:
        """Build context for stage detection analysis."""
        
        # Convert recent messages to text
        message_history = []
        for msg in request.recent_messages[-10:]:  # Last 10 messages for context
            role_prefix = f"{msg.role.value.upper()}:"
            message_history.append(f"{role_prefix} {msg.content}")
        
        history_text = "\n".join(message_history)
        
        context = f"""Analyze this PLC-Copilot conversation and determine the appropriate stage.

CURRENT STAGE: {request.current_stage}

CONVERSATION STAGES:
1. project_kickoff - Initial user query, identifying what's needed for PLC programming
2. gather_requirements - Asking questions to clarify missing requirements, specifications, I/O, etc.
3. code_generation - Generating the actual Structured Text (ST) PLC code
4. refinement_testing - User feedback, code modifications, testing, debugging

RECENT CONVERSATION:
{history_text}

ANALYSIS INSTRUCTIONS:
- Determine if the conversation should stay in current stage or transition
- Consider: Are requirements clear? Are questions answered? Is code requested? Are refinements needed?
- Provide confidence (0.0-1.0) and specific reasoning
- List any required actions before stage transition

Respond in this exact format:
SUGGESTED_STAGE: [stage_name]
CONFIDENCE: [0.0-1.0]
TRANSITION_READY: [true/false]
REASONING: [brief explanation]
REQUIRED_ACTIONS: [action1, action2, ...]"""

        return context
    
    def _parse_stage_response(self, response: str, current_stage: ConversationStage) -> StageDetectionResponse:
        """Parse the LLM response into a structured stage detection response."""
        
        try:
            lines = response.strip().split('\n')
            parsed = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    parsed[key.strip().lower()] = value.strip()
            
            # Extract suggested stage
            suggested_stage_str = parsed.get('suggested_stage', current_stage.value)
            try:
                suggested_stage = ConversationStage(suggested_stage_str)
            except ValueError:
                suggested_stage = current_stage
            
            # Extract confidence
            confidence_str = parsed.get('confidence', '0.5')
            try:
                confidence = float(confidence_str)
                confidence = max(0.0, min(1.0, confidence))  # Clamp to [0,1]
            except ValueError:
                confidence = 0.5
            
            # Extract transition readiness
            transition_ready_str = parsed.get('transition_ready', 'false').lower()
            transition_ready = transition_ready_str in ['true', 'yes', '1']
            
            # Extract reasoning
            reasoning = parsed.get('reasoning', 'Stage analysis completed')
            
            # Extract required actions
            actions_str = parsed.get('required_actions', '')
            if actions_str:
                required_actions = [action.strip() for action in actions_str.split(',') if action.strip()]
            else:
                required_actions = []
            
            return StageDetectionResponse(
                suggested_stage=suggested_stage,
                confidence=confidence,
                reasoning=reasoning,
                transition_ready=transition_ready,
                required_actions=required_actions
            )
            
        except Exception as e:
            logger.warning("Failed to parse stage detection response", error=str(e), response=response)
            
            # Fallback parsing
            return StageDetectionResponse(
                suggested_stage=current_stage,
                confidence=0.3,
                reasoning=f"Failed to parse stage detection response: {str(e)}",
                transition_ready=False,
                required_actions=["Review stage detection logic"]
            )


class StageTransitionRules:
    """Rules for valid stage transitions."""
    
    VALID_TRANSITIONS = {
        ConversationStage.PROJECT_KICKOFF: [
            ConversationStage.GATHER_REQUIREMENTS,
            ConversationStage.CODE_GENERATION  # If requirements are complete
        ],
        ConversationStage.GATHER_REQUIREMENTS: [
            ConversationStage.PROJECT_KICKOFF,  # Back to requirements if major gaps
            ConversationStage.CODE_GENERATION,
            ConversationStage.GATHER_REQUIREMENTS  # Stay for more Q&A
        ],
        ConversationStage.CODE_GENERATION: [
            ConversationStage.GATHER_REQUIREMENTS,  # If more info needed
            ConversationStage.REFINEMENT_TESTING,
            ConversationStage.COMPLETED
        ],
        ConversationStage.REFINEMENT_TESTING: [
            ConversationStage.CODE_GENERATION,  # Major code changes
            ConversationStage.REFINEMENT_TESTING,  # Continue refinement
            ConversationStage.COMPLETED
        ],
        ConversationStage.COMPLETED: [
            ConversationStage.PROJECT_KICKOFF  # New project
        ]
    }
    
    @classmethod
    def is_valid_transition(cls, from_stage: ConversationStage, to_stage: ConversationStage) -> bool:
        """Check if a stage transition is valid."""
        valid_targets = cls.VALID_TRANSITIONS.get(from_stage, [])
        return to_stage in valid_targets
    
    @classmethod
    def get_valid_transitions(cls, from_stage: ConversationStage) -> List[ConversationStage]:
        """Get list of valid transitions from a given stage."""
        return cls.VALID_TRANSITIONS.get(from_stage, [])