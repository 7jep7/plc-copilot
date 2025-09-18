#!/usr/bin/env python3
"""
Comprehensive integration test for the PLC Copilot API endpoints.

This script tests the actual FastAPI endpoints to ensure the complete pipeline works:
1. Project kickoff via API
2. Context update via API
3. File upload via API
4. Error handling
"""

import asyncio
import json
import sys
import requests
import tempfile
from pathlib import Path
from io import BytesIO

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.main import app
from app.schemas.context import Stage
import uvicorn
import threading
import time

BASE_URL = "http://localhost:8000"


def start_test_server():
    """Start the FastAPI server in a separate thread."""
    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(3)  # Wait for server to start
    return server_thread


def test_api_project_kickoff():
    """Test project kickoff via API."""
    print("Testing API - Project Kickoff...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/context/update",
            data={
                "message": "I want to create a conveyor belt control system",
                "current_context": json.dumps({
                    "device_constants": {},
                    "information": ""
                }),
                "current_stage": Stage.GATHERING_REQUIREMENTS.value
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Project Kickoff: {data['chat_message'][:100]}...")
            print(f"   Progress: {data.get('gathering_requirements_estimated_progress', 0)}")
            return data
        else:
            print(f"❌ API Project Kickoff failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ API Project Kickoff error: {e}")
        return None


def test_api_context_update(previous_response):
    """Test context update via API."""
    print("\nTesting API - Context Update...")
    
    if not previous_response:
        print("❌ Cannot test context update without previous response")
        return None
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/context/update",
            data={
                "message": "I want a 3-phase motor, 5HP, with VFD control",
                "mcq_responses": json.dumps(["Emergency stop (E-stop) button(s)"]),
                "previous_copilot_message": previous_response['chat_message'],
                "current_context": json.dumps(previous_response['updated_context']),
                "current_stage": previous_response['current_stage']
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Context Update: {data['chat_message'][:100]}...")
            print(f"   Device Constants: {data['updated_context'].get('device_constants', {})}")
            print(f"   Progress: {data.get('gathering_requirements_estimated_progress', 0)}")
            return data
        else:
            print(f"❌ API Context Update failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ API Context Update error: {e}")
        return None


def test_api_file_upload(previous_response):
    """Test file upload via API."""
    print("\nTesting API - File Upload...")
    
    if not previous_response:
        print("❌ Cannot test file upload without previous response")
        return None
    
    try:
        # Create a sample file
        sample_content = """
        Motor Control Specification
        
        Motor: 3-Phase Induction Motor
        Power: 5 HP (3.7 kW)
        Voltage: 480V AC
        Current: 7.2 A
        Speed: 1800 RPM
        
        VFD Requirements:
        - Variable speed control (0-100%)
        - Start/Stop functionality
        - Emergency stop capability
        - Speed feedback
        - Fault monitoring
        
        I/O Requirements:
        Inputs:
        - Start button (NO)
        - Stop button (NC)
        - E-stop (NC)
        - Speed reference (0-10V)
        
        Outputs:
        - Motor contactor
        - Run indicator
        - Fault indicator
        """
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(sample_content)
            tmp_file.flush()
            
            # Upload file via API
            with open(tmp_file.name, 'rb') as f:
                response = requests.post(
                    f"{BASE_URL}/api/v1/context/update",
                    data={
                        "message": "I've uploaded the motor specification document",
                        "current_context": json.dumps(previous_response['updated_context']),
                        "current_stage": previous_response['current_stage']
                    },
                    files=[('files', ('motor_spec.txt', f, 'text/plain'))]
                )
        
        # Clean up
        Path(tmp_file.name).unlink()
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API File Upload: {data['chat_message'][:100]}...")
            print(f"   Updated Device Constants: {data['updated_context'].get('device_constants', {})}")
            print(f"   Progress: {data.get('gathering_requirements_estimated_progress', 0)}")
            return data
        else:
            print(f"❌ API File Upload failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ API File Upload error: {e}")
        return None


def test_api_error_handling():
    """Test error handling via API."""
    print("\nTesting API - Error Handling...")
    
    try:
        # Test with invalid JSON
        response = requests.post(
            f"{BASE_URL}/api/v1/context/update",
            data={
                "message": "Test message",
                "current_context": "invalid json",
                "current_stage": Stage.GATHERING_REQUIREMENTS.value
            }
        )
        
        if response.status_code == 422:  # Validation error expected
            print("✅ API Error Handling: Correctly returned validation error")
            return True
        else:
            print(f"❌ API Error Handling: Expected 422, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API Error Handling error: {e}")
        return False


async def main():
    """Run comprehensive API tests."""
    print("🚀 Starting Comprehensive PLC Copilot API Tests\n")
    
    # Check if server is already running
    try:
        response = requests.get(f"{BASE_URL}/api/v1/context/health")
        if response.status_code != 200:
            print("Starting test server...")
            start_test_server()
    except:
        print("Starting test server...")
        start_test_server()
    
    # Wait a bit more for server to be ready
    time.sleep(2)
    
    # Verify server is running
    try:
        response = requests.get(f"{BASE_URL}/api/v1/context/health")
        if response.status_code == 200:
            print("✅ Test server is running")
        else:
            print("❌ Test server not responding")
            return
    except Exception as e:
        print(f"❌ Cannot connect to test server: {e}")
        return
    
    # Run tests
    results = []
    
    # Test 1: Project kickoff
    kickoff_response = test_api_project_kickoff()
    results.append(kickoff_response is not None)
    
    # Test 2: Context update
    if kickoff_response:
        context_response = test_api_context_update(kickoff_response)
        results.append(context_response is not None)
        
        # Test 3: File upload
        if context_response:
            file_response = test_api_file_upload(context_response)
            results.append(file_response is not None)
        else:
            results.append(False)
    else:
        results.extend([False, False])
    
    # Test 4: Error handling
    error_result = test_api_error_handling()
    results.append(error_result)
    
    print(f"\n📊 API Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All API tests passed! The new assistant integration is fully functional.")
    else:
        print("❌ Some API tests failed. Please check the implementation.")


if __name__ == "__main__":
    asyncio.run(main())