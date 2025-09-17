#!/usr/bin/env python3
"""
Comprehensive test suite for the context endpoint to catch errors early.
Tests various scenarios including edge cases and error conditions.
"""

import json
import sys
import tempfile
import traceback
from io import BytesIO
from fastapi.testclient import TestClient

# Import the FastAPI app
try:
    from app.main import app
except ImportError as e:
    print(f"❌ Failed to import app: {e}")
    sys.exit(1)

client = TestClient(app)

def create_test_pdf():
    """Create a simple test PDF file for upload testing."""
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test Motor Specs) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000205 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
297
%%EOF"""
    return pdf_content

def test_basic_context_update():
    """Test basic context update functionality."""
    print("🧪 Testing basic context update...")
    
    context_data = {
        'device_constants': {},
        'information': ''
    }
    
    response = client.post(
        '/api/v1/context/update',
        data={
            'message': 'I need help with a conveyor system',
            'current_context': json.dumps(context_data),
            'current_stage': 'gathering_requirements'
        }
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    result = response.json()
    
    # Check required fields
    required_fields = ['updated_context', 'chat_message', 'current_stage', 'is_mcq']
    for field in required_fields:
        assert field in result, f"Missing required field: {field}"
    
    assert result['current_stage'] == 'gathering_requirements'
    assert isinstance(result['updated_context'], dict)
    assert isinstance(result['chat_message'], str)
    assert isinstance(result['is_mcq'], bool)
    
    print("✅ Basic context update works")
    return result

def test_file_upload():
    """Test file upload functionality."""
    print("🧪 Testing file upload...")
    
    context_data = {
        'device_constants': {},
        'information': ''
    }
    
    # Create test PDF
    pdf_content = create_test_pdf()
    
    files = {'files': ('test_motor.pdf', BytesIO(pdf_content), 'application/pdf')}
    data = {
        'message': 'Please analyze this motor specification',
        'current_context': json.dumps(context_data),
        'current_stage': 'gathering_requirements'
    }
    
    response = client.post('/api/v1/context/update', data=data, files=files)
    
    assert response.status_code == 200, f"File upload failed: {response.status_code}: {response.text}"
    result = response.json()
    
    # Should have updated context with file info
    assert 'updated_context' in result
    assert isinstance(result['updated_context'], dict)
    
    print("✅ File upload works")
    return result

def test_mcq_responses():
    """Test MCQ response handling."""
    print("🧪 Testing MCQ responses...")
    
    context_data = {
        'device_constants': {
            'conveyor': {
                'speed': '2.5 m/s',
                'width': '600mm'
            }
        },
        'information': 'Basic conveyor system requirements'
    }
    
    response = client.post(
        '/api/v1/context/update',
        data={
            'mcq_responses': json.dumps(['Emergency stop buttons only', 'Light curtains']),
            'current_context': json.dumps(context_data),
            'current_stage': 'gathering_requirements'
        }
    )
    
    assert response.status_code == 200, f"MCQ response failed: {response.status_code}: {response.text}"
    result = response.json()
    
    assert 'updated_context' in result
    print("✅ MCQ responses work")
    return result

def test_stage_transitions():
    """Test different stage transitions."""
    print("🧪 Testing stage transitions...")
    
    stages = ['gathering_requirements', 'code_generation', 'refinement_testing']
    
    for stage in stages:
        print(f"   Testing stage: {stage}")
        context_data = {
            'device_constants': {
                'motor': {'power': '5kW', 'voltage': '400V'},
                'sensors': {'type': 'proximity', 'range': '10mm'}
            },
            'information': 'Complete motor control system requirements'
        }
        
        response = client.post(
            '/api/v1/context/update',
            data={
                'message': f'Test message for {stage}',
                'current_context': json.dumps(context_data),
                'current_stage': stage
            }
        )
        
        assert response.status_code == 200, f"Stage {stage} failed: {response.status_code}: {response.text}"
        result = response.json()
        # Allow stage to be maintained or advanced by AI logic
        assert result['current_stage'] in ['gathering_requirements', 'code_generation', 'refinement_testing']
    
    print("✅ All stage transitions work")

def test_error_conditions():
    """Test various error conditions."""
    print("🧪 Testing error conditions...")
    
    # Test missing required fields
    print("   Testing missing current_context...")
    response = client.post(
        '/api/v1/context/update',
        data={
            'message': 'Test message',
            'current_stage': 'gathering_requirements'
            # Missing current_context
        }
    )
    assert response.status_code == 422, f"Expected 422 for missing context, got {response.status_code}"
    
    # Test invalid stage
    print("   Testing invalid stage...")
    response = client.post(
        '/api/v1/context/update',
        data={
            'message': 'Test message',
            'current_context': json.dumps({'device_constants': {}, 'information': ''}),
            'current_stage': 'invalid_stage'
        }
    )
    assert response.status_code == 422, f"Expected 422 for invalid stage, got {response.status_code}"
    
    # Test malformed JSON context
    print("   Testing malformed JSON context...")
    response = client.post(
        '/api/v1/context/update',
        data={
            'message': 'Test message',
            'current_context': '{"invalid": json}',  # Malformed JSON
            'current_stage': 'gathering_requirements'
        }
    )
    assert response.status_code in [400, 422], f"Expected 400 or 422 for malformed JSON, got {response.status_code}"
    
    print("✅ Error conditions handled correctly")

def test_empty_requests():
    """Test edge cases with empty/minimal requests."""
    print("🧪 Testing empty/minimal requests...")
    
    # Test with minimal required fields only
    response = client.post(
        '/api/v1/context/update',
        data={
            'current_context': json.dumps({'device_constants': {}, 'information': ''}),
            'current_stage': 'gathering_requirements'
            # No message, no files, no MCQ responses
        }
    )
    
    assert response.status_code == 200, f"Minimal request failed: {response.status_code}: {response.text}"
    result = response.json()
    assert 'updated_context' in result
    assert 'chat_message' in result
    
    print("✅ Minimal requests work")

def test_large_context():
    """Test with larger context data."""
    print("🧪 Testing large context...")
    
    # Create a large context with many devices
    large_context = {
        'device_constants': {},
        'information': 'Large industrial automation system\n' * 100  # Large text
    }
    
    # Add many devices
    for i in range(20):
        large_context['device_constants'][f'device_{i}'] = {
            'type': f'Type_{i}',
            'model': f'Model_{i}',
            'specs': {f'param_{j}': f'value_{j}' for j in range(10)}
        }
    
    response = client.post(
        '/api/v1/context/update',
        data={
            'message': 'Process this large context',
            'current_context': json.dumps(large_context),
            'current_stage': 'gathering_requirements'
        }
    )
    
    assert response.status_code == 200, f"Large context failed: {response.status_code}: {response.text}"
    result = response.json()
    assert 'updated_context' in result
    
    print("✅ Large context handled correctly")

def test_ai_chat_endpoint():
    """Test the AI chat endpoint as well."""
    print("🧪 Testing AI chat endpoint...")
    
    response = client.post(
        '/api/v1/ai/chat',
        json={
            'user_prompt': 'What is a PID controller?',
            'context': {
                'device_constants': {},
                'information': ''
            }
        }
    )
    
    assert response.status_code == 200, f"AI chat failed: {response.status_code}: {response.text}"
    result = response.json()
    assert 'content' in result
    assert isinstance(result['content'], str)
    
    print("✅ AI chat endpoint works")

def test_health_endpoint():
    """Test health endpoint."""
    print("🧪 Testing health endpoint...")
    
    response = client.get('/health')
    assert response.status_code == 200, f"Health check failed: {response.status_code}"
    result = response.json()
    assert result['status'] == 'healthy'
    
    print("✅ Health endpoint works")

def run_all_tests():
    """Run all tests and report results."""
    print("🚀 Starting comprehensive context endpoint tests...")
    print("=" * 60)
    
    tests = [
        test_health_endpoint,
        test_basic_context_update,
        test_file_upload,
        test_mcq_responses,
        test_stage_transitions,
        test_empty_requests,
        test_large_context,
        test_error_conditions,
        test_ai_chat_endpoint,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} FAILED: {e}")
            print(f"   Traceback: {traceback.format_exc()}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! The context endpoint is robust and ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)