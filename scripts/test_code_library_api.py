#!/usr/bin/env python3
"""
Test script for Code Library API endpoints
Demonstrates how users can interact with the ST code library
"""

import asyncio
import aiohttp
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1/library"

async def test_code_library_api():
    """Test the Code Library API endpoints."""
    
    async with aiohttp.ClientSession() as session:
        
        print("🔍 Testing Code Library API Endpoints\n")
        
        # 1. Get library summary
        print("1. Getting library summary...")
        async with session.get(f"{BASE_URL}/") as response:
            if response.status == 200:
                summary = await response.json()
                print(f"   ✅ Total files: {summary['total_files']}")
                print(f"   ✅ Total domains: {summary['total_domains']}")
                for domain in summary['domains']:
                    print(f"   📁 {domain['name']}: {domain['file_count']} files")
            else:
                print(f"   ❌ Failed: {response.status}")
        
        print()
        
        # 2. Browse a specific domain
        print("2. Browsing motor_control domain...")
        async with session.get(f"{BASE_URL}/browse/motor_control") as response:
            if response.status == 200:
                domain_data = await response.json()
                print(f"   ✅ Domain: {domain_data['domain']}")
                print(f"   ✅ Description: {domain_data['description']}")
                print(f"   ✅ Files found: {len(domain_data['files'])}")
                for file_info in domain_data['files']:
                    print(f"      📄 {file_info['name']} ({file_info['size_bytes']} bytes)")
            else:
                print(f"   ❌ Failed: {response.status}")
        
        print()
        
        # 3. Get file content
        print("3. Getting content of VFD motor control file...")
        async with session.get(f"{BASE_URL}/file/motor_control/vfd_motor_control_system.st") as response:
            if response.status == 200:
                file_content = await response.json()
                print(f"   ✅ File: {file_content['name']}")
                print(f"   ✅ Author: {file_content.get('author', 'Unknown')}")
                print(f"   ✅ Description: {file_content.get('description', 'No description')}")
                print(f"   ✅ Source code length: {len(file_content['source_code'])} characters")
                print(f"   ✅ Features: {', '.join(file_content.get('features', []))}")
            else:
                print(f"   ❌ Failed: {response.status}")
        
        print()
        
        # 4. Search the library
        print("4. Searching for 'motor' in the library...")
        search_data = {
            "query": "motor",
            "limit": 5
        }
        async with session.post(f"{BASE_URL}/search", json=search_data) as response:
            if response.status == 200:
                search_results = await response.json()
                print(f"   ✅ Found {search_results['total_count']} results")
                for file_info in search_results['files']:
                    print(f"      🔍 {file_info['name']} in {file_info['domain']}")
            else:
                print(f"   ❌ Failed: {response.status}")
        
        print()
        
        # 5. Upload a custom ST file
        print("5. Uploading a custom ST file...")
        custom_st_code = """(*
====================================================================
PROGRAM: CustomTestProgram  
Description: User-contributed test program for API demonstration
Author: API Test User
Version: 1.0
Date: 2024-09-15
Features: - Basic motor start/stop
          - Simple alarm handling
          - HMI interface
Application: Test and demonstration
====================================================================
*)

PROGRAM CustomTestProgram
VAR
    bMotorStart    : BOOL;
    bMotorStop     : BOOL;
    bMotorRunning  : BOOL;
    bAlarmActive   : BOOL;
    rMotorSpeed    : REAL;
END_VAR

// Simple motor control logic
IF bMotorStart AND NOT bAlarmActive THEN
    bMotorRunning := TRUE;
END_IF

IF bMotorStop OR bAlarmActive THEN
    bMotorRunning := FALSE;
END_IF

// Speed control
IF bMotorRunning THEN
    rMotorSpeed := 1500.0;  // RPM
ELSE
    rMotorSpeed := 0.0;
END_IF

END_PROGRAM"""

        upload_data = {
            "filename": "custom_test_program.st",
            "content": custom_st_code,
            "domain": "user_examples", 
            "description": "Custom test program uploaded via API",
            "author": "API Test User",
            "tags": ["test", "demo", "motor-control"]
        }
        
        async with session.post(f"{BASE_URL}/upload", json=upload_data) as response:
            if response.status == 200:
                upload_result = await response.json()
                print(f"   ✅ Upload successful: {upload_result['message']}")
                print(f"   ✅ File path: {upload_result['file_info']['path']}")
            else:
                error_text = await response.text()
                print(f"   ❌ Upload failed: {response.status} - {error_text}")
        
        print()
        
        # 6. Find similar files
        print("6. Finding files similar to vfd_motor_control_system.st...")
        similar_data = {
            "reference_file": "vfd_motor_control_system.st",
            "limit": 3
        }
        async with session.post(f"{BASE_URL}/similar", json=similar_data) as response:
            if response.status == 200:
                similar_results = await response.json()
                print(f"   ✅ Reference: {similar_results['reference_file']}")
                print(f"   ✅ Similar files found: {len(similar_results['similar_files'])}")
                for file_info in similar_results['similar_files']:
                    print(f"      🔗 {file_info['name']} (similarity: {file_info.get('similarity_score', 'N/A')})")
            else:
                print(f"   ❌ Failed: {response.status}")
        
        print()
        
        # 7. List all domains
        print("7. Listing all available domains...")
        async with session.get(f"{BASE_URL}/domains") as response:
            if response.status == 200:
                domains_data = await response.json()
                print(f"   ✅ Available domains:")
                for domain in domains_data['domains']:
                    print(f"      📁 {domain['name']}: {domain['description']} ({domain['file_count']} files)")
            else:
                print(f"   ❌ Failed: {response.status}")
        
        print()
        
        # 8. Get user uploads
        print("8. Getting user-uploaded files...")
        async with session.get(f"{BASE_URL}/user-uploads") as response:
            if response.status == 200:
                uploads_data = await response.json()
                print(f"   ✅ User uploads found: {len(uploads_data['uploads'])}")
                for upload in uploads_data['uploads']:
                    print(f"      📤 {upload['name']} in {upload['domain']}")
            else:
                print(f"   ❌ Failed: {response.status}")


