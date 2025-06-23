#!/usr/bin/env python3
"""Test the analysis feature with a real JWT and request"""

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


async def test_create_config():
    """Create an intent classification configuration"""
    print("\n=== Creating Analysis Configuration ===")
    
    config_data = {
        "name": "Test Intent Classifier",
        "description": "Test configuration for intent classification",
        "config": {
            "analysis_type": "intent",
            "categories": [
                {
                    "name": "greeting",
                    "description": "User is greeting or saying hello",
                    "examples": ["hello", "hi", "hey", "good morning"]
                },
                {
                    "name": "question",
                    "description": "User is asking a question",
                    "examples": ["what", "how", "why", "when", "where"]
                },
                {
                    "name": "request",
                    "description": "User is making a request or command",
                    "examples": ["please", "can you", "I need", "help me"]
                },
                {
                    "name": "other",
                    "description": "Other types of messages",
                    "examples": ["okay", "thanks", "bye"]
                }
            ],
            "model": "gpt-4o-mini",
            "temperature": 0.3,
            "include_reasoning": True,
            "include_confidence": True
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/v1/analysis/configs",
            headers=headers,
            json=config_data
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"Config created successfully!")
            print(f"Config ID: {result['id']}")
            print(f"Name: {result['name']}")
            return result['id']
        else:
            print(f"Error: {response.text}")
            return None


async def test_analyze_with_config(config_id):
    """Analyze the request using the configuration"""
    print(f"\n=== Analyzing Request with Config ===")
    print(f"Request ID: {REQUEST_ID}")
    
    analysis_request = {
        "id": REQUEST_ID,
        "config_id": config_id
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/v1/analysis",
            headers=headers,
            json=analysis_request
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"\nAnalysis Results:")
            print(f"Primary Category: {result['primary_category']}")
            print(f"Confidence: {result['confidence']:.2%}")
            print(f"Reasoning: {result['reasoning']}")
            print(f"\nAll Categories:")
            for cat in result['categories']:
                print(f"  - {cat['name']}: {cat['confidence']:.2%}")
            print(f"\nMetadata: {json.dumps(result.get('metadata', {}), indent=2)}")
            print(f"Cached: {result['cached']}")
            print(f"Cost: ${result['cost_usd']:.6f}")
            return result
        else:
            print(f"Error: {response.text}")
            return None


async def test_analyze_sentiment():
    """Test sentiment analysis with inline config"""
    print(f"\n=== Testing Sentiment Analysis ===")
    
    analysis_request = {
        "id": REQUEST_ID,
        "config": {
            "analysis_type": "sentiment",
            "categories": [
                {
                    "name": "positive",
                    "description": "Positive sentiment",
                    "examples": ["great", "love", "excellent", "happy"]
                },
                {
                    "name": "neutral",
                    "description": "Neutral sentiment",
                    "examples": ["okay", "fine", "alright", "normal"]
                },
                {
                    "name": "negative",
                    "description": "Negative sentiment",
                    "examples": ["bad", "hate", "terrible", "angry"]
                }
            ],
            "model": "gpt-4o-mini",
            "temperature": 0.3,
            "include_reasoning": True
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/v1/analysis",
            headers=headers,
            json=analysis_request
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"\nSentiment Analysis Results:")
            print(f"Primary Sentiment: {result['primary_category']}")
            print(f"Confidence: {result['confidence']:.2%}")
            print(f"Reasoning: {result['reasoning']}")
        else:
            print(f"Error: {response.text}")


async def test_list_configs():
    """List all configurations"""
    print(f"\n=== Listing All Configurations ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/v1/analysis/configs",
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Total configurations: {result['total']}")
            for config in result['items']:
                print(f"  - {config['name']} (ID: {config['id']})")
        else:
            print(f"Error: {response.text}")


async def main():
    """Run all tests"""
    print("=== Analysis Feature Test ===")
    print(f"Time: {datetime.now()}")
    print(f"Organization: Test-Org-1749207205")
    
    # Test 1: Create configuration
    config_id = await test_create_config()
    
    if config_id:
        # Test 2: Analyze with saved config
        await test_analyze_with_config(config_id)
        
        # Test 3: Run again to test caching
        print("\n=== Testing Cached Result ===")
        await test_analyze_with_config(config_id)
    
    # Test 4: Sentiment analysis with inline config
    await test_analyze_sentiment()
    
    # Test 5: List all configurations
    await test_list_configs()
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
