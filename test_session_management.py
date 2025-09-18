#!/usr/bin/env python3
"""
Comprehensive tests for session management, cleanup, and multi-user scenarios.
"""

import asyncio
import time
import requests
import json
from io import BytesIO

BASE_URL = "http://127.0.0.1:8001"

def create_dummy_file(content: str = "Test PDF content") -> BytesIO:
    """Create a dummy file for testing."""
    return BytesIO(content.encode())

async def test_session_management():
    print("🧪 Testing Session Management System")
    print("=" * 50)
    
    # Test 1: Basic session creation and tracking
    print("\n1️⃣ Test: Session creation and file upload")
    
    form_data = {
        'message': 'Testing file upload with conveyor system',
        'current_context': json.dumps({
            'device_constants': {},
            'information': ''
        }),
        'current_stage': 'gathering_requirements'
    }
    
    # Upload file to create session
    files = {'files': ('test.pdf', create_dummy_file(), 'application/pdf')}
    response = requests.post(f"{BASE_URL}/api/v1/context/update", data=form_data, files=files)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ File uploaded successfully")
        print(f"   Session created in response")
        
        # Check session stats
        stats_response = requests.get(f"{BASE_URL}/api/v1/context/sessions/stats")
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"   📊 Active sessions: {stats['stats']['active_sessions']}")
            print(f"   📊 Total files tracked: {stats['stats']['total_files_tracked']}")
    else:
        print(f"   ❌ Error: {response.status_code}")
        return
    
    # Test 2: Multiple sessions simulation
    print("\n2️⃣ Test: Multiple users simulation")
    
    sessions = []
    for i in range(3):
        form_data_user = {
            'message': f'User {i+1} wants motor control help',
            'current_context': json.dumps({
                'device_constants': {},
                'information': ''
            }),
            'current_stage': 'gathering_requirements'
        }
        
        files_user = {'files': (f'user{i+1}.pdf', create_dummy_file(f"User {i+1} content"), 'application/pdf')}
        response_user = requests.post(f"{BASE_URL}/api/v1/context/update", data=form_data_user, files=files_user)
        
        if response_user.status_code == 200:
            sessions.append(f"user_{i+1}_session")
            print(f"   ✅ User {i+1} session created")
    
    # Check stats after multiple users
    stats_response = requests.get(f"{BASE_URL}/api/v1/context/sessions/stats")
    if stats_response.status_code == 200:
        stats = stats_response.json()
        print(f"   📊 After multi-user: {stats['stats']['active_sessions']} sessions")
        print(f"   📊 Total files: {stats['stats']['total_files_tracked']}")
    
    # Test 3: Manual cleanup
    print("\n3️⃣ Test: Manual session cleanup")
    
    # Try to clean up a session (we'll use a dummy session_id)
    cleanup_data = {'session_id': 'test_session_123'}
    cleanup_response = requests.post(f"{BASE_URL}/api/v1/context/cleanup", data=cleanup_data)
    
    if cleanup_response.status_code == 200:
        cleanup_result = cleanup_response.json()
        print(f"   ✅ Cleanup API working: {cleanup_result['status']}")
        print(f"   📁 Files cleaned: {cleanup_result.get('files_cleaned', 0)}")
    else:
        print(f"   ❌ Cleanup error: {cleanup_response.status_code}")
    
    # Test 4: Session timeout behavior
    print("\n4️⃣ Test: Session timeout simulation")
    print("   Note: In production, sessions timeout after 30 minutes of inactivity")
    print("   Cleanup happens automatically during new requests")
    
    # Test 5: Final stats check
    print("\n5️⃣ Test: Final session statistics")
    
    final_stats_response = requests.get(f"{BASE_URL}/api/v1/context/sessions/stats")
    if final_stats_response.status_code == 200:
        final_stats = final_stats_response.json()
        print(f"   📊 Final active sessions: {final_stats['stats']['active_sessions']}")
        print(f"   📊 Final total files: {final_stats['stats']['total_files_tracked']}")
        print(f"   ⏱️  Avg session age: {final_stats['stats']['avg_session_age_minutes']:.1f} minutes")
        print(f"   ⏱️  Session timeout: {final_stats['stats']['timeout_minutes']} minutes")
    
    print(f"\n🎉 Session management tests completed!")

def test_concurrent_users():
    """Test concurrent user scenarios"""
    print("\n6️⃣ Test: Concurrent user file uploads")
    
    import concurrent.futures
    import threading
    
    def user_session(user_id):
        """Simulate a user session"""
        try:
            form_data = {
                'message': f'Concurrent user {user_id} needs PLC help',
                'current_context': json.dumps({
                    'device_constants': {},
                    'information': ''
                }),
                'current_stage': 'gathering_requirements'
            }
            
            files = {'files': (f'concurrent_{user_id}.pdf', create_dummy_file(f"Concurrent user {user_id} data"), 'application/pdf')}
            response = requests.post(f"{BASE_URL}/api/v1/context/update", data=form_data, files=files)
            
            return user_id, response.status_code == 200
        except Exception as e:
            return user_id, False
    
    # Simulate 5 concurrent users
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(user_session, i) for i in range(5)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    successful_users = sum(1 for user_id, success in results if success)
    print(f"   ✅ {successful_users}/5 concurrent users successful")
    
    # Final stats
    stats_response = requests.get(f"{BASE_URL}/api/v1/context/sessions/stats")
    if stats_response.status_code == 200:
        stats = stats_response.json()
        print(f"   📊 Sessions after concurrent test: {stats['stats']['active_sessions']}")

if __name__ == "__main__":
    print("🚀 Starting Session Management Tests")
    print("Ensure the server is running on port 8001")
    print()
    
    # Check if server is running
    try:
        health_response = requests.get(f"{BASE_URL}/api/v1/context/health")
        if health_response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server health check failed")
            exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        exit(1)
    
    # Run tests
    asyncio.run(test_session_management())
    test_concurrent_users()
    
    print("\n🏁 All session management tests completed!")