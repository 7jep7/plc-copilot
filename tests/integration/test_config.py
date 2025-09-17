"""
Test configuration for cost-efficient testing.
Sets environment variables to use cheaper models and reduced token limits.
"""

import os

def setup_test_environment():
    """Configure environment for cost-efficient testing."""
    # Set testing flag to enable cheaper models
    os.environ["TESTING"] = "true"
    os.environ["ENVIRONMENT"] = "testing"
    
    print("🧪 Test environment configured:")
    print("   - Using gpt-4o-mini for all operations")
    print("   - Reduced token limits for cost efficiency")
    print("   - Optimized for minimal API usage")
    print()

def setup_dev_environment():
    """Configure environment for development (still cost-efficient)."""
    os.environ["TESTING"] = "false"
    os.environ["ENVIRONMENT"] = "development"
    
    print("🔧 Development environment configured:")
    print("   - Using gpt-4o-mini for most operations")
    print("   - Standard token limits")
    print()

def setup_production_environment():
    """Configure environment for production (premium models)."""
    os.environ["TESTING"] = "false"
    os.environ["ENVIRONMENT"] = "production"
    
    print("🚀 Production environment configured:")
    print("   - Using gpt-4o for document analysis")
    print("   - Using gpt-4o-mini for conversations")
    print("   - Full token limits")
    print()

if __name__ == "__main__":
    setup_test_environment()