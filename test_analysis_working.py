#!/usr/bin/env python3
"""Test analysis feature with proper configuration"""

import asyncio
import httpx
import json

# Configuration
BASE_URL = "http://localhost:8000"
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2N2RkYTQ2OS0wNmM0LTQyN2QtYTk1ZC04MjY5NTc4NTIwZmUiLCJvcmdfbmFtZSI6IlRlc3QtT3JnLTE3NDkyMDcyMDUiLCJpYXQiOjE3NTA3MDAxODUsImV4cCI6MTc4MjIzNjE4NX0.2r0WYjc6tzbKtZT4VxzUNDc_NhbDxa_hzENxg3e38KM"

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json",
    "X-User-ID": "u1+4639ef65@ex.com"
}


async def create_conversation():
    """Create a conversation to analyze"""
    print("\n=== Creating Conversation ===")
    
    request_data = {
        "input": "I'm having trouble logging into my account. I keep getting an error message and I need help urgently!",
        "model": "gpt-4o-mini",
        "max_output_tokens": 100,
        "temperature": 0.7,
        "stream": False
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/v1/responses",
            headers=headers,
            json=request_data
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response ID: {result.get('id')}")
            
            # Extract the AI response
            if result.get('output'):
                for output in result['output']:
                    if output.get('content'):
                        for content in output['content']:
                            if content.get('text'):
                                print(f"AI Response: {content['text'][:100]}...")
            return result
        else:
            print(f"Error: {response.text}")
            return None


async def test_analysis(response_id: str):
    """Test the analysis feature"""
    print(f"\n=== Testing Analysis on Response {response_id} ===")
    
    # Test with a well-defined configuration
    analysis_request = {
        "id": response_id,
        "config": {
            "analysis_type": "intent_classification",
            "categories": [
                {
                    "name": "technical_support",
                    "description": "User needs help with technical issues, bugs, or system problems",
                    "examples": ["can't login", "error message", "system crash", "not working"]
                },
                {
                    "name": "billing_inquiry",
                    "description": "Questions about pricing, payments, or billing",
                    "examples": ["how much", "payment", "invoice", "charge"]
                },
                {
                    "name": "general_inquiry",
                    "description": "General questions or information requests",
                    "examples": ["how does it work", "what is", "tell me about"]
                },
                {
                    "name": "feedback",
                    "description": "User providing feedback, suggestions, or complaints",
                    "examples": ["I think", "suggestion", "would be better", "love it"]
                }
            ],
            "model": "gpt-4o-mini",
            "temperature": 0.1,
            "include_reasoning": True,
            "include_confidence": True
        }
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/v1/analysis",
            headers=headers,
            json=analysis_request
        )
        
        print(f"Analysis Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n=== Analysis Results ===")
            print(f"Primary Category: {result.get('primary_category')}")
            print(f"Confidence: {result.get('confidence')}")
            print(f"Reasoning: {result.get('reasoning')}")
            
            print("\nCategory Scores:")
            for cat in result.get('categories', []):
                print(f"  - {cat['name']}: {cat['confidence']:.2f}")
                
            if result.get('metadata'):
                print(f"\nMetadata:")
                print(f"  Sentiment: {result['metadata'].get('sentiment')}")
                print(f"  Urgency: {result['metadata'].get('urgency')}")
                print(f"  Topics: {', '.join(result['metadata'].get('topics', []))}")
                
            print(f"\nModel Used: {result.get('model_used')}")
            print(f"Tokens Used: {result.get('tokens_used')}")
            print(f"Cost: ${result.get('cost_usd', 0):.6f}")
            
            return result
        else:
            print(f"Error: {response.text}")
            return None


async def test_with_config_id():
    """Test using a saved configuration"""
    print("\n=== Testing with Saved Config ===")
    
    # First, let's use the config we know exists
    analysis_request = {
        "id": "req_24449b7a90e745e4aa7e30b41b4c2269",  # Using a known request ID
        "config_id": "4f863d9f-ecf5-4ee6-800b-6227c4f310bb"  # Test Intent Classifier
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/v1/analysis",
            headers=headers,
            json=analysis_request
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")


async def main():
    """Run all tests"""
    print("=== Analysis Feature Test ===")
    
    # Create a new conversation
    conversation = await create_conversation()
    
    if conversation and conversation.get('id'):
        # Test analysis on the new conversation
        await test_analysis(conversation['id'])
    
    # Also test with saved config
    await test_with_config_id()
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
