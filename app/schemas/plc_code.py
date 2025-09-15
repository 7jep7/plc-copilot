"""PLC code schemas for request/response validation."""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.plc_code import PLCLanguage, PLCCodeStatus


class PLCCodeBase(BaseModel):
    """Base PLC code schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    language: PLCLanguage = PLCLanguage.STRUCTURED_TEXT


class PLCCodeCreate(PLCCodeBase):
    """Schema for creating PLC code manually."""
    source_code: str = Field(..., min_length=1)
    version: str = "1.0.0"
    user_prompt: str = Field(..., min_length=1)


class PLCGenerationRequest(BaseModel):
    """Schema for PLC code generation requests."""
    user_prompt: str = Field(..., min_length=1, max_length=4000)
    language: PLCLanguage = PLCLanguage.STRUCTURED_TEXT
    document_id: Optional[str] = None
    generation_parameters: Optional[Dict[str, Any]] = None
    name: Optional[str] = None
    description: Optional[str] = None
    
    # AI model parameters
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    # Accept both legacy `max_tokens` and new `max_completion_tokens`.
    max_tokens: Optional[int] = Field(default=2000, gt=0, le=4000)
    max_completion_tokens: Optional[int] = Field(default=None, gt=0, le=4000)
    
    # Context parameters
    include_io_definitions: bool = True
    include_safety_checks: bool = True
    target_plc_type: Optional[str] = None


class PLCCodeUpdate(BaseModel):
    """Schema for updating PLC code."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    source_code: Optional[str] = None
    version: Optional[str] = None
    status: Optional[PLCCodeStatus] = None


class PLCCodeResponse(PLCCodeBase):
    """Schema for PLC code responses."""
    id: str
    version: str
    source_code: str
    compiled_code: Optional[str] = None
    user_prompt: str
    ai_model_used: Optional[str] = None
    generation_parameters: Optional[Dict[str, Any]] = None
    status: str
    validation_results: Optional[Dict[str, Any]] = None
    test_results: Optional[Dict[str, Any]] = None
    document_id: Optional[str] = None
    input_variables: Optional[Dict[str, Any]] = None
    output_variables: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None
    execution_time_estimate: Optional[float] = None
    memory_usage_estimate: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ValidationResult(BaseModel):
    """Schema for code validation results."""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    syntax_score: Optional[float] = None
    complexity_score: Optional[float] = None
    validation_metadata: Optional[Dict[str, Any]] = None


class CompilationResult(BaseModel):
    """Schema for code compilation results."""
    success: bool
    compiled_code: Optional[str] = None
    compilation_errors: List[str] = []
    compilation_warnings: List[str] = []
    binary_size: Optional[int] = None
    compilation_time: Optional[float] = None