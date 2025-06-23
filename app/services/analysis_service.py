"""Service for handling conversation analysis (intents, sentiments, topics, etc.)"""

from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.database import (
    Request, AnalysisConfig, AnalysisResult, Organization, User
)
from app.models.analysis import (
    AnalysisConfigData, CategoryDefinition, CategoryResult
)
from app.core.openai_client import openai_client
from app.core.security import decrypt_api_key
from app.services.key_mapper import KeyMapperService
from datetime import datetime
from decimal import Decimal
import json
import uuid
import hashlib
import logging

logger = logging.getLogger(__name__)


class AnalysisService:
    """Service for performing conversation analysis"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def analyze(
        self,
        id: str,
        config_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        config_overrides: Optional[Dict[str, Any]] = None,
        organization_id: str = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a request/response for intents, sentiments, or other categories
        
        Args:
            id: Request ID or Response ID
            config_id: ID of saved configuration to use
            config: Inline configuration
            config_overrides: Override specific config fields
            organization_id: Organization ID for access control
            user_id: User ID for tracking
            
        Returns:
            Analysis results
        """
        # Get the request data
        request_data = await self._get_request_data(id)
        if not request_data:
            raise ValueError(f"Request with ID {id} not found")
            
        # Verify organization access
        if not await self._verify_organization_access(request_data, organization_id):
            raise ValueError("Not authorized to analyze this request")
            
        # Get or build configuration
        final_config = await self._get_final_config(
            config_id, config, config_overrides, organization_id
        )
        
        # Check cache
        config_hash = self._hash_config(final_config)
        cached_result = await self._get_cached_result(request_data.id, config_hash)
        if cached_result:
            return self._format_cached_result(cached_result)
            
        # Get API key for OpenAI
        key_mapper = KeyMapperService(self.db)
        api_key = await key_mapper.get_openai_key(organization_id)
        if not api_key:
            raise ValueError("No active API key found for organization")
            
        # Perform analysis
        analysis_result = await self._perform_analysis(
            request_data=request_data,
            config=final_config,
            api_key=api_key
        )
        
        # Store result
        stored_result = await self._store_result(
            request_id=request_data.id,
            config_id=config_id,
            config_snapshot=final_config,
            analysis_result=analysis_result
        )
        
        return self._format_result(stored_result, request_data)
        
    async def _get_request_data(self, id: str) -> Optional[Request]:
        """Get request by request_id or response_id"""
        # Try request_id first
        result = await self.db.execute(
            select(Request).where(Request.request_id == id)
        )
        request = result.scalar_one_or_none()
        
        # Try response_id if not found
        if not request:
            result = await self.db.execute(
                select(Request).where(Request.response_id == id)
            )
            request = result.scalar_one_or_none()
            
        return request
        
    async def _verify_organization_access(
        self, 
        request: Request, 
        organization_id: str
    ) -> bool:
        """Verify the request belongs to the organization"""
        # Get the user's organization through the request
        result = await self.db.execute(
            select(User).where(User.id == request.user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return False
            
        return str(user.organization_id) == organization_id
        
    async def _get_final_config(
        self,
        config_id: Optional[str],
        config: Optional[Dict[str, Any]],
        config_overrides: Optional[Dict[str, Any]],
        organization_id: str
    ) -> Dict[str, Any]:
        """Get the final configuration to use"""
        final_config = {}
        
        # Start with saved config if provided
        if config_id:
            saved_config = await self._get_saved_config(config_id, organization_id)
            if saved_config:
                final_config = saved_config.config.copy()
                
        # Override with inline config
        if config:
            final_config.update(config)
            
        # Apply overrides
        if config_overrides:
            final_config.update(config_overrides)
            
        # Validate we have required fields
        if not final_config.get("categories") and not final_config.get("analysis_type"):
            raise ValueError("Configuration must include categories or analysis_type")
            
        # Set defaults
        final_config.setdefault("model", "gpt-4o-mini")
        final_config.setdefault("temperature", 0.3)
        final_config.setdefault("include_reasoning", True)
        final_config.setdefault("include_confidence", True)
        
        return final_config
        
    async def _get_saved_config(
        self, 
        config_id: str, 
        organization_id: str
    ) -> Optional[AnalysisConfig]:
        """Get a saved configuration"""
        result = await self.db.execute(
            select(AnalysisConfig).where(
                and_(
                    AnalysisConfig.id == config_id,
                    AnalysisConfig.organization_id == organization_id,
                    AnalysisConfig.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()
        
    def _hash_config(self, config: Dict[str, Any]) -> str:
        """Create a hash of the configuration for caching"""
        # Sort keys for consistent hashing
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()
        
    async def _get_cached_result(
        self, 
        request_id: uuid.UUID, 
        config_hash: str
    ) -> Optional[AnalysisResult]:
        """Check if we have a cached result"""
        # For now, we'll use config_hash comparison
        # In a future version, we could store the hash in the DB
        result = await self.db.execute(
            select(AnalysisResult).where(
                AnalysisResult.request_id == request_id
            )
        )
        
        for analysis in result.scalars().all():
            if self._hash_config(analysis.config_snapshot) == config_hash:
                return analysis
                
        return None
        
    async def _perform_analysis(
        self,
        request_data: Request,
        config: Dict[str, Any],
        api_key: str
    ) -> Dict[str, Any]:
        """Perform the actual analysis using OpenAI"""
        # Extract input and response from request
        user_input = request_data.request_payload.get("input", "")
        
        # Handle response payload - it follows the OpenAI Responses API structure
        response_content = ""
        if request_data.response_payload:
            # Check for the 'output' field which contains the response in Responses API
            if "output" in request_data.response_payload:
                output_array = request_data.response_payload.get("output", [])
                if output_array and isinstance(output_array, list):
                    # Navigate to output[0].content[0].text
                    first_output = output_array[0]
                    if "content" in first_output:
                        content_array = first_output.get("content", [])
                        if content_array and isinstance(content_array, list):
                            first_content = content_array[0]
                            response_content = first_content.get("text", "")
            elif "error" in request_data.response_payload:
                # Handle error responses
                response_content = f"Error: {request_data.response_payload.get('error')}"
                
        # Build prompt
        prompt = self._build_analysis_prompt(
            user_input=user_input,
            ai_response=response_content,
            config=config
        )
        
        # Call OpenAI
        analysis_request = {
            "model": config.get("model", "gpt-4o-mini"),
            "input": prompt,
            "temperature": config.get("temperature", 0.3),
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "analysis_response",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "primary_category": {"type": "string"},
                            "categories": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "confidence": {"type": "number"}
                                    },
                                    "required": ["name", "confidence"],
                                    "additionalProperties": False
                                }
                            },
                            "reasoning": {"type": "string"},
                            "metadata": {
                                "type": "object",
                                "properties": {
                                    "sentiment": {"type": "string"},
                                    "urgency": {"type": "string"},
                                    "topics": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["sentiment", "urgency", "topics"],
                                "additionalProperties": False
                            }
                        },
                        "required": ["primary_category", "categories", "reasoning", "metadata"],
                        "additionalProperties": False
                    }
                }
            }
        }
        
        # Get response
        response_text = ""
        tokens_used = 0
        
        try:
            response_generator = openai_client.create_response(
                api_key=api_key,
                request_data=analysis_request,
                stream=False
            )
            
            async for chunk in response_generator:
                response_text = chunk
                break
                
            # Parse response
            response_data = json.loads(response_text)
            
            # Log the full response for debugging
            logger.info(f"Full OpenAI response for analysis: {json.dumps(response_data, indent=2)}")
            
            # Extract usage data
            if "usage" in response_data:
                tokens_used = response_data["usage"].get("total_tokens", 0)
                
            # Extract the actual analysis from the response - follows Responses API structure
            if "output" in response_data and response_data["output"]:
                output_array = response_data["output"]
                if output_array and isinstance(output_array, list):
                    first_output = output_array[0]
                    if "content" in first_output:
                        content_array = first_output.get("content", [])
                        if content_array and isinstance(content_array, list):
                            first_content = content_array[0]
                            analysis_text = first_content.get("text", "{}")
                            analysis_data = json.loads(analysis_text)
                        else:
                            raise ValueError("No content in analysis response")
                    else:
                        raise ValueError("No content in analysis response output")
                else:
                    raise ValueError("Invalid output format in analysis response")
            else:
                raise ValueError("No output in analysis response")
                
        except Exception as e:
            logger.error(f"Error performing analysis: {e}")
            raise
            
        # Calculate cost
        cost_usd = self._calculate_cost(
            model=config.get("model", "gpt-4o-mini"),
            tokens=tokens_used
        )
        
        return {
            "raw_result": analysis_data,
            "tokens_used": tokens_used,
            "cost_usd": cost_usd,
            "model_used": config.get("model", "gpt-4o-mini")
        }
        
    def _build_analysis_prompt(
        self,
        user_input: str,
        ai_response: str,
        config: Dict[str, Any]
    ) -> str:
        """Build the analysis prompt"""
        analysis_type = config.get("analysis_type", "classification")
        categories = config.get("categories", [])
        
        # Convert categories to a readable format
        category_descriptions = []
        for cat in categories:
            if isinstance(cat, dict):
                name = cat.get("name", "")
                desc = cat.get("description", "")
                examples = cat.get("examples", [])
                
                cat_text = f"- {name}: {desc}"
                if examples:
                    cat_text += f" (Examples: {', '.join(examples[:3])})"
                category_descriptions.append(cat_text)
            else:
                # Simple string category
                category_descriptions.append(f"- {cat}")
                
        categories_text = "\n".join(category_descriptions)
        
        # Check for custom prompt
        if config.get("custom_prompt"):
            prompt = config["custom_prompt"].format(
                user_input=user_input,
                ai_response=ai_response,
                categories=categories_text
            )
        else:
            # Default prompt
            # Extract just the category names for the example
            category_names = []
            for cat in categories:
                if isinstance(cat, dict):
                    category_names.append(cat.get("name", ""))
                else:
                    category_names.append(str(cat))
            
            prompt = f"""Analyze the following conversation and classify it according to the given categories.

User Message: {user_input}

AI Response: {ai_response}

Categories:
{categories_text}

Analyze this conversation and provide:
1. The primary category that best matches from the categories listed above
2. Confidence score (0.0 to 1.0) for EACH of the categories listed above
3. Brief reasoning for the classification

You MUST include ALL categories in your response with their confidence scores.

Respond in JSON format:
{{
    "primary_category": "{category_names[0] if category_names else 'category_name'}",
    "categories": [
        {', '.join([f'{{"name": "{name}", "confidence": 0.0}}' for name in category_names[:2]])}
    ],
    "reasoning": "Brief explanation of why this category was chosen",
    "metadata": {{
        "sentiment": "positive/neutral/negative",
        "urgency": "low/medium/high",
        "topics": ["relevant", "topics", "from", "conversation"]
    }}
}}

IMPORTANT: The "categories" array must include ALL the categories I listed above, each with their name and confidence score."""
        
        return prompt
        
    def _calculate_cost(self, model: str, tokens: int) -> float:
        """Calculate the cost of the analysis"""
        # Simplified pricing (you may want to import from usage_logger)
        pricing = {
            "gpt-4o-mini": 0.15 / 1_000_000,  # $0.15 per 1M tokens
            "gpt-4o": 2.50 / 1_000_000,  # $2.50 per 1M tokens
        }
        
        rate = pricing.get(model, pricing["gpt-4o-mini"])
        return tokens * rate
        
    async def _store_result(
        self,
        request_id: uuid.UUID,
        config_id: Optional[str],
        config_snapshot: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> AnalysisResult:
        """Store the analysis result"""
        result = AnalysisResult(
            id=uuid.uuid4(),
            request_id=request_id,
            analysis_config_id=uuid.UUID(config_id) if config_id else None,
            config_snapshot=config_snapshot,
            analysis_type=config_snapshot.get("analysis_type", "classification"),
            results=analysis_result["raw_result"],
            model_used=analysis_result["model_used"],
            tokens_used=analysis_result["tokens_used"],
            cost_usd=Decimal(str(analysis_result["cost_usd"]))
        )
        
        self.db.add(result)
        await self.db.commit()
        await self.db.refresh(result)
        
        return result
        
    def _format_result(
        self, 
        analysis_result: AnalysisResult,
        request_data: Request
    ) -> Dict[str, Any]:
        """Format the result for API response"""
        results = analysis_result.results
        
        # Extract categories
        categories = []
        for cat in results.get("categories", []):
            categories.append(CategoryResult(
                name=cat["name"],
                confidence=cat["confidence"],
                reasoning=cat.get("reasoning")
            ))
            
        return {
            "request_id": request_data.request_id,
            "response_id": request_data.response_id,
            "analysis_type": analysis_result.analysis_type,
            "primary_category": results.get("primary_category"),
            "categories": [cat.model_dump() for cat in categories],
            "confidence": max(cat.confidence for cat in categories) if categories else None,
            "reasoning": results.get("reasoning"),
            "metadata": results.get("metadata"),
            "analyzed_at": analysis_result.created_at,
            "model_used": analysis_result.model_used,
            "tokens_used": analysis_result.tokens_used,
            "cost_usd": float(analysis_result.cost_usd),
            "cached": False
        }
        
    def _format_cached_result(self, analysis_result: AnalysisResult) -> Dict[str, Any]:
        """Format a cached result"""
        # Similar to _format_result but with cached=True
        result = self._format_result(analysis_result, analysis_result.request)
        result["cached"] = True
        return result
