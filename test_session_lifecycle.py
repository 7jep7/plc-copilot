#!/usr/bin/env python3
"""
Comprehensive test for session lifecycle and file tracking.
"""

import requests
import tempfile
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8001"

def test_complete_session_lifecycle():
    """Test complete file upload and cleanup lifecycle"""
    print("🧪 Testing Complete Session Lifecycle")
    
    # 1. Initial request to get session_id
    print("\n1️⃣ Starting new session...")
    context_data = {
        "device_constants": {},
        "information": ""
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/context/update",
        data={
            "current_context": json.dumps(context_data),
            success = False
            try:
                with open(temp_file_path, 'rb') as f:
                    files = {'files': ('motor_spec.txt', f, 'text/plain')}
                    data = {
                        "current_context": json.dumps(context_data),
                        "current_stage": "gathering_requirements",
                        "message": "Here's my motor specification document"
                    }
                    print(f"❌ Failed to start session: {response.status_code} - {response.text}")
                    return False
                result = response.json()
                session_id = result.get("metadata", {}).get("session_id")
                print(f"   ✅ Session created: {session_id}")
                # 2. Upload a test file
                print("\n2️⃣ Uploading test file...")
                test_content = """
                print(f"   🔍 Motor keywords found: {found_keywords}")
                print("\n5️⃣ Cleaning up session...")
                response = requests.post(
                    f"{BASE_URL}/api/v1/context/cleanup",
                    data={"session_id": session_id}
                )
                if response.status_code != 200:
                    # 1. Start session
                    response = requests.post(
                        f"{BASE_URL}/api/v1/context/update",
                        data={
                            "current_context": json.dumps(context_data),
                            "current_stage": "gathering_requirements",
                            "message": "I want to control a conveyor belt system"
                        }
                    )
                    if response.status_code != 200:
                        print(f"❌ Failed to start session: {response.status_code} - {response.text}")
                        return False
                    result = response.json()
                    session_id = result.get("metadata", {}).get("session_id")
                    print(f"   ✅ Session created: {session_id}")
                    # 2. Upload a test file
                    print("\n2️⃣ Uploading test file...")
                    test_content = """
            print(f"   ✅ Session properly cleaned up (status: {response.status_code})")
        
        print("\n🎉 Complete session lifecycle test COMPLETED!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        try:

                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                        f.write(test_content)
                        temp_file_path = f.name
                    try:
                        with open(temp_file_path, 'rb') as f:
                            files = {'files': ('motor_spec.txt', f, 'text/plain')}
                            data = {
                                "current_context": json.dumps(context_data),
                                "current_stage": "gathering_requirements",
                                "message": "Here's my motor specification document"
                            }
                            response = requests.post(
                                f"{BASE_URL}/api/v1/context/update",
                                files=files,
                                data=data
                            )
                        if response.status_code != 200:
                            print(f"❌ Failed to upload file: {response.status_code} - {response.text}")
                            return False
                        result = response.json()
                        print(f"   ✅ File uploaded successfully")
                        print(f"   📋 Response preview: {result['chat_message'][:150]}...")
                        uploaded_session_id = result.get("metadata", {}).get("session_id")
                        if uploaded_session_id != session_id:
                            print(f"   ⚠️  Session ID changed: {session_id} -> {uploaded_session_id}")
                            session_id = uploaded_session_id
                        # 3. Check session stats
                        print("\n3️⃣ Checking session stats...")
                        response = requests.get(f"{BASE_URL}/api/v1/context/sessions/stats")
                        if response.status_code != 200:
                            print(f"❌ Failed to get stats: {response.status_code}")
                            return False
                        stats = response.json()
                        print(f"   📊 Active sessions: {stats['active_sessions']}")
                        print(f"   📁 Sessions with files: {stats['sessions_with_files']}")
                        # 4. Make another request to verify file is available to assistant
                        print("\n4️⃣ Testing file availability in subsequent request...")
                        response = requests.post(
                            f"{BASE_URL}/api/v1/context/update",
                            data={
                                "current_context": json.dumps(result["updated_context"]),
                                "current_stage": "gathering_requirements", 
                                "message": "What are the motor specifications I uploaded? Please list the key details."
                            }
                        )
                        if response.status_code != 200:
                            print(f"❌ Failed subsequent request: {response.status_code}")
                            return False
                        result2 = response.json()
                        print(f"   ✅ File still accessible")
                        print(f"   📋 Assistant response: {result2['chat_message'][:200]}...")
                        response_text = result2['chat_message'].lower()
                        motor_keywords = ['5.5', 'kw', 'abb', '1450', 'rpm', '400v', 'vfd']
                        found_keywords = [kw for kw in motor_keywords if kw in response_text]
                        print(f"   🔍 Motor keywords found: {found_keywords}")
                        # 5. Clean up session
                        print("\n5️⃣ Cleaning up session...")
                        response = requests.post(
                            f"{BASE_URL}/api/v1/context/cleanup",
                            data={"session_id": session_id}
                        )
                        if response.status_code != 200:
                            print(f"❌ Failed to cleanup: {response.status_code} - {response.text}")
                            return False
                        cleanup_result = response.json()
                        print(f"   ✅ Cleanup result: {cleanup_result}")
                        # 6. Check stats after cleanup
                        print("\n6️⃣ Checking stats after cleanup...")
                        response = requests.get(f"{BASE_URL}/api/v1/context/sessions/stats")
                        if response.status_code == 200:
                            stats_after = response.json()
                            print(f"   📊 Active sessions: {stats_after['active_sessions']}")
                            print(f"   📁 Sessions with files: {stats_after['sessions_with_files']}")
                            session_reduction = stats['active_sessions'] - stats_after['active_sessions']
                            files_reduction = stats['sessions_with_files'] - stats_after['sessions_with_files']
                            print(f"   📉 Sessions reduced by: {session_reduction}")
                            print(f"   📉 File sessions reduced by: {files_reduction}")
                        # 7. Try to use the session after cleanup (should fail gracefully)
                        print("\n7️⃣ Testing session after cleanup...")
                        response = requests.post(
                            f"{BASE_URL}/api/v1/context/update",
                            data={
                                "current_context": json.dumps(result2["updated_context"]),
                                "current_stage": "gathering_requirements", 
                                "message": "Can you still see my motor specifications?"
                            }
                        )
                        if response.status_code == 200:
                            result3 = response.json()
                            print(f"   ⚠️  Session still works after cleanup")
                            print(f"   📋 Response: {result3['chat_message'][:150]}...")
                        else:
                            print(f"   ✅ Session properly cleaned up (status: {response.status_code})")
                        print("\n🎉 Complete session lifecycle test COMPLETED!")
                        success = True
                    except Exception as e:
                        print(f"❌ Test failed with exception: {e}")
                        success = False
                    try:
                        os.unlink(temp_file_path)
                    except Exception:
                        pass
                    return success

if __name__ == "__main__":
    success = test_complete_session_lifecycle()
    import sys
    if success:
        sys.exit(0)
    else:
        sys.exit(1)