#!/usr/bin/env python3
"""Test script to simulate rate limit scenarios for fallback testing."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.openai_service import OpenAIService, OpenAIParameterError
from app.core.models import ModelConfig

class MockRateLimitRequest:
    """Mock request to simulate rate limit testing."""
    def __init__(self):
        self.user_prompt = "Test rate limit fallback"
        self.model = ModelConfig.CONVERSATION_MODEL
        self.temperature = 1.0
        self.max_completion_tokens = 50
        self.conversation_id = "rate-limit-test-123"

async def test_rate_limit_simulation():
    """Test rate limit detection and email notification."""
    print("🧪 Testing Rate Limit Detection Logic")
    print("=" * 50)
    
    service = OpenAIService()
    
    # Test the rate limit detection function
    test_errors = [
        "Error code: 429 - Rate limit reached for gpt-4o-mini",
        "429 Too Many Requests",
        "quota exceeded for this model",
        "requests per day limit exceeded",
        "Random other error",
        "Connection timeout"
    ]
    
    print("🔍 Testing rate limit error detection:")
    for error in test_errors:
        is_rate_limit = service._is_rate_limit_error(error)
        status = "✅ DETECTED" if is_rate_limit else "❌ IGNORED"
        print(f"   {status}: {error[:50]}...")
    
    # Test fallback model selection
    print(f"\n🔄 Testing fallback model mapping:")
    models = ["gpt-4o-mini", "gpt-4o", "unknown-model"]
    for model in models:
        fallback = ModelConfig.get_fallback_model(model)
        print(f"   {model} → {fallback}")
    
    # Test email notification (won't actually send without SMTP config)
    print(f"\n📧 Testing email notification system:")
    success = service.notification_service.send_rate_limit_alert(
        primary_model="gpt-4o-mini",
        fallback_model="gpt-4o", 
        error_message="Test rate limit error for notification testing",
        conversation_id="test-conversation-456"
    )
    
    status = "✅ SENT" if success else "⚠️  SKIPPED (SMTP not configured)"
    print(f"   Email notification: {status}")
    
    print("\n🎯 Rate limit simulation test completed!")

if __name__ == "__main__":
    asyncio.run(test_rate_limit_simulation())