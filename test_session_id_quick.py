#!/usr/bin/env python3
"""
Quick test for frontend-generated session ID functionality.
"""

import requests
import json
import uuid

BASE_URL = "http://localhost:8001"

def test_session_id_frontend_generation():
    """Test that frontend can generate and use session IDs"""
    print("🧪 Testing Frontend-Generated Session ID")
    
    # 1. Generate session_id on frontend (client) side
    session_id = str(uuid.uuid4())
    print(f"\n1️⃣ Generated session_id: {session_id}")
    
    # 2. Test health endpoint first
    print("\n2️⃣ Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/api/v1/context/health")
    if response.status_code != 200:
        print(f"❌ Health check failed: {response.status_code}")
        return False
    print("   ✅ Health check passed")
    
    # 3. Send request with frontend-generated session_id
    print("\n3️⃣ Testing session_id with context update...")
    context_data = {
        "device_constants": {},
        "information": ""
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/context/update",
        data={
            "current_context": json.dumps(context_data),
            "current_stage": "gathering_requirements",
            "message": "Quick test message",
            "session_id": session_id
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Context update failed: {response.status_code} - {response.text}")
        return False
        
    result = response.json()
    returned_session_id = result.get("session_id")
    
    print(f"   ✅ Request successful")
    print(f"   📋 Sent session_id: {session_id}")
    print(f"   📋 Returned session_id: {returned_session_id}")
    
    # 4. Verify session ID matches
    if returned_session_id != session_id:
        print(f"   ❌ Session ID mismatch! Expected: {session_id}, Got: {returned_session_id}")
        return False
    
    print(f"   ✅ Session ID correctly preserved")
    
    # 5. Test session stats to see the session is tracked
    print("\n4️⃣ Checking session stats...")
    response = requests.get(f"{BASE_URL}/api/v1/context/sessions/stats")
    if response.status_code != 200:
        print(f"❌ Stats failed: {response.status_code}")
        return False
        
    stats_response = response.json()
    stats = stats_response['stats']
    print(f"   📊 Active sessions: {stats['active_sessions']}")
    print(f"   📁 Total files tracked: {stats['total_files_tracked']}")
    
    # 6. Test another session ID 
    print("\n5️⃣ Testing with different session ID...")
    session_id_2 = str(uuid.uuid4())
    print(f"   📋 Generated second session_id: {session_id_2}")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/context/update",
        data={
            "current_context": json.dumps(context_data),
            "current_stage": "gathering_requirements",
            "message": "Second session test",
            "session_id": session_id_2
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Second session failed: {response.status_code}")
        return False
        
    result2 = response.json()
    returned_session_id_2 = result2.get("session_id")
    
    if returned_session_id_2 != session_id_2:
        print(f"   ❌ Second session ID mismatch! Expected: {session_id_2}, Got: {returned_session_id_2}")
        return False
    
    print(f"   ✅ Second session ID correctly preserved")
    
    # 7. Check stats again to verify multiple sessions
    response = requests.get(f"{BASE_URL}/api/v1/context/sessions/stats")
    if response.status_code == 200:
        stats_response = response.json()
        stats = stats_response['stats']
        print(f"   📊 Active sessions after 2 requests: {stats['active_sessions']}")
    
    print("\n🎉 Frontend-generated session ID test COMPLETED!")
    return True

if __name__ == "__main__":
    success = test_session_id_frontend_generation()
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tests failed!")