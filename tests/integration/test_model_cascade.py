#!/usr/bin/env python3
"""
Test script to verify OpenAI model availability and cascade functionality.

This script:
1. Tests which models are actually available in the current OpenAI account
2. Verifies the cascade fallback logic works correctly
3. Simulates rate limiting scenarios to test all fallback paths
"""

import sys
import os
import asyncio
from datetime import datetime
import json

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.config import settings
from app.core.models import ModelConfig
from app.services.openai_service import OpenAIService
import openai

def test_model_availability():
    """Test which models are actually available in the current OpenAI account."""
    print("🔍 Testing OpenAI Model Availability")
    print("=" * 50)
    
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    available_models = set()
    unavailable_models = set()
    
    # Test each model in our cascade
    for model in ModelConfig.FALLBACK_CASCADE:
        print(f"\n📡 Testing model: {model}")
        try:
            # Try a minimal request to see if the model is available
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5,
                temperature=0
            )
            print(f"✅ {model}: Available")
            available_models.add(model)
            
            # Print some basic info about the response
            if response.choices:
                print(f"   Response: {response.choices[0].message.content.strip()}")
                if hasattr(response, 'usage') and response.usage:
                    print(f"   Usage: {response.usage.total_tokens} tokens")
            
        except openai.BadRequestError as e:
            if "model" in str(e).lower():
                print(f"❌ {model}: Not available - {e}")
                unavailable_models.add(model)
            else:
                print(f"⚠️  {model}: Available but bad request - {e}")
                available_models.add(model)
        except openai.RateLimitError as e:
            print(f"⚠️  {model}: Available but rate limited - {e}")
            available_models.add(model)
        except Exception as e:
            print(f"❓ {model}: Unknown error - {e}")
            unavailable_models.add(model)
    
    print(f"\n📊 Summary:")
    print(f"✅ Available models ({len(available_models)}): {', '.join(sorted(available_models))}")
    print(f"❌ Unavailable models ({len(unavailable_models)}): {', '.join(sorted(unavailable_models))}")
    
    return available_models, unavailable_models

def test_cascade_logic():
    """Test the cascade fallback logic."""
    print("\n🔄 Testing Cascade Logic")
    print("=" * 50)
    
    # Test different starting models
    test_models = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo", "gpt-4"]
    
    for model in test_models:
        cascade = ModelConfig.get_fallback_models(model)
        print(f"\n🎯 Starting with: {model}")
        print(f"   Cascade: {' → '.join(cascade)}")
        
        # Test the backwards compatibility method too
        single_fallback = ModelConfig.get_fallback_model(model)
        print(f"   Single fallback: {single_fallback}")

def test_service_cascade():
    """Test the OpenAI service cascade functionality."""
    print("\n🔧 Testing Service Cascade")
    print("=" * 50)
    
    service = OpenAIService()
    
    # Test normal operation
    print("\n1. Normal operation (no rate limits):")
    best_model = service._get_best_available_model("gpt-4o-mini")
    print(f"   Best model for gpt-4o-mini: {best_model}")
    
    # Simulate rate limiting some models
    print("\n2. Simulating rate limits:")
    service._rate_limited_models.add("gpt-4o-mini")
    best_model = service._get_best_available_model("gpt-4o-mini")
    print(f"   Best model when gpt-4o-mini is rate limited: {best_model}")
    
    # Simulate more rate limits
    service._rate_limited_models.add("gpt-3.5-turbo")
    best_model = service._get_best_available_model("gpt-4o-mini")
    print(f"   Best model when gpt-4o-mini and gpt-3.5-turbo are rate limited: {best_model}")
    
    # Simulate all models rate limited
    for model in ModelConfig.FALLBACK_CASCADE:
        service._rate_limited_models.add(model)
    best_model = service._get_best_available_model("gpt-4o-mini")
    print(f"   Best model when all models are rate limited: {best_model}")
    print(f"   Rate limited models: {sorted(service._rate_limited_models)}")

def test_end_to_end_cascade():
    """Test end-to-end cascade with actual API calls (be careful with rate limits!)."""
    print("\n🚀 Testing End-to-End Cascade (Limited)")
    print("=" * 50)
    
    print("⚠️  This test makes actual API calls. Proceeding carefully...")
    
    service = OpenAIService()
    
    # Test a simple chat completion with cascade
    try:
        response = service._safe_chat_create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'cascade test' in exactly two words."}],
            max_tokens=10,
            temperature=0
        )
        
        if response and response.choices:
            print(f"✅ Cascade test successful")
            print(f"   Model used: {response.model}")
            print(f"   Response: {response.choices[0].message.content.strip()}")
            if hasattr(response, 'usage') and response.usage:
                print(f"   Tokens used: {response.usage.total_tokens}")
        else:
            print(f"❌ No response received")
            
    except Exception as e:
        print(f"❌ Cascade test failed: {e}")

def main():
    """Run all tests."""
    print("🧪 OpenAI Model Cascade Test Suite")
    print("=" * 70)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔑 Using API key: {settings.OPENAI_API_KEY[:8]}...")
    
    try:
        # Test 1: Check which models are available
        available_models, unavailable_models = test_model_availability()
        
        # Test 2: Test cascade logic
        test_cascade_logic()
        
        # Test 3: Test service cascade
        test_service_cascade()
        
        # Test 4: End-to-end test (optional, comment out to avoid API calls)
        user_input = input("\n🤔 Run end-to-end test with real API calls? (y/N): ")
        if user_input.lower().startswith('y'):
            test_end_to_end_cascade()
        else:
            print("⏭️  Skipping end-to-end test")
        
        print(f"\n🎉 All tests completed!")
        print(f"💡 Recommendation: Update FALLBACK_CASCADE to only include available models:")
        if available_models:
            print(f"   FALLBACK_CASCADE = {json.dumps(sorted(available_models), indent=4)}")
        
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()