async def demonstrate_user_workflow():
    """Demonstrate a typical user workflow with the API."""
    
    print("\n" + "="*60)
    print("🚀 DEMONSTRATION: How Users Can Add Their Own ST Files")
    print("="*60)
    
    print("""
This API provides several ways for users to add their own ST code files:

1. 📤 **Upload via JSON API** (/api/v1/library/upload)
   - Send filename, content, domain, description, author, tags
   - Perfect for programmatic uploads or web interfaces

2. 📎 **Upload via File Upload** (/api/v1/library/upload-file)  
   - Standard multipart form upload
   - Drag & drop file uploads from web browsers

3. 📁 **Direct File System** (user_uploads/ directory)
   - Place .st files directly in user_uploads/st_code/[domain]/
   - Files are automatically discovered and indexed

4. 🔍 **Easy Discovery**
   - Browse by domain (/api/v1/library/browse/{domain})
   - Search across all files (/api/v1/library/search)
   - Find similar files (/api/v1/library/similar)

5. 📊 **Management Features**
   - List all user uploads (/api/v1/library/user-uploads)
   - Delete unwanted files (/api/v1/library/user-uploads/{domain}/{file})
   - Get library statistics (/api/v1/library/)

**Example Usage Scenarios:**

🏭 **Company Code Repository:**
   Companies can upload their entire ST code library and make it searchable
   for all engineers. The API supports batch uploads and organization by 
   domains (motor_control, safety_systems, process_control, etc.).

👨‍💻 **Individual Engineer:**
   Engineers can upload their personal ST code snippets and templates,
   making them available for reuse across projects. The search function
   helps find relevant code quickly.

🎓 **Training & Education:**
   Educational institutions can build libraries of example code for
   students, organized by complexity level or application domain.

🔧 **Integration with Existing Tools:**
   The REST API can be integrated with existing PLCs, IDEs, or automation
   tools to automatically sync code libraries.
    """)


if __name__ == "__main__":
    print("🧪 Code Library API Test Suite")
    print("Make sure the FastAPI server is running on localhost:8000")
    print()
    
    try:
        asyncio.run(test_code_library_api())
        asyncio.run(demonstrate_user_workflow())
        
        print("\n✅ All tests completed!")
        print("\n💡 Try these endpoints in your browser or Postman:")
        print(f"   📊 Library Summary: {BASE_URL}/")
        print(f"   🔍 Search: POST {BASE_URL}/search")
        print(f"   📤 Upload: POST {BASE_URL}/upload")
        print(f"   📁 Browse: {BASE_URL}/browse/motor_control")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("Make sure the FastAPI server is running and the endpoints are accessible.")