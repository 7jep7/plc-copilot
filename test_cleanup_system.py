#!/usr/bin/env python3
"""
Test the file upload and cleanup system end-to-end.
"""

import requests
import json
import time
import os
from openai import OpenAI

API_BASE = "http://127.0.0.1:8001/api/v1/context"

def check_openai_files():
    """Check how many files are in OpenAI storage."""
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        all_files = client.files.list()
        return len(all_files.data)
    except Exception as e:
        print(f"Error checking OpenAI files: {e}")
        return -1

def main():
    print("=== File Upload and Cleanup Test ===")
    
    # Check initial file count
    initial_count = check_openai_files()
    print(f"Initial OpenAI files: {initial_count}")
    
    # Create a test PDF file
    test_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n178\n%%EOF"
    
    # Test 1: Upload a file
    print("\n1. Testing file upload...")
    files = {
        'files': ('test_cleanup.pdf', test_content, 'application/pdf')
    }
    
    response = requests.post(f"{API_BASE}/upload", files=files)
    print(f"Upload status: {response.status_code}")
    
    if response.status_code == 200:
        upload_data = response.json()
        session_id = upload_data.get('session_id')
        print(f"Session ID: {session_id}")
        print(f"Files uploaded: {upload_data.get('files_uploaded', 0)}")
        
        # Check file count after upload
        after_upload_count = check_openai_files()
        print(f"OpenAI files after upload: {after_upload_count}")
        
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
            print(f"Cleanup result: {cleanup_result}")
            
            # Check file count after cleanup
            time.sleep(2)  # Give time for deletion to process
            after_cleanup_count = check_openai_files()
            print(f"OpenAI files after cleanup: {after_cleanup_count}")
            
            # Verify cleanup worked
            if after_cleanup_count == initial_count:
                print("✅ SUCCESS: File was properly cleaned up!")
            else:
                print(f"❌ ISSUE: Expected {initial_count} files, got {after_cleanup_count}")
        else:
            print(f"Cleanup failed: {cleanup_response.text}")
    else:
        print(f"Upload failed: {response.text}")
    
    # Final session stats
    print("\n4. Final session stats...")
    final_stats_response = requests.get(f"{API_BASE}/sessions/stats")
    if final_stats_response.status_code == 200:
        final_stats = final_stats_response.json()
        print(f"Active sessions: {final_stats.get('active_sessions', 0)}")
        print(f"Total files tracked: {final_stats.get('total_files_tracked', 0)}")

if __name__ == "__main__":
    main()