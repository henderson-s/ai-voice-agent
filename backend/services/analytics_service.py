"""
Analytics service for aggregating and querying call analytics data.

Provides clean interfaces for retrieving analytics metrics,
events, and cost breakdowns from the database.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from supabase import Client

logger = logging.getLogger(__name__)


class AnalyticsServiceError(Exception):
    """Base exception for analytics service errors."""
    pass


class AnalyticsService:
    """
    Service for analytics data aggregation and retrieval.
    
    Provides DRY methods for common analytics queries
    with proper error handling and logging.
    """

    def __init__(self, db_client: Client):
        """
        Initialize analytics service.
        
        Args:
            db_client: Supabase client instance
        """
        self.db = db_client
        logger.debug("Analytics service initialized")

    def get_summary_metrics(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get high-level summary metrics for a user.
        
        Args:
            user_id: User ID to filter by
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary with summary metrics
            
        Raises:
            AnalyticsServiceError: If query fails
        """
        try:
            logger.info(f"Fetching summary metrics for user {user_id}")
            
            # Build date filter
            date_filter = self._build_date_filter(start_date, end_date)
            
            # Get total calls
            calls_query = self.db.table("calls")\
                .select("id", count="exact")\
                .eq("user_id", user_id)
            
            if date_filter:
                calls_query = calls_query.gte("created_at", date_filter["start"])\
                    .lte("created_at", date_filter["end"])
            
            total_calls = calls_query.execute().count or 0
            
            # Get user's call IDs
            user_calls = self.db.table("calls")\
                .select("id")\
                .eq("user_id", user_id)\
                .execute()
            
            call_ids = [call["id"] for call in user_calls.data]
            
            # Get analytics for those calls
            if call_ids:
                analytics_query = self.db.table("call_analytics")\
                    .select("*")\
                    .in_("call_id", call_ids)
                
                analytics_data = analytics_query.execute().data
            else:
                analytics_data = []
            
            # Calculate aggregates
            metrics = self._calculate_aggregates(analytics_data)
            metrics["total_calls"] = total_calls
            
            logger.debug(f"Summary metrics calculated: {total_calls} calls")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get summary metrics: {e}", exc_info=True)
            raise AnalyticsServiceError(f"Summary metrics query failed: {str(e)}")

    def get_call_analytics(self, call_id: str) -> Optional[Dict[str, Any]]:
        """
        Get analytics for a specific call.
        
        Args:
            call_id: Call ID to retrieve analytics for
            
        Returns:
            Analytics data dictionary or None if not found
            
        Raises:
            AnalyticsServiceError: If query fails
        """
        try:
            logger.debug(f"Fetching analytics for call {call_id}")
            
            response = self.db.table("call_analytics")\
                .select("*")\
                .eq("call_id", call_id)\
                .execute()
            
            if not response.data:
                logger.warning(f"No analytics found for call {call_id}")
                return None
            
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Failed to get call analytics: {e}", exc_info=True)
            raise AnalyticsServiceError(f"Call analytics query failed: {str(e)}")

    def get_call_events(
        self,
        call_id: str,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get events for a specific call.
        
        Args:
            call_id: Call ID to retrieve events for
            event_type: Optional event type filter
            limit: Maximum number of events to return
            
        Returns:
            List of event dictionaries
            
        Raises:
            AnalyticsServiceError: If query fails
        """
        try:
            logger.debug(f"Fetching events for call {call_id}")
            
            query = self.db.table("analytics_events")\
                .select("*")\
                .eq("call_id", call_id)\
                .order("timestamp", desc=False)\
                .limit(limit)
            
            if event_type:
                query = query.eq("event_type", event_type)
            
            response = query.execute()
            
            logger.debug(f"Retrieved {len(response.data)} events")
            return response.data
            
        except Exception as e:
            logger.error(f"Failed to get call events: {e}", exc_info=True)
            raise AnalyticsServiceError(f"Call events query failed: {str(e)}")

    def get_cost_breakdown(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get cost breakdown for a user's calls.
        
        Args:
            user_id: User ID to filter by
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary with cost breakdown
            
        Raises:
            AnalyticsServiceError: If query fails
        """
        try:
            logger.info(f"Fetching cost breakdown for user {user_id}")
            
            # Get user's calls
            calls_query = self.db.table("calls")\
                .select("id")\
                .eq("user_id", user_id)
            
            date_filter = self._build_date_filter(start_date, end_date)
            if date_filter:
                calls_query = calls_query.gte("created_at", date_filter["start"])\
                    .lte("created_at", date_filter["end"])
            
            call_ids = [call["id"] for call in calls_query.execute().data]
            
            if not call_ids:
                return self._empty_cost_breakdown()
            
            # Get analytics for those calls
            analytics = self.db.table("call_analytics")\
                .select("llm_cost, tts_cost, stt_cost, total_cost")\
                .in_("call_id", call_ids)\
                .execute().data
            
            # Calculate totals
            breakdown = {
                "llm_cost": sum(Decimal(str(a.get("llm_cost", 0))) for a in analytics),
                "tts_cost": sum(Decimal(str(a.get("tts_cost", 0))) for a in analytics),
                "stt_cost": sum(Decimal(str(a.get("stt_cost", 0))) for a in analytics),
                "total_cost": sum(Decimal(str(a.get("total_cost", 0))) for a in analytics),
                "call_count": len(call_ids),
            }
            
            # Convert to float for JSON serialization
            breakdown = {k: float(v) if isinstance(v, Decimal) else v 
                        for k, v in breakdown.items()}
            
            logger.debug(f"Cost breakdown calculated: ${breakdown['total_cost']:.4f}")
            return breakdown
            
        except Exception as e:
            logger.error(f"Failed to get cost breakdown: {e}", exc_info=True)
            raise AnalyticsServiceError(f"Cost breakdown query failed: {str(e)}")

    def get_outcome_distribution(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """
        Get distribution of call outcomes.
        
        Args:
            user_id: User ID to filter by
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dictionary mapping outcomes to counts
        """
        try:
            logger.debug(f"Fetching outcome distribution for user {user_id}")
            
            # Get user's calls with results
            query = self.db.table("call_results")\
                .select("call_outcome, call_id")\
                .in_("call_id",
                     self.db.table("calls").select("id").eq("user_id", user_id).execute().data
                )
            
            results = query.execute().data
            
            # Count outcomes
            distribution: Dict[str, int] = {}
            for result in results:
                outcome = result.get("call_outcome", "unknown")
                distribution[outcome] = distribution.get(outcome, 0) + 1
            
            logger.debug(f"Outcome distribution: {distribution}")
            return distribution
            
        except Exception as e:
            logger.error(f"Failed to get outcome distribution: {e}", exc_info=True)
            return {}

    def _build_date_filter(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> Optional[Dict[str, str]]:
        """
        Build date filter for queries.
        
        Args:
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Dictionary with start and end ISO strings, or None
        """
        if not start_date and not end_date:
            return None
        
        start = start_date or (datetime.utcnow() - timedelta(days=30))
        end = end_date or datetime.utcnow()
        
        return {
            "start": start.isoformat(),
            "end": end.isoformat(),
        }

    def _calculate_aggregates(self, analytics_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate aggregate metrics from analytics data.
        
        Args:
            analytics_data: List of analytics records
            
        Returns:
            Dictionary with aggregated metrics
        """
        if not analytics_data:
            return self._empty_aggregates()
        
        total_duration = sum(a.get("total_duration_ms", 0) for a in analytics_data)
        total_interruptions = sum(a.get("interruption_count", 0) for a in analytics_data)
        total_tokens = sum(a.get("tokens_spent", 0) for a in analytics_data)
        total_cost = sum(Decimal(str(a.get("total_cost", 0))) for a in analytics_data)
        
        return {
            "average_duration_seconds": total_duration / len(analytics_data) / 1000,
            "total_interruptions": total_interruptions,
            "average_interruptions": total_interruptions / len(analytics_data),
            "total_tokens": total_tokens,
            "total_cost": float(total_cost),
            "analyzed_calls": len(analytics_data),
        }

    def _empty_aggregates(self) -> Dict[str, Any]:
        """Return empty aggregate metrics."""
        return {
            "average_duration_seconds": 0,
            "total_interruptions": 0,
            "average_interruptions": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "analyzed_calls": 0,
        }

    def _empty_cost_breakdown(self) -> Dict[str, Any]:
        """Return empty cost breakdown."""
        return {
            "llm_cost": 0.0,
            "tts_cost": 0.0,
            "stt_cost": 0.0,
            "total_cost": 0.0,
            "call_count": 0,
        }


def get_analytics_service(db_client: Client) -> AnalyticsService:
    """
    Dependency injection function for FastAPI routes.
    
    Args:
        db_client: Supabase client instance
        
    Returns:
        AnalyticsService instance
    """
    return AnalyticsService(db_client)

