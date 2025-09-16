"""Centralized model configuration for PLC-Copilot."""

import os
from typing import Dict, Any


class ModelConfig:
    """Centralized configuration for AI models used throughout the application."""
    
    # Environment-based model selection for cost optimization
    _is_testing = os.getenv("TESTING", "false").lower() == "true"
    _is_dev = os.getenv("ENVIRONMENT", "production") == "development"
    
    # Model names as constants - optimized for cost
    # Use cheaper models in testing/dev, premium models in production
    if _is_testing:
        DOCUMENT_ANALYSIS_MODEL = "gpt-4o-mini"  # Use cheaper model for tests
        CONVERSATION_MODEL = "gpt-4o-mini"
    elif _is_dev:
        DOCUMENT_ANALYSIS_MODEL = "gpt-4o-mini"  # Use cheaper model for dev
        CONVERSATION_MODEL = "gpt-4o-mini"
    else:
        DOCUMENT_ANALYSIS_MODEL = "gpt-4o"  # For extracting info from parsed PDFs
        CONVERSATION_MODEL = "gpt-4o-mini"  # For everything else (conversations, stage detection, etc.)
    
    # Model configurations for different use cases - optimized token limits
    DOCUMENT_ANALYSIS_CONFIG = {
        "model": DOCUMENT_ANALYSIS_MODEL,
        "temperature": 0.3,
        "max_completion_tokens": 1000 if _is_testing else 1500  # Reduce tokens in testing
    }
    
    CONVERSATION_CONFIG = {
        "model": CONVERSATION_MODEL,
        "temperature": 1.0,
        "max_completion_tokens": 512 if _is_testing else 1024  # Reduce tokens in testing
    }
    
    STAGE_DETECTION_CONFIG = {
        "model": CONVERSATION_MODEL,
        "temperature": 1.0,
        "max_tokens": 100 if _is_testing else 200,  # Significantly reduce for testing
        "max_completion_tokens": 100 if _is_testing else 200
    }
    
    CODE_GENERATION_CONFIG = {
        "model": CONVERSATION_MODEL,
        "temperature": 1.0,
        "max_completion_tokens": 1024 if _is_testing else 2048  # Reduce tokens in testing
    }
    
    REFINEMENT_CONFIG = {
        "model": CONVERSATION_MODEL,
        "temperature": 1.0,
        "max_completion_tokens": 768 if _is_testing else 1536  # Reduce tokens in testing
    }
    
    @classmethod
    def get_model_for_task(cls, task: str) -> str:
        """Get the appropriate model for a specific task."""
        if task == "document_analysis":
            return cls.DOCUMENT_ANALYSIS_MODEL
        else:
            return cls.CONVERSATION_MODEL
    
    @classmethod
    def get_config_for_task(cls, task: str) -> Dict[str, Any]:
        """Get the complete configuration for a specific task."""
        configs = {
            "document_analysis": cls.DOCUMENT_ANALYSIS_CONFIG,
            "conversation": cls.CONVERSATION_CONFIG,
            "stage_detection": cls.STAGE_DETECTION_CONFIG,
            "code_generation": cls.CODE_GENERATION_CONFIG,
            "refinement": cls.REFINEMENT_CONFIG
        }
        return configs.get(task, cls.CONVERSATION_CONFIG)