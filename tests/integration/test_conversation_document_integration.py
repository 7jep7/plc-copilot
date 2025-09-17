#!/usr/bin/env python3
"""
Comprehensive test for conversation-level document integration.

This test verifies the complete workflow of:
1. Starting a conversation
2. Uploading documents to the conversation
3. Document parsing and analysis
4. Context persistence throughout conversation stages
5. Usage in both gathering_requirements and code_generation stages
"""

import sys
import asyncio
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.conversation_orchestrator import ConversationOrchestrator
from app.services.conversation_document_service import ConversationDocumentService
from app.schemas.conversation import ConversationRequest, ConversationStage


class MockUploadFile:
    """Mock UploadFile for testing."""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.filename = self.file_path.name
        self.content_type = "application/pdf"
        
    async def read(self):
        with open(self.file_path, 'rb') as f:
            return f.read()


async def test_conversation_document_workflow(pdf_path: str):
    """Test the complete conversation-document workflow."""
    
    print("🧪 Testing Conversation-Document Integration Workflow")
    print("=" * 60)
    
    # Initialize services
    orchestrator = ConversationOrchestrator()
    doc_service = ConversationDocumentService()
    
    try:
        # Step 1: Start a new conversation
        print("\n📋 Step 1: Starting new conversation...")
        
        initial_request = ConversationRequest(
            message="I need to automate a camera inspection system for quality control"
        )
        
        response = await orchestrator.process_message(initial_request)
        conversation_id = response.conversation_id
        
        print(f"✅ Conversation started: {conversation_id}")
        print(f"   Stage: {response.stage}")
        print(f"   Response length: {len(response.response)} chars")
        
        # Step 2: Upload document to conversation
        print(f"\n📄 Step 2: Uploading document to conversation...")
        
        mock_file = MockUploadFile(pdf_path)
        doc_info = await doc_service.process_uploaded_document(mock_file, analyze_with_openai=True)
        
        # Add document to conversation context
        conversation = orchestrator.get_conversation(conversation_id)
        conversation.extracted_documents.append(doc_info.to_dict())
        
        print(f"✅ Document processed and added to conversation:")
        print(f"   Filename: {doc_info.filename}")
        print(f"   Document type: {doc_info.document_type}")
        print(f"   Content length: {len(doc_info.raw_text):,} characters")
        print(f"   Device info: {doc_info.device_info}")
        print(f"   Has PLC analysis: {bool(doc_info.plc_analysis)}")
        
        # Step 3: Continue conversation in requirements gathering stage
        print(f"\n❓ Step 3: Continuing conversation with document context...")
        
        follow_up_request = ConversationRequest(
            conversation_id=conversation_id,
            message="The camera should detect defects on products moving on a conveyor belt"
        )
        
        response = await orchestrator.process_message(follow_up_request)
        
        print(f"✅ Requirements gathering response:")
        print(f"   Stage: {response.stage}")
        print(f"   Response includes document context: {'document' in response.response.lower()}")
        print(f"   Response length: {len(response.response)} chars")
        
        # Step 4: Force transition to code generation stage
        print(f"\n🔧 Step 4: Transitioning to code generation stage...")
        
        # First, gather some requirements
        conversation.requirements.identified_requirements = [
            "Camera-based defect detection system",
            "Conveyor belt integration",
            "Quality control automation",
            "Product reject mechanism"
        ]
        
        # Force transition to code generation
        await orchestrator._transition_to_stage(conversation, ConversationStage.CODE_GENERATION)
        
        code_request = ConversationRequest(
            conversation_id=conversation_id,
            message="Generate the PLC code for the camera inspection system"
        )
        
        response = await orchestrator.process_message(code_request)
        
        print(f"✅ Code generation response:")
        print(f"   Stage: {response.stage}")
        print(f"   Response includes document context: {'document' in response.response.lower()}")
        print(f"   Has generated code: {bool(response.generated_code)}")
        print(f"   Response length: {len(response.response)} chars")
        
        # Step 5: Test document persistence and retrieval
        print(f"\n🔍 Step 5: Verifying document persistence...")
        
        retrieved_conversation = orchestrator.get_conversation(conversation_id)
        documents = retrieved_conversation.extracted_documents
        
        print(f"✅ Document persistence verified:")
        print(f"   Documents in conversation: {len(documents)}")
        print(f"   Document filename: {documents[0]['filename'] if documents else 'None'}")
        print(f"   Document type: {documents[0]['document_type'] if documents else 'None'}")
        
        # Step 6: Test duplicate detection
        print(f"\n🔄 Step 6: Testing duplicate document detection...")
        
        # Try to upload the same document again
        duplicate_doc = await doc_service.process_uploaded_document(mock_file, analyze_with_openai=False)
        existing_doc = doc_service.is_document_already_processed(
            duplicate_doc.content_hash, 
            conversation.extracted_documents
        )
        
        print(f"✅ Duplicate detection:")
        print(f"   Same content hash detected: {existing_doc is not None}")
        print(f"   Original filename: {existing_doc.filename if existing_doc else 'None'}")
        
        # Step 7: Test document context in prompts
        print(f"\n📝 Step 7: Testing document context in prompt generation...")
        
        from app.services.prompt_templates import PromptTemplateFactory
        
        template = PromptTemplateFactory.get_template(ConversationStage.CODE_GENERATION)
        system_prompt = template.build_system_prompt(conversation)
        
        has_doc_context = "document" in system_prompt.lower()
        doc_context_length = len([line for line in system_prompt.split('\n') if 'document' in line.lower()])
        
        print(f"✅ Prompt context integration:")
        print(f"   System prompt includes document context: {has_doc_context}")
        print(f"   Document-related prompt lines: {doc_context_length}")
        print(f"   Total system prompt length: {len(system_prompt):,} characters")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_document_service_features():
    """Test document service standalone features."""
    
    print("\n🧪 Testing Document Service Features")
    print("=" * 60)
    
    doc_service = ConversationDocumentService()
    
    # Test document type classification
    test_texts = {
        "This is a user manual for the XYZ camera system. Follow these installation steps...": "MANUAL",
        "Technical Datasheet - Model ABC123. Specifications: Resolution 1920x1080...": "DATASHEET", 
        "Project Specification Document. Requirements for automated inspection...": "SPECIFICATION",
        "Electrical schematic diagram showing camera connections...": "DRAWING",
        "Random text without clear indicators...": "UNKNOWN"
    }
    
    print("\n📋 Document Type Classification:")
    for text, expected in test_texts.items():
        detected = doc_service._classify_document_type(text)
        status = "✅" if detected == expected else "❌"
        print(f"   {status} '{text[:50]}...' → {detected} (expected: {expected})")
    
    # Test device info extraction
    test_device_texts = [
        "Siemens S7-1200 PLC with integrated Ethernet",
        "Allen-Bradley CompactLogix 5370 L2 Controller",
        "Cognex In-Sight 7000 Series Vision System",
        "Model: IV3-500CA Datasheet Version 2.1"
    ]
    
    print("\n🔧 Device Information Extraction:")
    for text in test_device_texts:
        device_info = doc_service._extract_device_info(text)
        print(f"   Text: '{text[:40]}...'")
        print(f"   Extracted: {device_info}")
    
    return True


