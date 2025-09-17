#!/usr/bin/env python3
"""
Simple test of the conversation system with model cascade fallback.

This script tests that the conversation system properly falls back
through the model cascade when rate limits are encountered.
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.models import ModelConfig
from app.services.openai_service import OpenAIService

def test_conversation_with_fallback():
    """Test a simple conversation that should trigger fallback."""
    print("🗣️  Testing Conversation with Model Cascade")
    print("=" * 50)
    
    service = OpenAIService()
    
    # Show current cascade
    print(f"🔄 Model cascade: {' → '.join(ModelConfig.FALLBACK_CASCADE)}")
    print(f"📝 Primary conversation model: {ModelConfig.CONVERSATION_MODEL}")
    
    # Test simple chat completion
    print("\n💬 Testing simple chat completion:")
    try:
        response = service._safe_chat_create(
            model=ModelConfig.CONVERSATION_MODEL,
            messages=[
                {"role": "user", "content": "Say 'Hello from cascade test' and nothing else."}
            ],
            max_tokens=10,
            temperature=0
        )
        
        if response and response.choices:
            print(f"✅ Success!")
            print(f"   🤖 Model used: {response.model}")
            print(f"   💬 Response: {response.choices[0].message.content.strip()}")
            if hasattr(response, 'usage') and response.usage:
                print(f"   🔢 Tokens: {response.usage.total_tokens}")
                
            # Check if we used a fallback model
            if response.model != ModelConfig.CONVERSATION_MODEL:
                print(f"   ⚠️  Note: Fell back from {ModelConfig.CONVERSATION_MODEL} to {response.model}")
            else:
                print(f"   ✅ Used primary model as expected")
        else:
            print("❌ No response received")
            
    except Exception as e:
        print(f"❌ Chat completion failed: {e}")
    
    # Show current rate limit status
    print(f"\n📊 Current rate limited models: {sorted(service._rate_limited_models)}")

def main():
    print("🧪 Conversation Cascade Test")
    print("=" * 30)
    
    try:
        test_conversation_with_fallback()
        print("\n🎉 Test completed!")
        
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()