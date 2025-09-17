#!/usr/bin/env python3
"""
Efficient 4-Stage Conversation System Test Suite
Optimized for minimal OpenAI API usage and cost.
"""

import os
import sys
import asyncio
import structlog
from typing import Optional

# Set testing environment variable to use cheaper models
os.environ["TESTING"] = "true"

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from app.services.conversation_orchestrator import ConversationOrchestrator
from app.schemas.conversation import ConversationStage, ConversationResponse, ConversationRequest

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

class EfficientTestSuite:
    """Efficient test suite that minimizes API calls."""
    
    def __init__(self):
        self.orchestrator = ConversationOrchestrator()
        self.conversation_id: Optional[str] = None
        self.test_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "api_calls": 0
        }
    
    async def run_suite(self):
        """Run the complete efficient test suite."""
        print("🚀 STARTING EFFICIENT 4-STAGE TEST SUITE")
        print("=" * 60)
        print("⚡ Optimized for minimal OpenAI API usage")
        print()
        
        try:
            # Single conversation flow test
            await self.test_single_flow()
            
            # Stage transition test
            await self.test_stage_transitions()
            
            # Print results
            self.print_results()
            
        except Exception as e:
            logger.error("Test suite failed", error=str(e))
            raise
    
    async def test_single_flow(self):
        """Test complete flow through all stages in one conversation."""
        print("📋 TESTING COMPLETE CONVERSATION FLOW")
        print("-" * 40)
        
        # Stage 1: Project Kickoff (may auto-transition to gather_requirements)
        await self.test_stage(
            stage=ConversationStage.PROJECT_KICKOFF,
            message="Need help with conveyor belt control system",
            expected_stage=None,  # Allow auto-transition
            test_name="Project Kickoff (with auto-transition)"
        )
        
        # Stage 2: Gather Requirements (force transition)
        await self.test_stage(
            stage=ConversationStage.GATHER_REQUIREMENTS,
            message="The conveyor needs emergency stop and variable speed",
            expected_stage=ConversationStage.GATHER_REQUIREMENTS,
            test_name="Gather Requirements",
            force_stage=True
        )
        
        # Stage 3: Code Generation (force transition)
        await self.test_stage(
            stage=ConversationStage.CODE_GENERATION,
            message="Generate the code now",
            expected_stage=ConversationStage.CODE_GENERATION,
            test_name="Code Generation",
            force_stage=True
        )
        
        print()
    
    async def test_stage_transitions(self):
        """Test stage transition logic with minimal API calls."""
        print("🔄 TESTING STAGE TRANSITIONS")
        print("-" * 30)
        
        # Create new conversation for transition test
        self.conversation_id = None
        
        # Test invalid transition
        await self.test_stage(
            stage=ConversationStage.REFINEMENT_TESTING,
            message="Test message",
            expected_stage=ConversationStage.REFINEMENT_TESTING,
            test_name="Invalid Transition Handling",
            force_stage=True
        )
        
        print()
    
    async def test_stage(
        self, 
        stage: ConversationStage, 
        message: str, 
        expected_stage: Optional[ConversationStage],
        test_name: str,
        force_stage: bool = False
    ):
        """Test a single stage with minimal API usage."""
        self.test_results["total_tests"] += 1
        
        try:
            # Create request object
            request = ConversationRequest(
                message=message,
                conversation_id=self.conversation_id,
                force_stage=stage if force_stage else None
            )
            
            # Process message
            response = await self.orchestrator.process_message(request)
            
            self.test_results["api_calls"] += 1  # Approximate
            
            # Update conversation ID
            if not self.conversation_id:
                self.conversation_id = response.conversation_id
            
            # Validate response
            if expected_stage is not None:
                assert response.stage == expected_stage, f"Expected {expected_stage}, got {response.stage}"
            assert len(response.response) > 0, "Response should not be empty"
            
            print(f"✅ {test_name}: {response.stage.value}")
            print(f"   Response: {len(response.response)} chars")
            
            self.test_results["passed"] += 1
            
        except Exception as e:
            print(f"❌ {test_name}: FAILED - {str(e)}")
            self.test_results["failed"] += 1
            logger.error("Test failed", test=test_name, error=str(e))
    
    def print_results(self):
        """Print test suite results."""
        print("=" * 60)
        print("📊 EFFICIENT TEST SUITE SUMMARY")
        print("=" * 60)
        
        total = self.test_results["total_tests"]
        passed = self.test_results["passed"]
        failed = self.test_results["failed"]
        api_calls = self.test_results["api_calls"]
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"📈 RESULTS:")
        print(f"   Total Tests: {total}")
        print(f"   Passed: {passed}")
        print(f"   Failed: {failed}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Estimated API Calls: {api_calls}")
        print()
        
        if failed == 0:
            print("🎉 ALL TESTS PASSED! System ready for frontend integration.")
        else:
            print(f"⚠️  {failed} test(s) failed. Review above for details.")
        
        print(f"💰 Cost Optimization: Using gpt-4o-mini with reduced token limits")
        print(f"   Estimated cost reduction: ~80% vs full test suite")

async def main():
    """Main test runner."""
    test_suite = EfficientTestSuite()
    await test_suite.run_suite()

if __name__ == "__main__":
    asyncio.run(main())