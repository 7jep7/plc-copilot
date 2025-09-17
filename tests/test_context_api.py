"""
Comprehensive test suite for the new context-centric API.

Tests cover:
- Context updates and integration
- File processing and extraction
- Stage transitions and management
- MCQ handling and responses
- Structured Text generation
- Progress calculation
"""

import json
import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock
from io import BytesIO

from app.schemas.context import (
    ProjectContext,
    ContextUpdateRequest,
    ContextUpdateResponse,
    FileProcessingResult,
    Stage
)
from app.services.context_service import ContextProcessingService


class TestContextProcessingService:
    """Test suite for ContextProcessingService."""

    @pytest.fixture
    def context_service(self):
        """Create a context service instance for testing."""
        with patch('app.services.context_service.OpenAIService') as mock_openai:
            service = ContextProcessingService()
            service.openai_service = mock_openai.return_value
            return service

    @pytest.fixture
    def sample_context(self):
        """Sample project context for testing."""
        return ProjectContext(
            device_constants={
                "ConveyorMotor": {
                    "Type": "AC Servo",
                    "Power": "2.5kW",
                    "Voltage": "400V"
                },
                "SafetySystem": {
                    "EmergencyStops": {"Count": 2, "Type": "Category 3"}
                }
            },
            information="## Project Requirements\n- Conveyor belt control system\n- Safety requirements: emergency stops\n- Speed control needed"
        )

    @pytest.fixture
    def sample_pdf_bytes(self):
        """Mock PDF file bytes for testing."""
        # This would be actual PDF bytes in real tests
        return b"%PDF-1.4 mock pdf content"

    @pytest.mark.asyncio
    async def test_process_context_update_basic_message(self, context_service, sample_context):
        """Test basic context update with user message."""
        # Mock AI response for context update
        mock_ai_response = Mock()
        mock_ai_response.content = json.dumps({
            "device_constants": sample_context.device_constants,
            "information": sample_context.information + "\n- Additional info from user"
        })
        context_service.openai_service.chat_completion.return_value = mock_ai_response

        # Mock AI response for requirements question
        mock_question_response = Mock()
        mock_question_response.content = json.dumps({
            "message": "What type of sensors will detect items on the conveyor?",
            "is_mcq": False
        })
        
        # Set up multiple returns for different calls
        context_service.openai_service.chat_completion.side_effect = [
            mock_ai_response,  # First call for context update
            mock_question_response  # Second call for question generation
        ]

        request = ContextUpdateRequest(
            message="I need optical sensors for detection",
            current_context=sample_context,
            current_stage=Stage.GATHERING_REQUIREMENTS
        )

        response = await context_service.process_context_update(request)

        assert isinstance(response, ContextUpdateResponse)
        assert response.current_stage == Stage.GATHERING_REQUIREMENTS
        assert response.gathering_requirements_estimated_progress is not None
        assert response.chat_message == "What type of sensors will detect items on the conveyor?"
        assert not response.is_mcq

    @pytest.mark.asyncio
    async def test_mcq_generation_and_response(self, context_service, sample_context):
        """Test MCQ generation and handling of MCQ responses."""
        # Mock AI response for MCQ generation
        mock_mcq_response = Mock()
        mock_mcq_response.content = json.dumps({
            "message": "Select safety features for your conveyor system:",
            "is_mcq": True,
            "mcq_question": "What safety features do you require?",
            "mcq_options": [
                "Emergency stop buttons only",
                "Light curtains for perimeter protection", 
                "Safety mats for operator zones",
                "Comprehensive safety package"
            ],
            "is_multiselect": False
        })

        context_service.openai_service.chat_completion.side_effect = [
            mock_mcq_response  # MCQ question response
        ]

        request = ContextUpdateRequest(
            message="I need safety features",
            current_context=sample_context,
            current_stage=Stage.GATHERING_REQUIREMENTS
        )

        response = await context_service.process_context_update(request)

        assert response.is_mcq
        assert response.mcq_question == "What safety features do you require?"
        assert len(response.mcq_options) == 4
        assert "Emergency stop buttons only" in response.mcq_options

    @pytest.mark.asyncio
    async def test_file_processing_integration(self, context_service, sample_context, sample_pdf_bytes):
        """Test file upload processing and context integration."""
        # Mock text extraction
        with patch.object(context_service, '_extract_text_from_bytes') as mock_extract:
            mock_extract.return_value = "Motor specifications: 3-phase AC motor, 2.5kW, 400V, IP65 protection"

            # Mock AI response for file extraction
            mock_extraction_response = Mock()
            mock_extraction_response.content = json.dumps({
                "devices": {
                    "Motor1": {
                        "Type": "AC Motor",
                        "Power": "2.5kW",
                        "Voltage": "400V",
                        "Protection": "IP65"
                    }
                },
                "information": "3-phase AC motor with IP65 protection rating",
                "summary": "Extracted motor specifications from datasheet"
            })

            # Mock AI response for requirements question
            mock_question_response = Mock()
            mock_question_response.content = json.dumps({
                "message": "Great! I've processed the motor specifications. What control method do you prefer?",
                "is_mcq": False
            })

            context_service.openai_service.chat_completion.side_effect = [
                mock_extraction_response,  # File extraction
                mock_question_response     # Follow-up question
            ]

            file_data = BytesIO(sample_pdf_bytes)
            request = ContextUpdateRequest(
                current_context=sample_context,
                current_stage=Stage.GATHERING_REQUIREMENTS
            )

            response = await context_service.process_context_update(request, uploaded_files=[file_data])

            # Check that file content was integrated
            assert "Motor1" in response.updated_context.device_constants
            assert "3-phase AC motor" in response.updated_context.information
            assert "motor specifications" in response.chat_message.lower()

    @pytest.mark.asyncio
    async def test_code_generation_stage(self, context_service, sample_context):
        """Test Structured Text code generation with proper JSON response."""
        mock_code_response = Mock()
        mock_code_response.content = """{
    "updated_context": {
        "device_constants": {},
        "information": "Generated PLC code for conveyor control system"
    },
    "chat_message": "I've generated the Structured Text code for your conveyor system.",
    "is_mcq": false,
    "mcq_question": null,
    "mcq_options": [],
    "is_multiselect": false,
    "generated_code": "PROGRAM ConveyorControl\\nVAR\\n    StartButton : BOOL;\\n    StopButton : BOOL;\\n    MotorRun : BOOL;\\nEND_VAR\\n\\n// Main logic\\nMotorRun := StartButton AND NOT StopButton;\\n\\nEND_PROGRAM"
}"""

        context_service.openai_service.chat_completion.return_value = mock_code_response

        request = ContextUpdateRequest(
            current_context=sample_context,
            current_stage=Stage.CODE_GENERATION
        )

        response = await context_service.process_context_update(request)

        assert response.current_stage == Stage.CODE_GENERATION  # Stage doesn't auto-transition
        assert response.generated_code is not None
        assert "PROGRAM ConveyorControl" in response.generated_code
        assert "MotorRun" in response.generated_code
        assert response.gathering_requirements_estimated_progress is None  # Not in requirements stage

    @pytest.mark.asyncio
    async def test_code_generation_non_json_fallback(self, context_service, sample_context):
        """Test that non-JSON responses during CODE_GENERATION are handled with retry, not auto-transition."""
        # Mock a raw code response (non-JSON) for both calls
        mock_code_response = Mock()
        mock_code_response.content = """
PROGRAM ConveyorControl
VAR
    StartButton : BOOL;
    StopButton : BOOL; 
    MotorRun : BOOL;
    ConveyorSpeed : REAL := 1.5;
END_VAR

// Main control logic
MotorRun := StartButton AND NOT StopButton;

END_PROGRAM
"""

        context_service.openai_service.chat_completion.return_value = mock_code_response

        request = ContextUpdateRequest(
            current_context=sample_context,
            current_stage=Stage.CODE_GENERATION
        )

        response = await context_service.process_context_update(request)

        # Should stay in CODE_GENERATION stage and return error message
        assert response.current_stage == Stage.CODE_GENERATION
        assert response.generated_code is None
        assert "error processing your request" in response.chat_message.lower()
        assert response.is_mcq is False

    @pytest.mark.asyncio
    async def test_refinement_testing_stage(self, context_service, sample_context):
        """Test refinement and testing stage interactions."""
        mock_refinement_response = Mock()
        mock_refinement_response.content = json.dumps({
            "message": "I can help improve the safety logic. Would you like to add timeout protection?",
            "is_mcq": True,
            "mcq_question": "What safety improvements would you like?",
            "mcq_options": [
                "Add motor timeout protection",
                "Implement speed monitoring",
                "Add fault diagnostics",
                "All of the above"
            ],
            "is_multiselect": True
        })

        context_service.openai_service.chat_completion.return_value = mock_refinement_response

        request = ContextUpdateRequest(
            message="I want to improve the safety features",
            current_context=sample_context,
            current_stage=Stage.REFINEMENT_TESTING
        )

        response = await context_service.process_context_update(request)

        assert response.current_stage == Stage.REFINEMENT_TESTING
        assert response.is_mcq
        assert response.is_multiselect
        assert "safety improvements" in response.mcq_question.lower()

    def test_file_extraction_error_handling(self, context_service):
        """Test error handling in file processing."""
        with patch.object(context_service, '_extract_text_from_bytes') as mock_extract:
            mock_extract.side_effect = Exception("PDF parsing failed")

            result = asyncio.run(context_service._process_uploaded_file(BytesIO(b"invalid data")))

            assert isinstance(result, FileProcessingResult)
            assert result.extracted_devices == {}
            assert "Error processing file" in result.processing_summary

    def test_context_integration_merge_devices(self, context_service, sample_context):
        """Test merging of device specifications from file extraction."""
        extraction_result = FileProcessingResult(
            extracted_devices={
                "ConveyorMotor": {  # Existing device - should merge
                    "Efficiency": "IE3",
                    "RPM": "1440"
                },
                "NewSensor": {  # New device - should add
                    "Type": "Proximity",
                    "Range": "8mm"
                }
            },
            extracted_information="Additional sensor specifications",
            processing_summary="Extracted sensor data"
        )

        updated_context = context_service._integrate_file_extraction(sample_context, extraction_result)

        # Check device merging
        assert "Efficiency" in updated_context.device_constants["ConveyorMotor"]
        assert "Power" in updated_context.device_constants["ConveyorMotor"]  # Original preserved
        assert "NewSensor" in updated_context.device_constants

        # Check information appending
        assert "Additional sensor specifications" in updated_context.information


