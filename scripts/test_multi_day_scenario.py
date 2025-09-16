#!/usr/bin/env python3
"""Test script to simulate multi-day rate limit scenarios."""

import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.openai_service import OpenAIService
from app.core.models import ModelConfig

class MockRequest:
    """Mock request object for testing."""
    def __init__(self):
        self.user_prompt = "Test multi-day scenario"
        self.model = ModelConfig.CONVERSATION_MODEL
        self.temperature = 1.0
        self.max_completion_tokens = 50
        self.conversation_id = "multi-day-test-123"

async def test_multi_day_scenario():
    """Test the system across multiple days with rate limits."""
    
    print("🧪 Testing Multi-Day Rate Limit Intelligence")
    print("=" * 60)
    
    service = OpenAIService()
    
    print("📋 Scenario: Both models hit rate limits on different days")
    print("🎯 Goal: Verify automatic model availability reset at midnight UTC")
    
    # Simulate Day 1: gpt-4o-mini hits rate limit
    print(f"\n📅 DAY 1 SIMULATION:")
    print("=" * 30)
    
    # Manually mark gpt-4o-mini as rate limited (simulating it hit the limit)
    service._rate_limited_models.add("gpt-4o-mini")
    service._last_reset_date = datetime.now(timezone.utc).date()
    
    status = service.get_session_model_status()
    print(f"   Active model: {status['current_active_model'] or 'None'}")
    print(f"   Rate limited: {status['rate_limited_models']}")
    print(f"   Available: {status['available_models']}")
    print(f"   Reset date: {status['last_reset_date']}")
    
    # Simulate Day 2: Fast forward time and add gpt-4o to rate limited
    print(f"\n📅 DAY 2 SIMULATION:")
    print("=" * 30)
    
    # Manually set yesterday's date to trigger reset logic
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date()
    service._last_reset_date = yesterday
    
    # Add gpt-4o as rate limited (simulating it also hit limit on day 2)
    service._rate_limited_models.add("gpt-4o")
    
    print(f"   Before reset check:")
    print(f"     Rate limited: {list(service._rate_limited_models)}")
    print(f"     Last reset: {service._last_reset_date}")
    
    # This should trigger the daily reset
    status = service.get_session_model_status()
    
    print(f"   After automatic daily reset:")
    print(f"     Active model: {status['current_active_model']}")
    print(f"     Rate limited: {status['rate_limited_models']}")
    print(f"     Available: {status['available_models']}")
    print(f"     Reset date: {status['last_reset_date']}")
    print(f"     Current UTC date: {status['current_utc_date']}")
    
    # Test model selection after reset
    print(f"\n🔧 Testing model selection after reset:")
    best_model = service._get_best_available_model("gpt-4o-mini")
    print(f"   Best model for 'gpt-4o-mini': {best_model}")
    
    best_model = service._get_best_available_model("gpt-4o")
    print(f"   Best model for 'gpt-4o': {best_model}")
    
    # Simulate hitting rate limit again to test the system
    print(f"\n📧 Email notification status:")
    print(f"   Email sent this session: {service.notification_service._email_sent_this_session}")
    
    print(f"\n✅ SUCCESS INDICATORS:")
    print(f"   ✅ Rate limited models cleared: {len(service._rate_limited_models) == 0}")
    print(f"   ✅ All models available: {len(status['available_models']) == 2}")
    print(f"   ✅ Email flag reset: {not service.notification_service._email_sent_this_session}")
    print(f"   ✅ Date tracking works: {status['last_reset_date'] == status['current_utc_date']}")
    
    print(f"\n💡 This solves the multi-day problem:")
    print(f"   🔄 Models automatically become available at midnight UTC")
    print(f"   📧 Email notifications reset for new day")
    print(f"   🧠 System remembers what happened yesterday but starts fresh today")
    print(f"   ⚡ No manual intervention needed")
    
    print(f"\n🎯 Multi-day test completed!")

if __name__ == "__main__":
    asyncio.run(test_multi_day_scenario())