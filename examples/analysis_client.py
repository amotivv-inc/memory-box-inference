"""
Example client for using the OpenAI Inference Proxy Analysis Feature

This example demonstrates how to:
1. Create analysis configurations
2. Analyze conversations for intents
3. Use both saved configs and inline configs
4. Handle caching and response IDs
"""

import asyncio
import httpx
import json
from typing import Dict, Any, Optional
import os


class AnalysisClient:
    """Client for interacting with the analysis API"""
    
    def __init__(self, base_url: str, jwt_token: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }
    
    async def create_intent_config(self) -> Optional[str]:
        """Create a reusable intent classification configuration"""
        config = {
            "name": "Customer Support Intent Classifier",
            "description": "Classifies customer messages into support categories for routing",
            "config": {
                "analysis_type": "intent",
                "categories": [
                    {
                        "name": "technical_support",
                        "description": "Technical issues, bugs, or errors",
                        "examples": [
                            "The app crashes when I click submit",
                            "I'm getting an error message",
                            "The feature isn't working properly"
                        ]
                    },
                    {
                        "name": "billing_inquiry",
                        "description": "Questions about billing, payments, or subscriptions",
                        "examples": [
                            "I was charged twice",
                            "How do I update my payment method?",
                            "I want to cancel my subscription"
                        ]
                    },
                    {
                        "name": "feature_request",
                        "description": "Suggestions for new features or improvements",
                        "examples": [
                            "It would be great if you could add",
                            "Have you considered implementing",
                            "I wish the app could"
                        ]
                    },
                    {
                        "name": "account_management",
                        "description": "Account-related issues like login, password, profile",
                        "examples": [
                            "I can't log in to my account",
                            "How do I reset my password?",
                            "I need to update my email address"
                        ]
                    },
                    {
                        "name": "general_inquiry",
                        "description": "General questions or information requests",
                        "examples": [
                            "What are your business hours?",
                            "How does this feature work?",
                            "Where can I find more information?"
                        ]
                    }
                ],
                "model": "gpt-4o-mini",
                "temperature": 0.3,
                "include_reasoning": True,
                "include_confidence": True,
                "confidence_threshold": 0.7,
                "multi_label": False
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/analysis/configs",
                headers=self.headers,
                json=config
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Created config: {result['name']} (ID: {result['id']})")
                return result['id']
            else:
                print(f"❌ Failed to create config: {response.text}")
                return None
    
    async def analyze_with_config(self, request_id: str, config_id: str) -> Dict[str, Any]:
        """Analyze a conversation using a saved configuration"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/analysis",
                headers=self.headers,
                json={
                    "id": request_id,
                    "config_id": config_id
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Analysis failed: {response.text}")
    
    async def analyze_sentiment(self, request_id: str) -> Dict[str, Any]:
        """Analyze sentiment using an inline configuration"""
        sentiment_config = {
            "analysis_type": "sentiment",
            "categories": [
                {
                    "name": "positive",
                    "description": "Positive sentiment - satisfaction, happiness, gratitude",
                    "examples": ["Thank you so much!", "This is amazing", "I love it"]
                },
                {
                    "name": "neutral",
                    "description": "Neutral sentiment - factual, informational",
                    "examples": ["I need information", "What are the options?", "Please explain"]
                },
                {
                    "name": "negative",
                    "description": "Negative sentiment - frustration, disappointment, anger",
                    "examples": ["This is terrible", "I'm very disappointed", "This doesn't work"]
                }
            ],
            "model": "gpt-4o-mini",
            "temperature": 0.3,
            "include_reasoning": True,
            "include_confidence": True
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/analysis",
                headers=self.headers,
                json={
                    "id": request_id,
                    "config": sentiment_config
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Analysis failed: {response.text}")
    
    async def analyze_urgency(self, response_id: str) -> Dict[str, Any]:
        """Analyze urgency level using response ID"""
        urgency_config = {
            "analysis_type": "urgency",
            "categories": [
                {
                    "name": "critical",
                    "description": "Requires immediate attention - system down, data loss risk",
                    "examples": ["Everything is down!", "We're losing customers", "Emergency!"]
                },
                {
                    "name": "high",
                    "description": "Important and time-sensitive",
                    "examples": ["Need this by end of day", "Urgent request", "ASAP"]
                },
                {
                    "name": "medium",
                    "description": "Should be addressed soon but not critical",
                    "examples": ["When you get a chance", "This week would be good", "Soon please"]
                },
                {
                    "name": "low",
                    "description": "Can wait, no immediate impact",
                    "examples": ["No rush", "Whenever convenient", "Just FYI"]
                }
            ],
            "model": "gpt-4o-mini",
            "temperature": 0.2,
            "include_reasoning": True
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/analysis",
                headers=self.headers,
                json={
                    "id": response_id,
                    "config": urgency_config
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Analysis failed: {response.text}")


def print_analysis_result(result: Dict[str, Any], title: str):
    """Pretty print analysis results"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    
    print(f"📊 Analysis Type: {result['analysis_type']}")
    print(f"🎯 Primary Category: {result['primary_category']}")
    print(f"💯 Confidence: {result.get('confidence', 0):.2%}")
    
    if result.get('reasoning'):
        print(f"💭 Reasoning: {result['reasoning']}")
    
    print("\n📈 All Categories:")
    for cat in result['categories']:
        confidence_bar = "█" * int(cat['confidence'] * 20)
        print(f"   {cat['name']:20} {confidence_bar:20} {cat['confidence']:.2%}")
        if cat.get('reasoning'):
            print(f"   └─ {cat['reasoning']}")
    
    if result.get('metadata'):
        print(f"\n📋 Metadata: {json.dumps(result['metadata'], indent=2)}")
    
    print(f"\n💰 Cost: ${result['cost_usd']:.6f}")
    print(f"🔄 Cached: {'Yes' if result['cached'] else 'No'}")
    print(f"🤖 Model: {result['model_used']}")


async def main():
    """Run example analysis scenarios"""
    # Configuration
    BASE_URL = os.getenv("PROXY_BASE_URL", "http://localhost:8000")
    JWT_TOKEN = os.getenv("PROXY_JWT_TOKEN", "your-jwt-token-here")
    
    # You need to replace these with actual IDs from your system
    SAMPLE_REQUEST_ID = os.getenv("SAMPLE_REQUEST_ID", "req_abc123")
    SAMPLE_RESPONSE_ID = os.getenv("SAMPLE_RESPONSE_ID", "resp_xyz789")
    
    print("🚀 OpenAI Inference Proxy - Analysis Feature Demo")
    print(f"📍 Server: {BASE_URL}")
    
    client = AnalysisClient(BASE_URL, JWT_TOKEN)
    
    try:
        # Step 1: Create a reusable configuration
        print("\n1️⃣ Creating Intent Classification Configuration...")
        config_id = await client.create_intent_config()
        
        if config_id:
            # Step 2: Analyze with saved config
            print("\n2️⃣ Analyzing conversation with saved config...")
            intent_result = await client.analyze_with_config(SAMPLE_REQUEST_ID, config_id)
            print_analysis_result(intent_result, "Intent Analysis Results")
            
            # Step 3: Run again to demonstrate caching
            print("\n3️⃣ Running same analysis again (should be cached)...")
            cached_result = await client.analyze_with_config(SAMPLE_REQUEST_ID, config_id)
            print(f"✅ Result was cached: {cached_result['cached']}")
        
        # Step 4: Analyze sentiment with inline config
        print("\n4️⃣ Analyzing sentiment with inline configuration...")
        sentiment_result = await client.analyze_sentiment(SAMPLE_REQUEST_ID)
        print_analysis_result(sentiment_result, "Sentiment Analysis Results")
        
        # Step 5: Analyze urgency using response ID
        print("\n5️⃣ Analyzing urgency using response ID...")
        urgency_result = await client.analyze_urgency(SAMPLE_RESPONSE_ID)
        print_analysis_result(urgency_result, "Urgency Analysis Results")
        
        print("\n✅ All analyses completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
