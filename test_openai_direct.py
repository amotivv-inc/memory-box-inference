#!/usr/bin/env python3
"""Test OpenAI API directly"""

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


async def test_direct_openai_request():
    """Test making a direct request through the proxy"""
    print("\n=== Testing Direct OpenAI Request ===")
    
    request_data = {
        "input": "Hello, how are you?",
        "model": "gpt-4o-mini",
        "max_output_tokens": 50,
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
            print(f"Status: {result.get('status')}")
            if result.get('output'):
                for output in result['output']:
                    if output.get('content'):
                        for content in output['content']:
                            if content.get('text'):
                                print(f"AI Response: {content['text']}")
            return result
        else:
            print(f"Error: {response.text}")
            return None


async def main():
    """Run the test"""
    print("=== Direct OpenAI API Test ===")
    
    # Test direct request
    result = await test_direct_openai_request()
    
    if result and result.get('id'):
        print(f"\n=== Now Testing Analysis on This Response ===")
        
        # Now try to analyze this response
        analysis_request = {
            "id": result['id'],
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
                        "examples": ["okay", "fine", "normal"]
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
            
            print(f"Analysis Status: {response.status_code}")
            print(f"Analysis Response: {response.text}")
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
