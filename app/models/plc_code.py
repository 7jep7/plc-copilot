"""PLC code model for storing generated structured text code."""

from sqlalchemy import Column, String, Text, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from enum import Enum

from app.models.base import BaseModel


class PLCLanguage(str, Enum):
    """Supported PLC programming languages."""
    STRUCTURED_TEXT = "structured_text"
    LADDER_LOGIC = "ladder_logic"
    FUNCTION_BLOCK = "function_block"
    INSTRUCTION_LIST = "instruction_list"
    SEQUENTIAL_FUNCTION_CHART = "sequential_function_chart"


class PLCCodeStatus(str, Enum):
    """PLC code generation and validation status."""
    DRAFT = "draft"
    GENERATED = "generated"
    VALIDATED = "validated"
    TESTED = "tested"
    DEPLOYED = "deployed"
    FAILED = "failed"


class PLCCode(BaseModel):
    """Model for storing generated PLC code and related metadata."""
    
    __tablename__ = "plc_codes"
    
    # Basic information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(50), default="1.0.0")
    
    # Code content
    language = Column(String(50), default=PLCLanguage.STRUCTURED_TEXT.value)
    source_code = Column(Text, nullable=False)
    compiled_code = Column(Text, nullable=True)
    
    # Generation metadata
    user_prompt = Column(Text, nullable=False)
    ai_model_used = Column(String(100), nullable=True)
    generation_parameters = Column(JSONB, nullable=True)  # Temperature, max_tokens, etc.
    
    # Status and validation
    status = Column(String(20), default=PLCCodeStatus.DRAFT.value)
    validation_results = Column(JSONB, nullable=True)
    test_results = Column(JSONB, nullable=True)
    
    # Relationships
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    document = relationship("Document", backref="plc_codes")
    
    # Configuration and I/O
    input_variables = Column(JSONB, nullable=True)  # Input variable definitions
    output_variables = Column(JSONB, nullable=True)  # Output variable definitions
    configuration = Column(JSONB, nullable=True)  # PLC configuration settings
    
    # Performance metrics
    execution_time_estimate = Column(Float, nullable=True)  # Estimated execution time in ms
    memory_usage_estimate = Column(Float, nullable=True)  # Estimated memory usage in KB
    
    def __repr__(self):
        return f"<PLCCode(id={self.id}, name={self.name}, language={self.language}, status={self.status})>"