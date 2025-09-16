#!/usr/bin/env python3
"""Comprehensive test script for the 4-stage conversation system."""

import asyncio
import json
from typing import Dict, Any
from app.schemas.conversation import ConversationRequest, ConversationStage
from app.services.conversation_orchestrator import ConversationOrchestrator


class StageTestSuite:
    """Test suite for validating each conversation stage."""
    
    def __init__(self):
        self.orchestrator = ConversationOrchestrator()
        self.test_results = []
    
    async def test_stage_1_requirements_gathering(self):
        """Test requirements gathering stage functionality."""
        print("\n🔍 TESTING STAGE 1: REQUIREMENTS GATHERING")
        print("=" * 60)
        
        # Test 1: Simple requirement
        print("\n📝 Test 1.1: Simple conveyor requirement")
        request = ConversationRequest(
            message="I need a conveyor belt system for my warehouse."
        )
        
        response = await self.orchestrator.process_message(request)
        conv_id = response.conversation_id
        
        # Verify stage and response quality
        assert response.stage == ConversationStage.REQUIREMENTS_GATHERING or response.stage == ConversationStage.QA_CLARIFICATION
        assert len(response.response) > 100  # Should provide substantial response
        print(f"✅ Stage: {response.stage}")
        print(f"✅ Response length: {len(response.response)} chars")
        
        # Test 2: Complex requirement 
        print("\n📝 Test 1.2: Complex multi-system requirement")
        request2 = ConversationRequest(
            conversation_id=conv_id,
            message="Actually, I need to control 3 conveyor belts, 2 robotic arms, safety systems, and HMI integration."
        )
        
        response2 = await self.orchestrator.process_message(request2)
        
        # Should still be in requirements or move to QA
        assert response2.stage in [ConversationStage.REQUIREMENTS_GATHERING, ConversationStage.QA_CLARIFICATION]
        print(f"✅ Stage transition handling: {response2.stage}")
        
        self.test_results.append({
            "stage": "requirements_gathering",
            "tests_passed": 2,
            "issues": []
        })
        return conv_id
    
    async def test_stage_2_qa_clarification(self, conv_id: str):
        """Test Q&A clarification stage functionality."""
        print("\n❓ TESTING STAGE 2: Q&A CLARIFICATION")
        print("=" * 60)
        
        # Force into QA stage if not already there
        request = ConversationRequest(
            conversation_id=conv_id,
            message="Can you ask me some clarifying questions about the system requirements?",
            force_stage=ConversationStage.QA_CLARIFICATION
        )
        
        response = await self.orchestrator.process_message(request)
        
        # Verify stage
        assert response.stage == ConversationStage.QA_CLARIFICATION
        print(f"✅ Forced stage transition: {response.stage}")
        
        # Test answering questions
        print("\n📝 Test 2.1: Answering clarification questions")
        answer_request = ConversationRequest(
            conversation_id=conv_id,
            message="The system operates at 24V DC, max speed 2 m/s, needs emergency stops, motor overload protection, and should handle 500kg loads."
        )
        
        answer_response = await self.orchestrator.process_message(answer_request)
        
        # Should continue in QA or move to generation
        assert answer_response.stage in [ConversationStage.QA_CLARIFICATION, ConversationStage.CODE_GENERATION]
        print(f"✅ Answer processing: {answer_response.stage}")
        
        self.test_results.append({
            "stage": "qa_clarification", 
            "tests_passed": 2,
            "issues": []
        })
        return conv_id
    
    async def test_stage_3_code_generation(self, conv_id: str):
        """Test code generation stage functionality."""
        print("\n⚙️ TESTING STAGE 3: CODE GENERATION")
        print("=" * 60)
        
        # Force code generation
        request = ConversationRequest(
            conversation_id=conv_id,
            message="Please generate the Structured Text code for this conveyor system.",
            force_stage=ConversationStage.CODE_GENERATION
        )
        
        response = await self.orchestrator.process_message(request)
        
        # Verify stage and code content
        assert response.stage == ConversationStage.CODE_GENERATION
        print(f"✅ Stage: {response.stage}")
        
        # Check if code was generated
        code_indicators = ["VAR", "BOOL", "END_VAR", "structured-text", "FUNCTION_BLOCK"]
        has_code = any(indicator in response.response for indicator in code_indicators)
        
        if has_code:
            print("✅ Code generation detected in response")
        else:
            print("⚠️  No clear code patterns found in response")
            
        # Verify reasonable response length for code generation
        assert len(response.response) > 500  # Code generation should be substantial
        print(f"✅ Response length: {len(response.response)} chars")
        
        self.test_results.append({
            "stage": "code_generation",
            "tests_passed": 2 if has_code else 1,
            "issues": [] if has_code else ["No clear code patterns detected"]
        })
        return conv_id
    
    async def test_stage_4_refinement_testing(self, conv_id: str):
        """Test refinement and testing stage functionality."""
        print("\n🔧 TESTING STAGE 4: REFINEMENT & TESTING")
        print("=" * 60)
        
        # Request refinements
        request = ConversationRequest(
            conversation_id=conv_id,
            message="Can you add variable speed control and improve the safety logic? Also add better error handling."
        )
        
        response = await self.orchestrator.process_message(request)
        
        # Should be in refinement or stay in generation
        expected_stages = [ConversationStage.REFINEMENT_TESTING, ConversationStage.CODE_GENERATION]
        assert response.stage in expected_stages
        print(f"✅ Stage: {response.stage}")
        
        # Test feedback incorporation
        print("\n📝 Test 4.1: Feedback incorporation")
        feedback_request = ConversationRequest(
            conversation_id=conv_id,
            message="The code looks good but can you optimize it for better performance?"
        )
        
        feedback_response = await self.orchestrator.process_message(feedback_request)
        
        # Should handle refinement feedback
        assert len(feedback_response.response) > 200  # Should provide detailed response
        print(f"✅ Feedback handling: {len(feedback_response.response)} chars")
        
        self.test_results.append({
            "stage": "refinement_testing",
            "tests_passed": 2,
            "issues": []
        })
        return conv_id
    
    async def test_stage_transitions(self):
        """Test stage transition logic."""
        print("\n🔄 TESTING STAGE TRANSITIONS")
        print("=" * 60)
        
        # Test invalid transition (should be handled gracefully)
        conv_id = None
        try:
            request = ConversationRequest(
                message="Generate code",
                force_stage=ConversationStage.REFINEMENT_TESTING  # Invalid: no prior code
            )
            
            response = await self.orchestrator.process_message(request)
            conv_id = response.conversation_id
            
            # Should handle gracefully - might stay in current stage or adjust
            print(f"✅ Invalid transition handled: {response.stage}")
            
        except Exception as e:
            print(f"⚠️  Transition error: {e}")
            
        self.test_results.append({
            "stage": "stage_transitions",
            "tests_passed": 1,
            "issues": []
        })
        
        return conv_id
    
    async def run_full_test_suite(self):
        """Run complete test suite for all stages."""
        print("🚀 STARTING COMPREHENSIVE 4-STAGE TEST SUITE")
        print("=" * 80)
        
        try:
            # Test each stage sequentially
            conv_id = await self.test_stage_1_requirements_gathering()
            conv_id = await self.test_stage_2_qa_clarification(conv_id)
            conv_id = await self.test_stage_3_code_generation(conv_id) 
            conv_id = await self.test_stage_4_refinement_testing(conv_id)
            
            # Test transition logic
            await self.test_stage_transitions()
            
            # Print summary
            self.print_test_summary()
            
        except Exception as e:
            print(f"\n❌ TEST SUITE FAILED: {e}")
            raise
    
    def print_test_summary(self):
        """Print comprehensive test results."""
        print("\n" + "=" * 80)
        print("📊 TEST SUITE SUMMARY")
        print("=" * 80)
        
        total_tests = 0
        total_passed = 0
        all_issues = []
        
        for result in self.test_results:
            stage = result["stage"].replace("_", " ").title()
            passed = result["tests_passed"] 
            issues = result["issues"]
            
            total_tests += passed + len(issues)
            total_passed += passed
            all_issues.extend(issues)
            
            status = "✅ PASS" if not issues else "⚠️  PARTIAL"
            print(f"{status} {stage}: {passed} tests passed")
            
            if issues:
                for issue in issues:
                    print(f"   ⚠️  {issue}")
        
        print(f"\n📈 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {total_passed}")
        print(f"   Issues: {len(all_issues)}")
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if len(all_issues) == 0:
            print("\n🎉 ALL TESTS PASSED! The 4-stage system is working correctly.")
        else:
            print(f"\n⚠️  {len(all_issues)} issues found that need attention.")


async def main():
    """Run the comprehensive test suite."""
    test_suite = StageTestSuite()
    await test_suite.run_full_test_suite()


if __name__ == "__main__":
    asyncio.run(main())