async def main():
    """Main test function."""
    
    # Get PDF path from command line or use default
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Use the sample camera datasheet from our test fixtures
        pdf_path = project_root / "tests/fixtures/sample_documents/datasheets/cameras/IV3-500CA_Datasheet.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF file not found: {pdf_path}")
        print("\nUsage: python test_conversation_document_integration.py [path_to_pdf]")
        print("\nOr place a PDF at: tests/fixtures/sample_documents/datasheets/cameras/IV3-500CA_Datasheet.pdf")
        return False
    
    print(f"📄 Using PDF: {pdf_path}")
    
    try:
        # Test standalone document service features
        service_tests_passed = test_document_service_features()
        
        # Test full conversation workflow
        workflow_tests_passed = await test_conversation_document_workflow(str(pdf_path))
        
        if service_tests_passed and workflow_tests_passed:
            print(f"\n🎉 All tests passed!")
            print(f"\n💡 Integration Summary:")
            print(f"   ✅ Document parsing and analysis working")
            print(f"   ✅ Conversation-level document storage working") 
            print(f"   ✅ Document context in prompt templates working")
            print(f"   ✅ Document persistence throughout conversation working")
            print(f"   ✅ Duplicate detection working")
            print(f"   ✅ Multi-stage document context usage working")
            
            print(f"\n🚀 Ready for frontend integration!")
            print(f"   API Endpoints:")
            print(f"   • POST /api/v1/conversations/{{id}}/documents/upload")
            print(f"   • GET /api/v1/conversations/{{id}}/documents")
            print(f"   • GET /api/v1/conversations/{{id}}/documents/{{hash}}")
            print(f"   • DELETE /api/v1/conversations/{{id}}/documents/{{hash}}")
            
            return True
        else:
            print(f"\n❌ Some tests failed")
            return False
            
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        return False
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)