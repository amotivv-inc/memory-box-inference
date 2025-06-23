#!/usr/bin/env python3
"""Test the analysis feature with a real JWT and request - Version 2"""

import asyncio
import httpx
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2N2RkYTQ2OS0wNmM0LTQyN2QtYTk1ZC04MjY5NTc4NTIwZmUiLCJvcmdfbmFtZSI6IlRlc3QtT3JnLTE3NDkyMDcyMDUiLCJpYXQiOjE3NTA2OTkyNTksImV4cCI6MTc1MzI5MTI1OX0.xlDUQb-mzNUdIGtqw-SsITZ1Ulxd8XLv2eoBsz0Kx2U"
REQUEST_ID = "req_24449b7a90e745e4aa7e30b41b4c2269"

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}


async def get_config_by_name(name):
    """Get configuration by name"""
    print(f"\n=== Getting Config by Name: {name} ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/v1/analysis/configs/by-name/{name}",
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Found config ID: {result['id']}")
            return result['id']
        else:
            print(f"Error: {response.text}")
            return None


async def test_simple_analysis():
    """Test with a very simple inline config"""
    print(f"\n=== Testing Simple Analysis ===")
    
    # First, let's check what content we're analyzing
    print(f"Analyzing request: {REQUEST_ID}")
    
    analysis_request = {
        "id": REQUEST_ID,
        "config": {
            "analysis_type": "intent",
            "categories": [
                {
                    "name": "greeting",
                    "description": "User is greeting",
                    "examples": ["hello", "hi"]
                },
                {
                    "name": "other",
                    "description": "Other messages",
                    "examples": ["bye", "thanks"]
                }
            ],
            "model": "gpt-4o-mini",
            "temperature": 0.1
        }
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/v1/analysis",
            headers=headers,
            json=analysis_request
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nAnalysis Results:")
            print(f"Primary Category: {result.get('primary_category', 'N/A')}")
            print(f"Confidence: {result.get('confidence', 0):.2%}")
            return result
        else:
            return None


async def test_with_response_id():
    """Test using response ID instead of request ID"""
    print(f"\n=== Testing with Response ID ===")
    
    response_id = "resp_6842c8a7d9ac81a1a6d551628ac59d4309dcb5ecd2a13ef0"
    
    analysis_request = {
        "id": response_id,
        "config": {
            "analysis_type": "sentiment",
            "categories": [
                {
                    "name": "positive",
                    "description": "Positive sentiment",
                    "examples": ["good", "great", "happy"]
                },
                {
                    "name": "neutral",
                    "description": "Neutral sentiment",
                    "examples": ["okay", "fine"]
                }
            ],
            "model": "gpt-4o-mini",
            "temperature": 0.1
        }
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/v1/analysis",
            headers=headers,
            json=analysis_request
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")


async def check_request_content():
    """Check what content is in the request we're trying to analyze"""
    print(f"\n=== Checking Request Content ===")
    
    # Get the response content
    response_id = "resp_6842c8a7d9ac81a1a6d551628ac59d4309dcb5ecd2a13ef0"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/v1/responses/{response_id}",
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response content: {json.dumps(result, indent=2)}")
        else:
            print(f"Error: {response.text}")


async def main():
    """Run all tests"""
    print("=== Analysis Feature Test V2 ===")
    print(f"Time: {datetime.now()}")
    print(f"Organization: Test-Org-1749207205")
    
    # First check what we're analyzing
    await check_request_content()
    
    # Test 1: Get existing config
    config_id = await get_config_by_name("Test Intent Classifier")
    
    # Test 2: Simple analysis
    await test_simple_analysis()
    
    # Test 3: Try with response ID
    await test_with_response_id()
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
