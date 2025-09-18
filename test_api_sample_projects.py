#!/usr/bin/env python3
"""
Test the sample projects fix through the API endpoint.
"""

import json
import requests

BASE_URL = "http://127.0.0.1:8001"

def test_api_sample_projects():
    print("🧪 Testing Sample Projects Fix via API")
    print("=" * 45)
    
    # Test 1: Off-topic message → should get sample projects
    print("\n1️⃣ Test: Off-topic request via API")
    
    form_data = {
        'message': 'I want to learn about cooking recipes',
        'current_context': json.dumps({
            'device_constants': {},
            'information': ''
        }),
        'current_stage': 'gathering_requirements'
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/context/update", data=form_data)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Response received")
        print(f"   Is MCQ: {data.get('is_mcq', False)}")
        print(f"   MCQ Options: {data.get('mcq_options', [])}")
        print(f"   Options count: {len(data.get('mcq_options', []))}")
        
        # Test 2: Select one of the sample projects
        if data.get('mcq_options'):
            print("\n2️⃣ Test: Select sample project (should break out of loop)")
            
            selected_option = data['mcq_options'][0]
            print(f"   Selecting: {selected_option}")
            
            form_data2 = {
                'message': 'I want to learn about cooking recipes',  # Still off-topic original message
                'mcq_responses': json.dumps([selected_option]),      # But with MCQ response
                'current_context': json.dumps({
                    'device_constants': {},
                    'information': ''
                }),
                'current_stage': 'gathering_requirements'
            }
            
            response2 = requests.post(f"{BASE_URL}/api/v1/context/update", data=form_data2)
            
            if response2.status_code == 200:
                data2 = response2.json()
                print(f"   ✅ Follow-up response received")
                print(f"   Message: {data2.get('chat_message', '')[:120]}...")
                is_sample_projects = 'sample projects' in data2.get('chat_message', '').lower()
                print(f"   Broke out of sample projects loop: {'✅' if not is_sample_projects else '❌'}")
            else:
                print(f"   ❌ Error: {response2.status_code}")
        
    else:
        print(f"   ❌ Error: {response.status_code}")

if __name__ == "__main__":
    test_api_sample_projects()