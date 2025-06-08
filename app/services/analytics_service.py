"""Service for analytics data"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics data"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_model_usage(
        self,
        organization_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get usage statistics by model
        
        Args:
            organization_id: Organization ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary with model usage statistics
        """
        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        logger.info(f"Getting model usage for org {organization_id} from {start_date} to {end_date}")
        
        # Build query for model stats
        model_query = """
        SELECT 
            r.model,
            COUNT(*) as request_count,
            COUNT(CASE WHEN r.status = 'completed' THEN 1 END) as success_count,
            COUNT(CASE WHEN r.status = 'failed' THEN 1 END) as failure_count,
            ROUND(COUNT(CASE WHEN r.status = 'completed' THEN 1 END)::numeric / 
                  NULLIF(COUNT(*), 0)::numeric * 100, 1) as success_rate,
            SUM(u.input_tokens) as input_tokens,
            SUM(u.output_tokens) as output_tokens,
            SUM(u.total_tokens) as total_tokens,
            SUM(u.cost_usd) as total_cost,
            AVG(EXTRACT(EPOCH FROM (r.completed_at - r.created_at))) as avg_response_time
        FROM requests r
        JOIN api_keys a ON r.api_key_id = a.id
        LEFT JOIN usage_logs u ON r.id = u.request_id
        WHERE a.organization_id = :org_id
        AND r.created_at BETWEEN :start_date AND :end_date
        GROUP BY r.model
        ORDER BY request_count DESC
        """
        
        # Execute model query
        try:
            model_result = await self.db.execute(
                text(model_query),
                {
                    "org_id": organization_id,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            
            model_rows = model_result.fetchall()
            logger.info(f"Found {len(model_rows)} models with usage data")
            
            # Build query for total stats
            total_query = """
            SELECT 
                COUNT(*) as total_requests,
                SUM(u.cost_usd) as total_cost
            FROM requests r
            JOIN api_keys a ON r.api_key_id = a.id
            LEFT JOIN usage_logs u ON r.id = u.request_id
            WHERE a.organization_id = :org_id
            AND r.created_at BETWEEN :start_date AND :end_date
            """
            
            # Execute total query
            total_result = await self.db.execute(
                text(total_query),
                {
                    "org_id": organization_id,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            
            total_row = total_result.fetchone()
            
            # Format response
            models = []
            for row in model_rows:
                model_data = {
                    "model": row.model,
                    "request_count": row.request_count,
                    "success_count": row.success_count or 0,
                    "failure_count": row.failure_count or 0,
                    "success_rate": float(row.success_rate) if row.success_rate is not None else 0.0,
                    "input_tokens": row.input_tokens,
                    "output_tokens": row.output_tokens,
                    "total_tokens": row.total_tokens,
                    "total_cost": float(row.total_cost) if row.total_cost is not None else None,
                    "avg_response_time": float(row.avg_response_time) if row.avg_response_time is not None else None
                }
                models.append(model_data)
            
            return {
                "models": models,
                "total_requests": total_row.total_requests if total_row else 0,
                "total_cost": float(total_row.total_cost) if total_row and total_row.total_cost is not None else None,
                "period_start": start_date,
                "period_end": end_date
            }
            
        except Exception as e:
            logger.error(f"Error getting model usage: {e}")
            # Return empty result on error
            return {
                "models": [],
                "total_requests": 0,
                "total_cost": None,
                "period_start": start_date,
                "period_end": end_date
            }
            
    async def get_rated_responses(
        self,
        organization_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        rating: Optional[int] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get rated responses for an organization
        
        Args:
            organization_id: Organization ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            rating: Optional rating filter (-1, 0, 1)
            user_id: Optional user ID filter
            session_id: Optional session ID filter
            limit: Maximum number of results to return
            offset: Pagination offset
            
        Returns:
            Dictionary with rated responses data
        """
        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        logger.info(f"Getting rated responses for org {organization_id} from {start_date} to {end_date}")
        
        try:
            # Build query parameters
            params = {
                "org_id": organization_id,
                "start_date": start_date,
                "end_date": end_date,
                "limit": limit,
                "offset": offset
            }
            
            # Add filters if provided
            rating_filter = ""
            if rating is not None:
                rating_filter = "AND r.rating = :rating"
                params["rating"] = rating
                
            user_filter = ""
            if user_id is not None:
                user_filter = "AND u.user_id = :user_id"
                params["user_id"] = user_id
                
            session_filter = ""
            if session_id is not None:
                session_filter = "AND s.session_id = :session_id"
                params["session_id"] = session_id
            
            # Build query for rated responses
            responses_query = f"""
            SELECT 
                r.request_id,
                r.response_id,
                u.user_id as external_user_id,
                r.model,
                r.rating,
                r.rating_feedback,
                r.rating_timestamp,
                r.created_at,
                r.completed_at,
                -- Extract preview of input (simplified to avoid jsonb_typeof)
                SUBSTRING(CAST(r.request_payload->>'input' AS TEXT), 1, 100) as input_preview,
                -- Extract preview of output (simplified to avoid jsonb_typeof)
                SUBSTRING(CAST(r.response_payload AS TEXT), 1, 100) as output_preview
            FROM 
                requests r
            JOIN 
                users u ON r.user_id = u.id
            JOIN 
                sessions s ON r.session_id = s.id
            WHERE 
                u.organization_id = :org_id
                AND r.rating IS NOT NULL
                AND r.created_at BETWEEN :start_date AND :end_date
                {rating_filter}
                {user_filter}
                {session_filter}
            ORDER BY 
                r.rating_timestamp DESC
            LIMIT :limit OFFSET :offset
            """
            
            # Execute query
            responses_result = await self.db.execute(text(responses_query), params)
            response_rows = responses_result.fetchall()
            
            # Get counts
            counts_query = f"""
            SELECT 
                COUNT(*) as total_count,
                COUNT(CASE WHEN r.rating = 1 THEN 1 END) as positive_count,
                COUNT(CASE WHEN r.rating = -1 THEN 1 END) as negative_count,
                COUNT(CASE WHEN r.rating = 0 THEN 1 END) as neutral_count
            FROM 
                requests r
            JOIN 
                users u ON r.user_id = u.id
            JOIN 
                sessions s ON r.session_id = s.id
            WHERE 
                u.organization_id = :org_id
                AND r.rating IS NOT NULL
                AND r.created_at BETWEEN :start_date AND :end_date
                {rating_filter}
                {user_filter}
                {session_filter}
            """
            
            counts_result = await self.db.execute(text(counts_query), params)
            counts_row = counts_result.fetchone()
            
            # Format response
            rated_responses = []
            for row in response_rows:
                response_data = {
                    "request_id": row.request_id,
                    "response_id": row.response_id,
                    "user_id": row.external_user_id,
                    "model": row.model,
                    "rating": row.rating,
                    "rating_feedback": row.rating_feedback,
                    "rating_timestamp": row.rating_timestamp,
                    "created_at": row.created_at,
                    "completed_at": row.completed_at,
                    "input_preview": row.input_preview or "Input not available",
                    "output_preview": row.output_preview or "Output not available"
                }
                rated_responses.append(response_data)
            
            return {
                "rated_responses": rated_responses,
                "total_count": counts_row.total_count if counts_row else 0,
                "positive_count": counts_row.positive_count if counts_row else 0,
                "negative_count": counts_row.negative_count if counts_row else 0,
                "neutral_count": counts_row.neutral_count if counts_row else 0,
                "period_start": start_date,
                "period_end": end_date,
                "filtered_by_user": user_id,
                "filtered_by_session": session_id
            }
            
        except Exception as e:
            logger.error(f"Error getting rated responses: {e}")
            # Return empty result on error
            return {
                "rated_responses": [],
                "total_count": 0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "period_start": start_date,
                "period_end": end_date,
                "filtered_by_user": user_id,
                "filtered_by_session": session_id
            }
            
    async def get_user_usage(
        self,
        organization_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get usage statistics by user
        
        Args:
            organization_id: Organization ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            user_id: Optional user ID filter
            limit: Maximum number of results to return
            offset: Pagination offset
            
        Returns:
            Dictionary with user usage statistics
        """
        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        logger.info(f"Getting user usage for org {organization_id} from {start_date} to {end_date}")
        
        try:
            # Build query parameters
            params = {
                "org_id": organization_id,
                "start_date": start_date,
                "end_date": end_date,
                "limit": limit,
                "offset": offset
            }
            
            # Add user filter if provided
            user_filter = ""
            if user_id is not None:
                user_filter = "AND u.user_id = :user_id"
                params["user_id"] = user_id
            
            # Build query for user usage
            # Using raw SQL to avoid recursion issues
            user_query = f"""
            SELECT 
                u.user_id as external_user_id,
                COUNT(r.id) as request_count,
                COUNT(CASE WHEN r.status = 'completed' THEN 1 END) as success_count,
                COUNT(CASE WHEN r.status = 'failed' THEN 1 END) as failure_count,
                ROUND(COUNT(CASE WHEN r.status = 'completed' THEN 1 END)::numeric / 
                      NULLIF(COUNT(r.id), 0)::numeric * 100, 1) as success_rate,
                SUM(ul.input_tokens) as input_tokens,
                SUM(ul.output_tokens) as output_tokens,
                SUM(ul.total_tokens) as total_tokens,
                SUM(ul.cost_usd) as total_cost,
                AVG(EXTRACT(EPOCH FROM (r.completed_at - r.created_at))) as avg_response_time,
                MAX(r.created_at) as last_request_at,
                array_agg(DISTINCT r.model) FILTER (WHERE r.model IS NOT NULL) as models_used
            FROM 
                users u
            LEFT JOIN 
                requests r ON u.id = r.user_id AND r.created_at BETWEEN :start_date AND :end_date
            LEFT JOIN 
                usage_logs ul ON r.id = ul.request_id
            WHERE 
                u.organization_id = :org_id
                {user_filter}
            GROUP BY 
                u.user_id
            ORDER BY 
                request_count DESC NULLS LAST
            LIMIT :limit OFFSET :offset
            """
            
            # Execute query
            user_result = await self.db.execute(text(user_query), params)
            user_rows = user_result.fetchall()
            
            # Get total counts
            counts_query = f"""
            SELECT 
                COUNT(DISTINCT u.id) as total_users,
                COUNT(r.id) as total_requests,
                SUM(ul.cost_usd) as total_cost
            FROM 
                users u
            LEFT JOIN 
                requests r ON u.id = r.user_id AND r.created_at BETWEEN :start_date AND :end_date
            LEFT JOIN 
                usage_logs ul ON r.id = ul.request_id
            WHERE 
                u.organization_id = :org_id
                {user_filter}
            """
            
            counts_result = await self.db.execute(text(counts_query), params)
            counts_row = counts_result.fetchone()
            
            # Format response
            users = []
            for row in user_rows:
                # Handle NULL values and type conversions
                models_used = []
                if row.models_used:
                    # Convert PostgreSQL array to Python list
                    if isinstance(row.models_used, list):
                        models_used = row.models_used
                    else:
                        # Handle string representation of array if needed
                        try:
                            models_used = row.models_used.strip('{}').split(',')
                        except (AttributeError, ValueError):
                            models_used = []
                
                user_data = {
                    "user_id": row.external_user_id,
                    "request_count": row.request_count or 0,
                    "success_count": row.success_count or 0,
                    "failure_count": row.failure_count or 0,
                    "success_rate": float(row.success_rate) if row.success_rate is not None else 0.0,
                    "input_tokens": row.input_tokens,
                    "output_tokens": row.output_tokens,
                    "total_tokens": row.total_tokens,
                    "total_cost": float(row.total_cost) if row.total_cost is not None else None,
                    "avg_response_time": float(row.avg_response_time) if row.avg_response_time is not None else None,
                    "last_request_at": row.last_request_at,
                    "models_used": models_used
                }
                users.append(user_data)
            
            return {
                "users": users,
                "total_users": counts_row.total_users if counts_row else 0,
                "total_requests": counts_row.total_requests if counts_row else 0,
                "total_cost": float(counts_row.total_cost) if counts_row and counts_row.total_cost is not None else None,
                "period_start": start_date,
                "period_end": end_date,
                "filtered_by_user": user_id
            }
            
        except Exception as e:
            logger.error(f"Error getting user usage: {e}")
            # Return empty result on error
            return {
                "users": [],
                "total_users": 0,
                "total_requests": 0,
                "total_cost": None,
                "period_start": start_date,
                "period_end": end_date,
                "filtered_by_user": user_id
            }
    
    async def get_sessions(
        self,
        organization_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        include_active: bool = True,
        include_completed: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get session analytics for an organization
        
        Args:
            organization_id: Organization ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            user_id: Optional user ID filter
            include_active: Whether to include active sessions
            include_completed: Whether to include completed sessions
            limit: Maximum number of results to return
            offset: Pagination offset
            
        Returns:
            Dictionary with session analytics data
        """
        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        logger.info(f"Getting sessions for org {organization_id} from {start_date} to {end_date}")
        
        try:
            # Build query parameters
            params = {
                "org_id": organization_id,
                "start_date": start_date,
                "end_date": end_date,
                "limit": limit,
                "offset": offset
            }
            
            # Add user filter if provided
            user_filter = ""
            if user_id is not None:
                user_filter = "AND u.user_id = :user_id"
                params["user_id"] = user_id
            
            # Add session status filter
            status_conditions = []
            if include_active:
                status_conditions.append("s.ended_at IS NULL")
            if include_completed:
                status_conditions.append("s.ended_at IS NOT NULL")
            
            status_filter = ""
            if status_conditions:
                status_filter = f"AND ({' OR '.join(status_conditions)})"
            
            # Build query for sessions
            sessions_query = f"""
            SELECT 
                s.session_id,
                u.user_id as external_user_id,
                s.started_at,
                s.ended_at,
                CASE 
                    WHEN s.ended_at IS NOT NULL THEN 
                        EXTRACT(EPOCH FROM (s.ended_at - s.started_at)) / 60.0
                    ELSE 
                        EXTRACT(EPOCH FROM (NOW() - s.started_at)) / 60.0
                END as duration_minutes,
                COUNT(r.id) as request_count,
                SUM(ul.total_tokens) as total_tokens,
                SUM(ul.cost_usd) as total_cost,
                array_agg(DISTINCT r.model) FILTER (WHERE r.model IS NOT NULL) as models_used,
                CASE WHEN s.ended_at IS NULL THEN TRUE ELSE FALSE END as is_active
            FROM 
                sessions s
            JOIN 
                users u ON s.user_id = u.id
            LEFT JOIN 
                requests r ON s.id = r.session_id
            LEFT JOIN 
                usage_logs ul ON r.id = ul.request_id
            WHERE 
                u.organization_id = :org_id
                AND s.started_at BETWEEN :start_date AND :end_date
                {user_filter}
                {status_filter}
            GROUP BY 
                s.id, s.session_id, u.user_id, s.started_at, s.ended_at
            ORDER BY 
                s.started_at DESC
            LIMIT :limit OFFSET :offset
            """
            
            # Execute query
            sessions_result = await self.db.execute(text(sessions_query), params)
            session_rows = sessions_result.fetchall()
            
            # Get summary statistics
            stats_query = f"""
            SELECT 
                COUNT(DISTINCT s.id) as total_sessions,
                COUNT(DISTINCT CASE WHEN s.ended_at IS NULL THEN s.id END) as active_sessions,
                COUNT(r.id) as total_requests,
                SUM(ul.cost_usd) as total_cost,
                AVG(CASE 
                    WHEN s.ended_at IS NOT NULL THEN 
                        EXTRACT(EPOCH FROM (s.ended_at - s.started_at)) / 60.0
                    ELSE 
                        NULL
                END) as avg_session_duration
            FROM 
                sessions s
            JOIN 
                users u ON s.user_id = u.id
            LEFT JOIN 
                requests r ON s.id = r.session_id
            LEFT JOIN 
                usage_logs ul ON r.id = ul.request_id
            WHERE 
                u.organization_id = :org_id
                AND s.started_at BETWEEN :start_date AND :end_date
                {user_filter}
            """
            
            stats_result = await self.db.execute(text(stats_query), params)
            stats_row = stats_result.fetchone()
            
            # Format response
            sessions = []
            for row in session_rows:
                # Handle PostgreSQL arrays
                models_used = []
                if row.models_used:
                    if isinstance(row.models_used, list):
                        models_used = row.models_used
                    else:
                        try:
                            models_used = row.models_used.strip('{}').split(',')
                        except (AttributeError, ValueError):
                            models_used = []
                
                session_data = {
                    "session_id": row.session_id,
                    "user_id": row.external_user_id,
                    "started_at": row.started_at,
                    "ended_at": row.ended_at,
                    "duration_minutes": float(row.duration_minutes) if row.duration_minutes is not None else None,
                    "request_count": row.request_count or 0,
                    "total_tokens": row.total_tokens,
                    "total_cost": float(row.total_cost) if row.total_cost is not None else None,
                    "models_used": models_used,
                    "is_active": row.is_active
                }
                sessions.append(session_data)
            
            return {
                "sessions": sessions,
                "total_sessions": stats_row.total_sessions if stats_row else 0,
                "active_sessions": stats_row.active_sessions if stats_row else 0,
                "total_requests": stats_row.total_requests if stats_row else 0,
                "total_cost": float(stats_row.total_cost) if stats_row and stats_row.total_cost is not None else None,
                "avg_session_duration": float(stats_row.avg_session_duration) if stats_row and stats_row.avg_session_duration is not None else None,
                "period_start": start_date,
                "period_end": end_date,
                "filtered_by_user": user_id
            }
            
        except Exception as e:
            logger.error(f"Error getting sessions: {e}")
            # Return empty result on error
            return {
                "sessions": [],
                "total_sessions": 0,
                "active_sessions": 0,
                "total_requests": 0,
                "total_cost": None,
                "avg_session_duration": None,
                "period_start": start_date,
                "period_end": end_date,
                "filtered_by_user": user_id
            }
    
    async def get_persona_usage(
        self,
        organization_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        include_inactive: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get usage statistics by persona
        
        Args:
            organization_id: Organization ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            user_id: Optional user ID filter
            include_inactive: Whether to include inactive personas
            limit: Maximum number of results to return
            offset: Pagination offset
            
        Returns:
            Dictionary with persona usage statistics
        """
        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        logger.info(f"Getting persona usage for org {organization_id} from {start_date} to {end_date}")
        
        try:
            # Build query parameters
            params = {
                "org_id": organization_id,
                "start_date": start_date,
                "end_date": end_date,
                "limit": limit,
                "offset": offset
            }
            
            # Add user filter if provided
            user_filter = ""
            if user_id is not None:
                user_filter = "AND u.user_id = :user_id"
                params["user_id"] = user_id
            
            # Add active filter if needed
            active_filter = ""
            if not include_inactive:
                active_filter = "AND p.is_active = TRUE"
            
            # Build query for persona usage
            persona_query = f"""
            SELECT 
                p.id as persona_id,
                p.name,
                p.description,
                u2.user_id as restricted_user_id,
                COUNT(r.id) as request_count,
                COUNT(CASE WHEN r.status = 'completed' THEN 1 END) as success_count,
                COUNT(CASE WHEN r.status = 'failed' THEN 1 END) as failure_count,
                ROUND(COUNT(CASE WHEN r.status = 'completed' THEN 1 END)::numeric / 
                      NULLIF(COUNT(r.id), 0)::numeric * 100, 1) as success_rate,
                SUM(ul.input_tokens) as input_tokens,
                SUM(ul.output_tokens) as output_tokens,
                SUM(ul.total_tokens) as total_tokens,
                SUM(ul.cost_usd) as total_cost,
                AVG(EXTRACT(EPOCH FROM (r.completed_at - r.created_at))) as avg_response_time,
                MAX(r.created_at) as last_used_at,
                array_agg(DISTINCT r.model) FILTER (WHERE r.model IS NOT NULL) as models_used,
                p.is_active
            FROM 
                personas p
            LEFT JOIN 
                users u2 ON p.user_id = u2.id
            LEFT JOIN 
                requests r ON p.id = r.persona_id AND r.created_at BETWEEN :start_date AND :end_date
            LEFT JOIN 
                users u ON r.user_id = u.id
            LEFT JOIN 
                usage_logs ul ON r.id = ul.request_id
            WHERE 
                p.organization_id = :org_id
                {active_filter}
                {user_filter}
            GROUP BY 
                p.id, p.name, p.description, u2.user_id, p.is_active
            ORDER BY 
                request_count DESC NULLS LAST, p.name ASC
            LIMIT :limit OFFSET :offset
            """
            
            # Execute query
            persona_result = await self.db.execute(text(persona_query), params)
            persona_rows = persona_result.fetchall()
            
            # Get total counts
            counts_query = f"""
            SELECT 
                COUNT(DISTINCT p.id) as total_personas,
                COUNT(r.id) as total_requests,
                SUM(ul.cost_usd) as total_cost
            FROM 
                personas p
            LEFT JOIN 
                requests r ON p.id = r.persona_id AND r.created_at BETWEEN :start_date AND :end_date
            LEFT JOIN 
                users u ON r.user_id = u.id
            LEFT JOIN 
                usage_logs ul ON r.id = ul.request_id
            WHERE 
                p.organization_id = :org_id
                {active_filter}
                {user_filter}
            """
            
            counts_result = await self.db.execute(text(counts_query), params)
            counts_row = counts_result.fetchone()
            
            # Format response
            personas = []
            for row in persona_rows:
                # Handle NULL values and type conversions
                models_used = []
                if row.models_used:
                    # Convert PostgreSQL array to Python list
                    if isinstance(row.models_used, list):
                        models_used = row.models_used
                    else:
                        # Handle string representation of array if needed
                        try:
                            models_used = row.models_used.strip('{}').split(',')
                        except (AttributeError, ValueError):
                            models_used = []
                
                persona_data = {
                    "persona_id": str(row.persona_id),
                    "name": row.name,
                    "description": row.description,
                    "user_id": row.restricted_user_id,
                    "request_count": row.request_count or 0,
                    "success_count": row.success_count or 0,
                    "failure_count": row.failure_count or 0,
                    "success_rate": float(row.success_rate) if row.success_rate is not None else 0.0,
                    "input_tokens": row.input_tokens,
                    "output_tokens": row.output_tokens,
                    "total_tokens": row.total_tokens,
                    "total_cost": float(row.total_cost) if row.total_cost is not None else None,
                    "avg_response_time": float(row.avg_response_time) if row.avg_response_time is not None else None,
                    "last_used_at": row.last_used_at,
                    "models_used": models_used,
                    "is_active": row.is_active
                }
                personas.append(persona_data)
            
            return {
                "personas": personas,
                "total_personas": counts_row.total_personas if counts_row else 0,
                "total_requests": counts_row.total_requests if counts_row else 0,
                "total_cost": float(counts_row.total_cost) if counts_row and counts_row.total_cost is not None else None,
                "period_start": start_date,
                "period_end": end_date,
                "filtered_by_user": user_id,
                "include_inactive": include_inactive
            }
            
        except Exception as e:
            logger.error(f"Error getting persona usage: {e}")
            # Return empty result on error
            return {
                "personas": [],
                "total_personas": 0,
                "total_requests": 0,
                "total_cost": None,
                "period_start": start_date,
                "period_end": end_date,
                "filtered_by_user": user_id,
                "include_inactive": include_inactive
            }
