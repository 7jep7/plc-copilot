"""Database models for multi-stage conversations."""

from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Enum, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.models.base import Base
from app.schemas.conversation import ConversationStage, MessageRole


class Conversation(Base):
    """Database model for conversation state."""
    
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(String, nullable=True, index=True)
    
    current_stage = Column(Enum(ConversationStage), nullable=False, default=ConversationStage.PROJECT_KICKOFF)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Project context as JSON
    project_context = Column(JSON, nullable=True)
    document_ids = Column(JSON, nullable=True)  # List of document IDs
    
    # Stage-specific state as JSON
    requirements_state = Column(JSON, nullable=True)
    qa_state = Column(JSON, nullable=True)
    generation_state = Column(JSON, nullable=True)
    refinement_state = Column(JSON, nullable=True)
    
    # Relationships
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.conversation_id}, stage={self.current_stage})>"


class ConversationMessage(Base):
    """Database model for conversation messages."""
    
    __tablename__ = "conversation_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Message metadata as JSON
    metadata = Column(JSON, nullable=True)
    attachments = Column(JSON, nullable=True)  # List of attachment IDs/paths
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<ConversationMessage(role={self.role}, timestamp={self.timestamp})>"


class ConversationTemplate(Base):
    """Database model for conversation prompt templates."""
    
    __tablename__ = "conversation_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    stage = Column(Enum(ConversationStage), nullable=False)
    
    system_prompt = Column(Text, nullable=False)
    user_prompt_template = Column(Text, nullable=True)
    
    # Model configuration as JSON
    model_config = Column(JSON, nullable=True)
    
    # Versioning and metadata
    version = Column(String, nullable=False, default="1.0")
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<ConversationTemplate(name={self.name}, stage={self.stage})>"


class ConversationMetrics(Base):
    """Database model for conversation analytics and metrics."""
    
    __tablename__ = "conversation_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    
    # Stage progression metrics
    stage = Column(Enum(ConversationStage), nullable=False)
    stage_entered_at = Column(DateTime, nullable=False)
    stage_duration_seconds = Column(Integer, nullable=True)  # Filled when leaving stage
    
    # Quality metrics
    user_satisfaction = Column(Float, nullable=True)  # 0.0 to 1.0
    stage_completion_quality = Column(Float, nullable=True)  # 0.0 to 1.0
    
    # Token usage metrics
    tokens_used = Column(Integer, nullable=True)
    api_calls_count = Column(Integer, nullable=True)
    
    # Error tracking
    error_count = Column(Integer, default=0, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<ConversationMetrics(conversation_id={self.conversation_id}, stage={self.stage})>"