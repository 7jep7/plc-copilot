"""
Context-centric schemas for the new unified API.

This module defines the data structures for the context-based approach where:
1. device_constants: Flexible nested JSON for device specifications
2. information: Markdown text summarizing project requirements
3. Single endpoint for all user interactions with files, MCQs, and stage management
"""

from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class Stage(str, Enum):
    """Available workflow stages."""
    GATHERING_REQUIREMENTS = "gathering_requirements"
    CODE_GENERATION = "code_generation"
    REFINEMENT_TESTING = "refinement_testing"


class DeviceOrigin(str, Enum):
    """Source of device information."""
    FILE = "file"
    USER_MESSAGE = "user message"
    INTERNET = "internet"
    INTERNAL_KNOWLEDGE_BASE = "internal knowledge base"
    OTHER = "other"


class DeviceEntry(BaseModel):
    """Device entry with origin tracking."""
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Device specifications and properties"
    )
    origin: DeviceOrigin = Field(
        DeviceOrigin.OTHER,
        description="Source of this device information"
    )


class ProjectContext(BaseModel):
    """Complete project context structure."""
    # Keep device_constants flexible and JSON-serializable for backwards compatibility with tests
    device_constants: Dict[str, Any] = Field(
        default_factory=dict,
        description="Device specifications with origin tracking. Keys are device names, values are dicts or DeviceEntry-like structures."
    )
    information: str = Field(
        default="",
        description="Markdown-formatted summary of project requirements, decisions, and notes"
    )


class FileProcessingResult(BaseModel):
    """Result of processing an uploaded file."""
    extracted_devices: Dict[str, Any] = Field(
        default_factory=dict,
        description="Device specifications extracted from file"
    )
    extracted_information: str = Field(
        default="",
        description="Relevant project information extracted from file"
    )
    processing_summary: str = Field(
        description="Brief summary of what was extracted from the file"
    )


class ContextUpdateRequest(BaseModel):
    """Request for updating project context."""
    message: Optional[str] = Field(None, description="User message or response")
    mcq_responses: List[str] = Field(
        default_factory=list,
        description="Selected MCQ options if responding to multiple choice question"
    )
    previous_copilot_message: Optional[str] = Field(
        None,
        description="Previous message from the copilot for conversation continuity"
    )
    current_context: ProjectContext = Field(
        default_factory=ProjectContext,
        description="Current project context state"
    )
    current_stage: Stage = Field(
        Stage.GATHERING_REQUIREMENTS,
        description="Current workflow stage"
    )


class ContextUpdateResponse(BaseModel):
    """Response from context update with all necessary UI information."""
    updated_context: ProjectContext = Field(
        description="Updated project context with new information integrated"
    )
    chat_message: str = Field(
        description="AI response message to display to user"
    )
    gathering_requirements_estimated_progress: Optional[float] = Field(
        None,
        description="AI's estimation of requirements completion (0.0-1.0) for automatic stage transition",
        ge=0.0,
        le=1.0
    )
    current_stage: Stage = Field(
        description="Current workflow stage after processing"
    )
    is_mcq: bool = Field(
        False,
        description="Whether the response contains a multiple choice question"
    )
    is_multiselect: bool = Field(
        False,
        description="Whether MCQ allows multiple selections"
    )
    mcq_question: Optional[str] = Field(
        None,
        description="MCQ question text (only when is_mcq=True)"
    )
    mcq_options: List[str] = Field(
        default_factory=list,
        description="MCQ answer options (only when is_mcq=True)"
    )
    generated_code: Optional[str] = Field(
        None,
        description="Generated Structured Text code (only when current_stage=code_generation)"
    )
    file_extractions: List[FileProcessingResult] = Field(
        default_factory=list,
        description="List of file extraction results (one per uploaded file)"
    )


class StageTransitionRequest(BaseModel):
    """Request to manually transition to a specific stage."""
    target_stage: Stage = Field(description="Stage to transition to")
    force: bool = Field(
        False,
        description="Force transition even if AI would recommend staying in current stage"
    )


class StageTransitionResponse(BaseModel):
    """Response indicating stage transition result."""
    new_stage: Stage = Field(description="Stage after transition")
    transition_message: str = Field(description="Message explaining the transition")
    success: bool = Field(description="Whether transition was successful")