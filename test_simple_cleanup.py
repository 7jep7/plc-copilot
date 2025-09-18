#!/usr/bin/env python3
"""
Simple test of the file upload and cleanup system.
"""

import requests
import json

API_BASE = "http://127.0.0.1:8001/api/v1/context"

def main():
    print("=== Simple Upload and Cleanup Test ===")
    
    # Create a test PDF file
    test_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\nxref\n0 2\ntrailer\n<<\n/Size 2\n/Root 1 0 R\n>>\nstartxref\n%%EOF"
    
    # Test 1: Upload a file using the update endpoint
    print("\n1. Testing file upload via /update endpoint...")
    
    # Prepare form data for context update with file
    form_data = {
        'current_context': '{"project_info": {}, "requirements": [], "constraints": [], "additional_info": ""}',
        'current_stage': 'gathering_requirements',
        'message': 'Here is a test document'
    }
    
    files = {
        'files': ('test_cleanup.pdf', test_content, 'application/pdf')
    }
    
    response = requests.post(f"{API_BASE}/update", data=form_data, files=files)
    print(f"Upload status: {response.status_code}")
    
    if response.status_code == 200:
        upload_data = response.json()
        session_id = upload_data.get('session_id')
        print(f"Session ID: {session_id}")
        
        # Test 2: Check session stats
        print("\n2. Checking session stats...")
        stats_response = requests.get(f"{API_BASE}/sessions/stats")
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"Active sessions: {stats.get('active_sessions', 0)}")
            print(f"Total files tracked: {stats.get('total_files_tracked', 0)}")
        
        # Test 3: Clean up the session
        print(f"\n3. Testing cleanup for session: {session_id}")
        cleanup_data = {'session_id': session_id}
        cleanup_response = requests.post(
            f"{API_BASE}/cleanup",
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data=cleanup_data
        )
        
        print(f"Cleanup status: {cleanup_response.status_code}")
        if cleanup_response.status_code == 200:
            cleanup_result = cleanup_response.json()
            print(f"Files cleaned: {cleanup_result.get('files_cleaned', 0)}")
            print(f"Cleanup message: {cleanup_result.get('message', 'N/A')}")
            print("✅ Cleanup completed successfully!")
        else:
            print(f"❌ Cleanup failed: {cleanup_response.text}")
    else:
        print(f"❌ Upload failed: {response.text}")
    
    # Final session stats
    print("\n4. Final session stats...")
    final_stats_response = requests.get(f"{API_BASE}/sessions/stats")
    if final_stats_response.status_code == 200:
        final_stats = final_stats_response.json()
        print(f"Active sessions: {final_stats.get('active_sessions', 0)}")
        print(f"Total files tracked: {final_stats.get('total_files_tracked', 0)}")

if __name__ == "__main__":
    main()