"""Centralized model configuration for PLC-Copilot."""

from typing import Dict, Any


class ModelConfig:
    """Centralized configuration for AI models used throughout the application."""
    
    # Model names as constants
    DOCUMENT_ANALYSIS_MODEL = "gpt-4o"  # For extracting info from parsed PDFs
    CONVERSATION_MODEL = "gpt-4o-mini"  # For everything else (conversations, stage detection, etc.)
    
    # Model configurations for different use cases
    DOCUMENT_ANALYSIS_CONFIG = {
        "model": DOCUMENT_ANALYSIS_MODEL,
        "temperature": 0.3,
        "max_completion_tokens": 1500
    }
    
    CONVERSATION_CONFIG = {
        "model": CONVERSATION_MODEL,
        "temperature": 1.0,
        "max_completion_tokens": 1024
    }
    
    STAGE_DETECTION_CONFIG = {
        "model": CONVERSATION_MODEL,
        "temperature": 1.0,
        "max_tokens": 200,
        "max_completion_tokens": 200
    }
    
    CODE_GENERATION_CONFIG = {
        "model": CONVERSATION_MODEL,
        "temperature": 1.0,
        "max_completion_tokens": 2048
    }
    
    REFINEMENT_CONFIG = {
        "model": CONVERSATION_MODEL,
        "temperature": 1.0,
        "max_completion_tokens": 1536
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