@pytest.mark.integration
class TestContextAPIIntegration:
    """Integration tests for the context API endpoints."""

    @pytest.mark.asyncio
    async def test_context_update_endpoint_basic(self):
        """Test the main context update endpoint with basic input."""
        from app.api.api_v1.endpoints.context import update_context
        from fastapi import Form

        # Mock the context service
        with patch('app.api.api_v1.endpoints.context.ContextProcessingService') as MockService:
            mock_service = MockService.return_value
            mock_response = ContextUpdateResponse(
                updated_context=ProjectContext(),
                chat_message="Test response",
                current_stage=Stage.GATHERING_REQUIREMENTS,
                is_mcq=False,
                is_multiselect=False,
                mcq_question=None,
                mcq_options=[]
            )
            mock_service.process_context_update.return_value = mock_response

            # Test the endpoint
            result = await update_context(
                message="Test message",
                mcq_responses=None,
                previous_copilot_message=None,
                current_context='{"device_constants": {}, "information": ""}',
                current_stage=Stage.GATHERING_REQUIREMENTS,
                files=[]
            )

            assert isinstance(result, ContextUpdateResponse)
            assert result.chat_message == "Test response"
            mock_service.process_context_update.assert_called_once()

    def test_stage_transition_validation(self):
        """Test stage transition validation logic."""
        from app.api.api_v1.endpoints.context import transition_stage
        from app.schemas.context import StageTransitionRequest

        # Test invalid transition (back to requirements gathering)
        request = StageTransitionRequest(
            target_stage=Stage.GATHERING_REQUIREMENTS,
            force=False
        )

        result = asyncio.run(transition_stage(request))
        assert not result.success
        assert "Cannot return to requirements gathering" in result.transition_message


if __name__ == "__main__":
    # Run specific tests
    pytest.main([__file__, "-v"])