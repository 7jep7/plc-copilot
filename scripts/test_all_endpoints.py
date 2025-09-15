#!/usr/bin/env python3
"""
Comprehensive API endpoint testing script for PLC-Copilot.
Tests all available endpoints to ensure they're working correctly before frontend integration.
"""

import json
import time
from typing import Dict, Any, Optional
import requests

# Base URL for the API
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.test_results = []
        
    def test_endpoint(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                      files: Optional[Dict] = None, expected_status: int = 200,
                      description: str = "") -> Dict[str, Any]:
        """Test a single API endpoint and return results."""
        url = f"{self.base_url}{API_PREFIX}{endpoint}"
        
        print(f"\n🔍 Testing {method.upper()} {endpoint}")
        print(f"   Description: {description}")
        
        start_time = time.time()
        
        try:
            kwargs = {}
            if data:
                kwargs['json'] = data
            if files:
                kwargs['files'] = files
                
            response = requests.request(method, url, **kwargs)
            response_time = time.time() - start_time
            
            # Try to parse as JSON
            try:
                response_json = response.json()
            except json.JSONDecodeError:
                response_json = {"raw_response": response.text}
            
            result = {
                "endpoint": endpoint,
                "method": method,
                "description": description,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "success": response.status_code == expected_status,
                "response_time": round(response_time, 3),
                "response_data": response_json
            }
            
            # Print result
            status_emoji = "✅" if result["success"] else "❌"
            print(f"   {status_emoji} Status: {response.status_code} (expected {expected_status})")
            print(f"   ⏱️  Response time: {response_time:.3f}s")
            
            if not result["success"]:
                print(f"   📄 Response: {response.text[:200]}...")
            elif response.status_code < 400:
                # Show a snippet of successful responses
                if isinstance(response_json, dict):
                    keys = list(response_json.keys())[:3]
                    snippet = {k: response_json[k] for k in keys}
                    print(f"   📄 Response snippet: {snippet}")
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            result = {
                "endpoint": endpoint,
                "method": method,
                "description": description,
                "status_code": 0,
                "expected_status": expected_status,
                "success": False,
                "response_time": time.time() - start_time,
                "error": str(e)
            }
            print(f"   ❌ Error: {str(e)}")
            self.test_results.append(result)
            return result

    def run_all_tests(self):
        """Run comprehensive tests for all API endpoints."""
        print("🚀 Starting comprehensive API endpoint testing...")
        print(f"   Base URL: {self.base_url}")
        print("=" * 60)
        
        # Test root endpoint (without API prefix)
        try:
            response = requests.get(f"{self.base_url}/")
            print(f"\n🔍 Testing GET / (root endpoint)")
            print(f"   ✅ Status: {response.status_code}")
            root_data = response.json()
            print(f"   📄 Response: {root_data}")
        except Exception as e:
            print(f"   ❌ Root endpoint error: {e}")
        
        # Test health endpoint (without API prefix)
        try:
            response = requests.get(f"{self.base_url}/health")
            print(f"\n🔍 Testing GET /health")
            print(f"   ✅ Status: {response.status_code}")
            health_data = response.json()
            print(f"   📄 Response: {health_data}")
        except Exception as e:
            print(f"   ❌ Health endpoint error: {e}")
        
        # AI Chat endpoint
        self.test_endpoint(
            "POST", 
            "/ai/chat",
            data={
                "user_prompt": "Hello, can you help me with PLC programming?",
                "model": "gpt-5-nano",
                "temperature": 1.0
            },
            description="AI chat completion"
        )
        
        # Conversation endpoints
        conversation_id = None
        
        # Start a new conversation
        result = self.test_endpoint(
            "POST",
            "/conversations/",
            data={
                "conversation_id": "test-conv-001",
                "message": "I need help creating a PLC program for a conveyor belt system"
            },
            description="Start new conversation"
        )
        
        if result["success"]:
            conversation_id = result["response_data"].get("conversation_id", "test-conv-001")
            
            # Test conversation endpoints
            self.test_endpoint(
                "GET",
                f"/conversations/{conversation_id}",
                description="Get conversation state"
            )
            
            self.test_endpoint(
                "GET",
                f"/conversations/{conversation_id}/messages",
                description="Get conversation messages"
            )
            
            self.test_endpoint(
                "GET",
                f"/conversations/{conversation_id}/stage/suggestions",
                description="Get stage suggestions"
            )
            
            # List all conversations
            self.test_endpoint(
                "GET",
                "/conversations/",
                description="List all conversations"
            )
            
            # Test conversation health
            self.test_endpoint(
                "GET",
                "/conversations/health",
                description="Conversation system health check"
            )
        
        # PLC Code endpoints
        self.test_endpoint(
            "POST",
            "/plc/generate",
            data={
                "user_prompt": "Create a ladder logic program for a simple traffic light controller",
                "language": "ladder_logic",
                "name": "Traffic Light Controller",
                "description": "Simple traffic light control system"
            },
            description="Generate PLC code"
        )
        
        self.test_endpoint(
            "GET",
            "/plc/",
            description="List PLC codes"
        )
        
        # Digital Twin endpoints
        self.test_endpoint(
            "POST",
            "/digital-twin/",
            data={
                "name": "Test Conveyor System",
                "description": "Test digital twin for API validation",
                "simulation_type": "conveyor",
                "configuration": {"belt_speed": 1.5, "length": 10.0}
            },
            description="Create digital twin"
        )
        
        self.test_endpoint(
            "GET",
            "/digital-twin/",
            description="List digital twins"
        )
        
        # Document endpoints (test without actual file upload for now)
        self.test_endpoint(
            "GET",
            "/documents/",
            description="List documents"
        )
        
        print("\n" + "=" * 60)
        self.print_summary()
        
    def print_summary(self):
        """Print test summary."""
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - successful_tests
        
        print(f"📊 TEST SUMMARY")
        print(f"   Total tests: {total_tests}")
        print(f"   ✅ Successful: {successful_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   📈 Success rate: {(successful_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    error_msg = result.get('error', f"Status {result.get('status_code', 'unknown')}")
                    print(f"   ❌ {result['method']} {result['endpoint']}: {error_msg}")
        
        # Average response time
        response_times = [r["response_time"] for r in self.test_results if r["success"]]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            print(f"   ⏱️  Average response time: {avg_time:.3f}s")


def main():
    """Main test runner."""
    print("🎯 PLC-Copilot API Endpoint Testing")
    print("   This script tests all API endpoints to ensure they're ready for frontend integration.")
    
    tester = APITester()
    tester.run_all_tests()
        
    print("\n✨ Testing completed!")


if __name__ == "__main__":
    main()