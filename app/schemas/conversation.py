"""Schemas for multi-stage PLC-Copilot conversations."""

from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime


class ConversationStage(str, Enum):
    """Stages of a PLC-Copilot conversation."""
    PROJECT_KICKOFF = "project_kickoff"
    GATHER_REQUIREMENTS = "gather_requirements"
    CODE_GENERATION = "code_generation"
    REFINEMENT_TESTING = "refinement_testing"
    COMPLETED = "completed"


class MessageRole(str, Enum):
    """Message roles in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationMessage(BaseModel):
    """A single message in a conversation."""
    id: Optional[str] = None
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
    attachments: Optional[List[str]] = None  # Document IDs or file paths


class RequirementsState(BaseModel):
    """State tracking for requirements gathering stage."""
    user_query: str
    identified_requirements: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    confidence_level: float = Field(default=0.0, ge=0.0, le=1.0)


class QAState(BaseModel):
    """State tracking for Q&A clarification stage."""
    questions_asked: List[str] = Field(default_factory=list)
    answers_received: List[str] = Field(default_factory=list)
    remaining_questions: List[str] = Field(default_factory=list)
    clarification_complete: bool = False


class GenerationState(BaseModel):
    """State tracking for code generation stage."""
    generated_code: Optional[str] = None
    io_specification: Optional[Dict[str, Any]] = None
    simulation_plan: Optional[Dict[str, Any]] = None
    generation_metadata: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None


class RefinementState(BaseModel):
    """State tracking for refinement and testing stage."""
    refinement_requests: List[str] = Field(default_factory=list)
    code_versions: List[str] = Field(default_factory=list)
    test_results: List[Dict[str, Any]] = Field(default_factory=list)
    user_feedback: List[str] = Field(default_factory=list)


class ConversationState(BaseModel):
    """Complete conversation state."""
    conversation_id: str
    user_id: Optional[str] = None
    current_stage: ConversationStage
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Stage-specific states
    requirements: Optional[RequirementsState] = None
    qa: Optional[QAState] = None
    generation: Optional[GenerationState] = None
    refinement: Optional[RefinementState] = None
    
    # Message history
    messages: List[ConversationMessage] = Field(default_factory=list)
    
    # Global context
    project_context: Optional[Dict[str, Any]] = None
    document_ids: List[str] = Field(default_factory=list)


class StageTransitionRequest(BaseModel):
    """Request to transition between conversation stages."""
    conversation_id: str
    target_stage: ConversationStage
    reason: Optional[str] = None
    force: bool = False


class StageDetectionRequest(BaseModel):
    """Request for stage detection analysis."""
    conversation_id: str
    recent_messages: List[ConversationMessage]
    current_stage: ConversationStage
    context: Optional[Dict[str, Any]] = None


class StageDetectionResponse(BaseModel):
    """Response from stage detection service."""
    suggested_stage: ConversationStage
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    transition_ready: bool
    required_actions: List[str] = Field(default_factory=list)


class ConversationRequest(BaseModel):
    """Request to continue a conversation."""
    conversation_id: Optional[str] = None
    message: str
    attachments: Optional[List[str]] = None
    force_stage: Optional[ConversationStage] = None
    context: Optional[Dict[str, Any]] = None


class ConversationResponse(BaseModel):
    """Response from conversation system."""
    conversation_id: str
    stage: ConversationStage
    response: str
    next_stage: Optional[ConversationStage] = None
    stage_progress: Optional[Dict[str, Any]] = None
    suggested_actions: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    # MCQ functionality
    is_mcq: bool = False
    mcq_question: Optional[str] = None
    mcq_options: List[str] = Field(default_factory=list)