"""Test script for the analysis feature"""

import asyncio
import httpx
import json
from datetime import datetime
import uuid

# Configuration
BASE_URL = "http://localhost:8000"
JWT_TOKEN = "your-jwt-token-here"  # Replace with actual JWT token

# Headers
headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json",
    "X-User-ID": "test-user"
}


async def test_create_analysis_config():
    """Test creating an analysis configuration"""
    print("\n=== Testing Create Analysis Config ===")
    
    config_data = {
        "name": "Customer Intent Classifier",
        "description": "Classifies customer intents for support routing",
        "config": {
            "analysis_type": "intent",
            "categories": [
                {
                    "name": "technical_support",
                    "description": "Customer needs help with technical issues",
                    "examples": ["My app won't load", "Getting an error message", "Can't connect"]
                },
                {
                    "name": "billing_inquiry",
                    "description": "Questions about billing, payments, or subscriptions",
                    "examples": ["What's this charge?", "How do I cancel?", "Payment failed"]
                },
                {
                    "name": "feature_request",
                    "description": "Customer is requesting new features or improvements",
                    "examples": ["Can you add", "It would be great if", "I wish it could"]
                },
                {
                    "name": "general_inquiry",
                    "description": "General questions or information requests",
                    "examples": ["How does this work?", "What is", "Tell me about"]
                }
            ],
            "model": "gpt-4o-mini",
            "temperature": 0.3,
            "include_reasoning": True,
            "include_confidence": True,
            "confidence_threshold": 0.7
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/v1/analysis/configs",
            headers=headers,
            json=config_data
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Config ID: {result['id']}")
            print(f"Config Name: {result['name']}")
            return result['id']
        else:
            print(f"Error: {response.text}")
            return None


async def test_list_analysis_configs():
    """Test listing analysis configurations"""
    print("\n=== Testing List Analysis Configs ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/v1/analysis/configs",
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Total configs: {result['total']}")
            for config in result['items']:
                print(f"  - {config['name']} (ID: {config['id']})")
        else:
            print(f"Error: {response.text}")


async def test_analyze_with_config(config_id: str, request_id: str):
    """Test analyzing a conversation with a saved config"""
    print(f"\n=== Testing Analysis with Config ID ===")
    
    analysis_request = {
        "id": request_id,
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
            print(f"Primary Category: {result['primary_category']}")
            print(f"Confidence: {result['confidence']}")
            print(f"Reasoning: {result['reasoning']}")
            print("\nAll Categories:")
            for cat in result['categories']:
                print(f"  - {cat['name']}: {cat['confidence']:.2f}")
            print(f"\nCached: {result['cached']}")
            print(f"Cost: ${result['cost_usd']:.6f}")
        else:
            print(f"Error: {response.text}")


async def test_analyze_with_inline_config(request_id: str):
    """Test analyzing with an inline configuration"""
    print(f"\n=== Testing Analysis with Inline Config ===")
    
    analysis_request = {
        "id": request_id,
        "config": {
            "analysis_type": "sentiment",
            "categories": [
                {
                    "name": "positive",
                    "description": "Positive sentiment",
                    "examples": ["Great!", "Love it", "Excellent"]
                },
                {
                    "name": "neutral",
                    "description": "Neutral sentiment",
                    "examples": ["Okay", "Fine", "It's alright"]
                },
                {
                    "name": "negative",
                    "description": "Negative sentiment",
                    "examples": ["Bad", "Terrible", "Hate it"]
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
            print(f"Primary Category: {result['primary_category']}")
            print(f"Confidence: {result['confidence']}")
            print(f"Reasoning: {result['reasoning']}")
            print("\nAll Categories:")
            for cat in result['categories']:
                print(f"  - {cat['name']}: {cat['confidence']:.2f}")
        else:
            print(f"Error: {response.text}")


async def test_analyze_by_response_id(response_id: str):
    """Test analyzing using a response ID"""
    print(f"\n=== Testing Analysis by Response ID ===")
    
    analysis_request = {
        "id": response_id,
        "config": {
            "analysis_type": "urgency",
            "categories": [
                {
                    "name": "high",
                    "description": "Requires immediate attention",
                    "examples": ["Emergency", "Urgent", "ASAP", "Critical"]
                },
                {
                    "name": "medium",
                    "description": "Should be addressed soon",
                    "examples": ["Soon", "When you can", "Important"]
                },
                {
                    "name": "low",
                    "description": "Can wait",
                    "examples": ["Whenever", "No rush", "FYI"]
                }
            ],
            "model": "gpt-4o-mini",
            "temperature": 0.2
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
            print(f"Request ID: {result['request_id']}")
            print(f"Response ID: {result['response_id']}")
            print(f"Primary Category: {result['primary_category']}")
            print(f"Analysis Type: {result['analysis_type']}")
        else:
            print(f"Error: {response.text}")


async def main():
    """Run all tests"""
    print("=== Analysis Feature Test Suite ===")
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {datetime.now()}")
    
    # Note: You'll need to replace these with actual IDs from your system
    test_request_id = "req_test123"  # Replace with actual request ID
    test_response_id = "resp_test123"  # Replace with actual response ID
    
    # Test 1: Create a configuration
    config_id = await test_create_analysis_config()
    
    # Test 2: List configurations
    await test_list_analysis_configs()
    
    # Test 3: Analyze with saved config
    if config_id:
        await test_analyze_with_config(config_id, test_request_id)
    
    # Test 4: Analyze with inline config
    await test_analyze_with_inline_config(test_request_id)
    
    # Test 5: Analyze by response ID
    await test_analyze_by_response_id(test_response_id)
    
    print("\n=== Test Suite Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
