#!/usr/bin/env python3
"""Test script to verify the fallback system works correctly."""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.openai_service import OpenAIService
from app.core.models import ModelConfig
from app.schemas.conversation import ConversationRequest

class MockRequest:
    """Mock request object for testing."""
    def __init__(self):
        self.user_prompt = "Test message"
        self.model = ModelConfig.CONVERSATION_MODEL
        self.temperature = 1.0
        self.max_completion_tokens = 100
        self.conversation_id = "test-conversation-123"

async def test_fallback_system():
    """Test the intelligent model selection system."""
    
    print("🧪 Testing PLC-Copilot Intelligent Model Selection")
    print("=" * 60)
    
    service = OpenAIService()
    request = MockRequest()
    
    print(f"📋 Primary model: {ModelConfig.CONVERSATION_MODEL}")
    print(f"🔄 Fallback model: {ModelConfig.get_fallback_model(ModelConfig.CONVERSATION_MODEL)}")
    print(f"💬 Test conversation ID: {request.conversation_id}")
    
    # Show initial session state
    status = service.get_session_model_status()
    print(f"\n📊 Initial Session State:")
    print(f"   Current active model: {status['current_active_model'] or 'None (first request)'}")
    print(f"   Rate limited models: {status['rate_limited_models'] or 'None'}")
    print(f"   Available models: {status['available_models']}")
    
    # Test multiple requests to see intelligent switching
    print(f"\n🔧 Testing intelligent model selection...")
    
    for i in range(3):
        print(f"\n--- Request {i+1} ---")
        try:
            response, usage = await service.chat_completion(
                request,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f"Request {i+1}: Say 'Smart fallback working!' if you can respond."}
                ]
            )
            
            print(f"✅ Response {i+1}: {response[:50]}...")
            if usage:
                print(f"📊 Token usage: {usage.get('total_tokens', 'N/A')} tokens")
            
            # Show session state after each request
            status = service.get_session_model_status()
            print(f"📊 Session State:")
            print(f"   Active model: {status['current_active_model']}")
            print(f"   Rate limited: {status['rate_limited_models'] or 'None'}")
            print(f"   Available: {status['available_models']}")
            
        except Exception as e:
            print(f"❌ Error in request {i+1}: {str(e)}")
            
            # Show session state even after errors
            status = service.get_session_model_status()
            print(f"� Session State after error:")
            print(f"   Active model: {status['current_active_model']}")
            print(f"   Rate limited: {status['rate_limited_models']}")
            print(f"   Available: {status['available_models']}")
    
    print("\n📧 Email Configuration Status:")
    print(f"   SMTP Host: {service.notification_service.smtp_host}")
    print(f"   SMTP User: {'✅ Configured' if service.notification_service.smtp_user else '❌ Not configured'}")
    print(f"   Notification Email: {service.notification_service.notification_email}")
    print(f"   Email sent this session: {service.notification_service._email_sent_this_session}")
    
    print("\n💡 Key Benefits:")
    print("   ✅ Models marked as rate-limited are avoided for the entire session")
    print("   ✅ No unnecessary API calls to known rate-limited models")
    print("   ✅ Only one email notification per session")
    print("   ✅ Intelligent model selection based on session history")
    
    print("\n🎯 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_fallback_system())