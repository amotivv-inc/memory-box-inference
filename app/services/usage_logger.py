"""Service for logging API usage and calculating costs"""

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.database import Request, UsageLog
from datetime import datetime
from decimal import Decimal
import json
import logging

logger = logging.getLogger(__name__)


class UsageLoggerService:
    """Service for handling usage logging and cost calculation"""
    
    # Model pricing per 1M tokens (as of 2025)
    MODEL_PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-2024-08-06": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o-mini-2024-07-18": {"input": 0.15, "output": 0.60},
        "o1": {"input": 15.00, "output": 60.00},
        "o1-2024-12-17": {"input": 15.00, "output": 60.00},
        "o1-mini": {"input": 3.00, "output": 12.00},
        "o1-mini-2024-09-12": {"input": 3.00, "output": 12.00},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-4-turbo-2024-04-09": {"input": 10.00, "output": 30.00},
        "gpt-4": {"input": 30.00, "output": 60.00},
        "gpt-4-0613": {"input": 30.00, "output": 60.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        "gpt-3.5-turbo-0125": {"input": 0.50, "output": 1.50},
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_request(
        self,
        request_id: str,
        session_id: str,
        user_id: str,
        api_key_id: str,
        model: str,
        request_payload: Dict[str, Any],
        persona_id: Optional[str] = None
    ) -> Request:
        """
        Create a new request record
        
        Args:
            request_id: Unique request ID
            session_id: Session ID
            user_id: User ID
            api_key_id: API key ID
            model: Model name
            request_payload: Request data
            
        Returns:
            Request model instance
        """
        request = Request(
            request_id=request_id,
            session_id=session_id,
            user_id=user_id,
            api_key_id=api_key_id,
            model=model,
            request_payload=request_payload,
            status="pending",
            persona_id=persona_id
        )
        self.db.add(request)
        await self.db.flush()
        
        logger.info(f"Created request {request_id} for model {model}")
        return request
    
    async def update_request_status(
        self,
        request_id: str,
        status: str,
        response_payload: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update request status and response
        
        Args:
            request_id: Request ID to update
            status: New status
            response_payload: Response data if successful
            error_message: Error message if failed
            
        Returns:
            True if updated, False if not found
        """
        result = await self.db.execute(
            select(Request).where(Request.request_id == request_id)
        )
        request = result.scalar_one_or_none()
        
        if not request:
            logger.error(f"Request {request_id} not found for status update")
            return False
        
        request.status = status
        request.completed_at = datetime.utcnow()
        
        if response_payload:
            request.response_payload = response_payload
        if error_message:
            request.error_message = error_message
        
        await self.db.flush()
        logger.info(f"Updated request {request_id} status to {status}")
        return True
    
    async def log_usage(
        self,
        request_id: str,
        usage_data: Dict[str, Any],
        model: str
    ) -> UsageLog:
        """
        Log token usage and calculate cost
        
        Args:
            request_id: Request ID
            usage_data: Usage data from OpenAI response
            model: Model name
            
        Returns:
            UsageLog model instance
        """
        # Extract token counts
        input_tokens = usage_data.get("input_tokens", 0)
        output_tokens = usage_data.get("output_tokens", 0)
        output_details = usage_data.get("output_tokens_details", {})
        reasoning_tokens = output_details.get("reasoning_tokens", 0)
        total_tokens = usage_data.get("total_tokens", 0)
        
        # Calculate cost
        cost_usd = self._calculate_cost(model, input_tokens, output_tokens)
        
        # Get request record
        result = await self.db.execute(
            select(Request).where(Request.request_id == request_id)
        )
        request = result.scalar_one_or_none()
        
        if not request:
            logger.error(f"Request {request_id} not found for usage logging")
            raise ValueError(f"Request {request_id} not found")
        
        # Create usage log
        usage_log = UsageLog(
            request_id=request.id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            reasoning_tokens=reasoning_tokens,
            total_tokens=total_tokens,
            model=model,
            cost_usd=cost_usd
        )
        self.db.add(usage_log)
        await self.db.flush()
        
        logger.info(
            f"Logged usage for request {request_id}: "
            f"{total_tokens} tokens, ${cost_usd:.6f}"
        )
        return usage_log
    
    def _calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> Decimal:
        """
        Calculate cost based on model and token usage
        
        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost in USD as Decimal
        """
        # Get base model name (remove date suffixes)
        base_model = model
        for key in self.MODEL_PRICING:
            if model.startswith(key.split("-")[0]):
                base_model = key
                break
        
        pricing = self.MODEL_PRICING.get(base_model)
        if not pricing:
            logger.warning(f"No pricing found for model {model}, using default")
            pricing = {"input": 1.00, "output": 2.00}
        
        # Calculate cost (pricing is per 1M tokens)
        input_cost = Decimal(str(input_tokens)) * Decimal(str(pricing["input"])) / Decimal("1000000")
        output_cost = Decimal(str(output_tokens)) * Decimal(str(pricing["output"])) / Decimal("1000000")
        
        total_cost = input_cost + output_cost
        return total_cost.quantize(Decimal("0.000001"))
    
    async def get_user_usage_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get usage statistics for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with usage statistics
        """
        # Get all requests for user
        result = await self.db.execute(
            select(Request)
            .where(Request.user_id == user_id)
            .where(Request.status == "completed")
        )
        requests = result.scalars().all()
        
        total_requests = len(requests)
        total_cost = Decimal("0")
        total_tokens = 0
        
        # Get usage logs for these requests
        for request in requests:
            usage_result = await self.db.execute(
                select(UsageLog).where(UsageLog.request_id == request.id)
            )
            usage_logs = usage_result.scalars().all()
            
            for log in usage_logs:
                if log.cost_usd:
                    total_cost += log.cost_usd
                if log.total_tokens:
                    total_tokens += log.total_tokens
        
        return {
            "user_id": user_id,
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "total_cost_usd": float(total_cost),
            "average_tokens_per_request": total_tokens / total_requests if total_requests > 0 else 0,
            "average_cost_per_request": float(total_cost / total_requests) if total_requests > 0 else 0
        }
