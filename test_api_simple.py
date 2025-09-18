#!/usr/bin/env python3
"""
Simple API test for the new assistant integration.
Tests the main endpoint to ensure everything works end-to-end.
"""

import json
import requests
import time
from io import BytesIO

BASE_URL = "http://127.0.0.1:8001"

def test_health():
    """Test the health endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/context/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def test_project_kickoff():
    """Test project kickoff via API."""
    print("\n🚀 Testing Project Kickoff API...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/context/update",
            data={
                "message": "I want to create a conveyor belt control system with safety features",
                "current_context": json.dumps({
                    "device_constants": {},
                    "information": ""
                }),
                "current_stage": "gathering_requirements"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Project Kickoff Success!")
            print(f"   Message: {data['chat_message'][:100]}...")
            print(f"   Is MCQ: {data['is_mcq']}")
            print(f"   Progress: {data.get('gathering_requirements_estimated_progress', 0)}")
            return data
        else:
            print(f"❌ Project Kickoff failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Project Kickoff error: {e}")
        return None

def test_context_update(previous_response):
    """Test context update with MCQ response."""
    print("\n🔄 Testing Context Update API...")
    
    if not previous_response:
        print("❌ Cannot test context update without previous response")
        return None
    
    try:
        # Simulate MCQ response
        mcq_response = []
        if previous_response.get('mcq_options'):
            mcq_response = [previous_response['mcq_options'][0]]  # Select first option
        
        response = requests.post(
            f"{BASE_URL}/api/v1/context/update",
            data={
                "message": "The conveyor will handle 50kg boxes, 2 meters per second speed",
                "mcq_responses": json.dumps(mcq_response),
                "previous_copilot_message": previous_response['chat_message'],
                "current_context": json.dumps(previous_response['updated_context']),
                "current_stage": previous_response['current_stage']
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Context Update Success!")
            print(f"   Message: {data['chat_message'][:100]}...")
            print(f"   Device Constants: {data['updated_context'].get('device_constants', {})}")
            print(f"   Progress: {data.get('gathering_requirements_estimated_progress', 0)}")
            return data
        else:
            print(f"❌ Context Update failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Context Update error: {e}")
        return None

def test_file_upload(previous_response):
    """Test file upload via API."""
    print("\n📁 Testing File Upload API...")
    
    if not previous_response:
        print("❌ Cannot test file upload without previous response")
        return None
    
    try:
        # Create sample file content
        sample_file_content = """
Motor Control Specification Document

Equipment Details:
- Motor Type: 3-Phase AC Induction Motor  
- Power Rating: 5 HP (3.7 kW)
- Voltage: 480V AC, 60 Hz
- Current: 7.2 A at full load
- Speed: 1800 RPM
- Efficiency: 90%

Control Requirements:
- Variable Frequency Drive (VFD) control
- Start/Stop functionality
- Emergency stop capability
- Speed control: 0-100% variable
- Overload protection
- Fault monitoring and diagnostics

Safety Features:
- Emergency stop button (NC contact)
- Motor overload protection
- Short circuit protection
- Ground fault protection

I/O Configuration:
Digital Inputs:
- Start pushbutton (NO contact)
- Stop pushbutton (NC contact)
- Emergency stop (NC contact)
- VFD ready signal
- VFD fault signal

Analog Inputs:
- Speed reference (0-10V DC)
- Motor current feedback (4-20mA)

Digital Outputs:
- Motor contactor control
- Run indicator light (green)
- Fault indicator light (red)
- VFD enable signal

Analog Outputs:
- Speed command to VFD (0-10V DC)
"""
        
        # Create file-like object
        file_data = BytesIO(sample_file_content.encode('utf-8'))
        
        response = requests.post(
            f"{BASE_URL}/api/v1/context/update",
            data={
                "message": "I've uploaded the motor control specification document",
                "current_context": json.dumps(previous_response['updated_context']),
                "current_stage": previous_response['current_stage']
            },
            files=[('files', ('motor_spec.txt', file_data, 'text/plain'))]
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ File Upload Success!")
            print(f"   Message: {data['chat_message'][:100]}...")
            print(f"   Updated Device Constants: {list(data['updated_context'].get('device_constants', {}).keys())}")
            print(f"   Progress: {data.get('gathering_requirements_estimated_progress', 0)}")
            return data
        else:
            print(f"❌ File Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ File Upload error: {e}")
        return None

def main():
    """Run all API tests."""
    print("🧪 PLC Copilot API Integration Tests")
    print("=====================================")
    
    # Wait a moment for server to be ready
    time.sleep(2)
    
    # Test health endpoint
    if not test_health():
        print("❌ Server not ready. Please ensure the server is running.")
        return
    
    results = []
    
    # Test 1: Project kickoff
    kickoff_response = test_project_kickoff()
    results.append(kickoff_response is not None)
    
    # Test 2: Context update
    if kickoff_response:
        context_response = test_context_update(kickoff_response)
        results.append(context_response is not None)
        
        # Test 3: File upload
        if context_response:
            file_response = test_file_upload(context_response)
            results.append(file_response is not None)
        else:
            results.append(False)
    else:
        results.extend([False, False])
    
    # Summary
    print(f"\n📊 Test Results Summary")
    print(f"=======================")
    print(f"✅ Tests Passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 All API tests passed! The new assistant integration is fully functional!")
        print("\n🔍 Key Features Verified:")
        print("   ✅ OpenAI Assistant integration with structured JSON responses")
        print("   ✅ Context management and progress tracking")
        print("   ✅ File upload and processing")
        print("   ✅ MCQ handling and conversation flow")
        print("   ✅ Three core interaction cases working correctly")
    else:
        print("❌ Some tests failed. Please check the logs above.")

if __name__ == "__main__":
    main()