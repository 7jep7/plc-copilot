"""Prompt templates for different conversation stages in PLC-Copilot."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.schemas.conversation import ConversationStage, ConversationState, ConversationMessage


class PromptTemplate(ABC):
    """Base class for stage-specific prompt templates."""
    
    @abstractmethod
    def build_system_prompt(self, state: ConversationState) -> str:
        """Build the system prompt for this stage."""
        pass
    
    @abstractmethod
    def build_user_prompt(self, message: str, state: ConversationState) -> str:
        """Build the user prompt for this stage."""
        pass
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration for this stage."""
        return {
            "model": "gpt-4",
            "temperature": 1.0,
            "max_completion_tokens": 1024
        }


class RequirementsGatheringTemplate(PromptTemplate):
    """Template for requirements gathering stage."""
    
    def build_system_prompt(self, state: ConversationState) -> str:
        return """You are PLC-Copilot Requirements Analyst — an expert Programmable Logic Controller (PLC) systems engineer specializing in requirements gathering for industrial automation projects.

Your mission: Analyze user requests, identify technical requirements, and determine what additional information is needed for PLC code generation.

CORE RESPONSIBILITIES:
1. Parse user queries to extract:
   - Control objectives (what should the system do?)
   - I/O requirements (sensors, actuators, communication)
   - Safety requirements and constraints
   - Performance requirements (timing, accuracy)
   - Target PLC platform and standards

2. Identify missing critical information:
   - Unclear control logic or sequences
   - Missing I/O specifications or datasheets
   - Undefined safety requirements
   - Unspecified operating parameters

3. Ask targeted clarifying questions:
   - Prioritize safety-critical gaps first
   - Ask specific, actionable questions
   - Avoid overwhelming the user with too many questions at once

RESPONSE FORMAT:
## Clarification Analysis

**Information Received:**
- [Summarize new information from user response]

**Updated Understanding:**
- [How this changes/confirms your understanding]

**Remaining Questions:**
1. [Most critical remaining question]
2. [Secondary question]
3. [Tertiary question - if needed]

**Ready for Code Generation?** [Yes/No] - [reasoning]

**Recommendations:**
- [Any technical recommendations based on clarifications]
Always respond with this structure:
"""

    def build_user_prompt(self, message: str, state: ConversationState) -> str:
        context_parts = [f"User Request: {message}"]
        
        # Add document context if available
        if state.document_ids:
            context_parts.append(f"Available Documents: {len(state.document_ids)} documents attached")
        
        # Add previous requirements if this is a follow-up
        if state.requirements and state.requirements.identified_requirements:
            context_parts.append("Previous Requirements Identified:")
            for req in state.requirements.identified_requirements:
                context_parts.append(f"- {req}")
        
        return "\n".join(context_parts)
    
    def get_model_config(self) -> Dict[str, Any]:
        return {
            "model": "gpt-5-nano",  # Use available model
            "temperature": 1.0,  # Use default temperature
            "max_completion_tokens": 800
        }


class QAClarificationTemplate(PromptTemplate):
    """Template for Q&A clarification stage."""
    
    def build_system_prompt(self, state: ConversationState) -> str:
        return """You are PLC-Copilot Technical Interviewer — an expert PLC engineer conducting technical clarification interviews.

Your mission: Ask precise, technical questions to fill knowledge gaps and validate assumptions for PLC code generation.

RESPONSE FORMAT:
## Clarification Analysis

**Information Received:**
- [Summarize new information from user response]

**Remaining Questions:**
1. [Most critical remaining question]
2. [Secondary question]

**Ready for Code Generation?** [Yes/No] - [reasoning]
"""

    def build_user_prompt(self, message: str, state: ConversationState) -> str:
        return f"User Response: {message}"


class CodeGenerationTemplate(PromptTemplate):
    """Template for code generation stage."""
    
    def build_system_prompt(self, state: ConversationState) -> str:
        return """You are PLC-Copilot Code Generator — an expert IEC 61131-3 Structured Text programmer.

Generate production-ready Structured Text (ST) code based on requirements.

RESPONSE FORMAT:
## Generated PLC Code

### Structured Text Code
```st
[Full ST code here]
```

### Explanation
[Detailed explanation of the logic and operation]
"""

    def build_user_prompt(self, message: str, state: ConversationState) -> str:
        return f"Generation Request: {message}"
    
    def get_model_config(self) -> Dict[str, Any]:
        return {
            "model": "gpt-5-nano",
            "temperature": 1.0,
            "max_completion_tokens": 2048
        }


class RefinementTestingTemplate(PromptTemplate):
    """Template for refinement and testing stage."""
    
    def build_system_prompt(self, state: ConversationState) -> str:
        return """You are PLC-Copilot Code Reviewer — an expert focused on code improvement and testing.

Help users refine and improve generated PLC code based on feedback.

RESPONSE FORMAT:
## Code Refinement

### Modified Code
```st
[Updated ST code]
```

### Change Explanation
[Explanation of modifications]
"""

    def build_user_prompt(self, message: str, state: ConversationState) -> str:
        return f"Refinement Request: {message}"
    
    def get_model_config(self) -> Dict[str, Any]:
        return {
            "model": "gpt-5-nano",
            "temperature": 1.0,
            "max_completion_tokens": 1536
        }


class PromptTemplateFactory:
    """Factory for creating stage-specific prompt templates."""
    
    _templates = {
        ConversationStage.REQUIREMENTS_GATHERING: RequirementsGatheringTemplate,
        ConversationStage.QA_CLARIFICATION: QAClarificationTemplate,
        ConversationStage.CODE_GENERATION: CodeGenerationTemplate,
        ConversationStage.REFINEMENT_TESTING: RefinementTestingTemplate,
    }
    
    @classmethod
    def get_template(cls, stage: ConversationStage) -> PromptTemplate:
        """Get the appropriate template for a conversation stage."""
        template_class = cls._templates.get(stage)
        if not template_class:
            raise ValueError(f"No template available for stage: {stage}")
        return template_class()
    
    @classmethod
    def get_available_stages(cls) -> List[ConversationStage]:
        """Get list of stages with available templates."""
        return list(cls._templates.keys())
