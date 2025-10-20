"""
Analytics API routes for call metrics and cost tracking.

Provides endpoints for retrieving analytics data captured
by RTVI observers during Pipecat voice calls.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from backend.database import Database, get_db
from backend.services.analytics_service import AnalyticsService, get_analytics_service
from backend.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


# ============================================
# Request/Response Models
# ============================================

class DateRangeParams(BaseModel):
    """Query parameters for date range filtering."""
    start_date: Optional[str] = None
    end_date: Optional[str] = None


# ============================================
# Analytics Endpoints
# ============================================

@router.get("/summary")
async def get_analytics_summary(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """
    Get high-level analytics summary for the current user.
    
    Returns aggregated metrics including:
    - Total calls
    - Average duration
    - Total interruptions
    - Token usage
    - Total costs
    """
    try:
        logger.info(f"Fetching analytics summary for user {current_user.id}")
        
        # Parse dates if provided
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        analytics_service = get_analytics_service(db.client)
        summary = analytics_service.get_summary_metrics(
            user_id=current_user.id,
            start_date=start,
            end_date=end,
        )
        
        logger.info(f"✅ Summary retrieved: {summary.get('total_calls', 0)} calls")
        return summary
        
    except ValueError as e:
        logger.warning(f"Invalid date format: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to get analytics summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics summary"
        )


@router.get("/cost-breakdown")
async def get_cost_breakdown(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """
    Get detailed cost breakdown by service (LLM, TTS, STT).
    
    Returns:
    - LLM costs (OpenAI)
    - TTS costs (Cartesia)
    - STT costs (Deepgram)
    - Total cost
    - Number of calls
    """
    try:
        logger.info(f"Fetching cost breakdown for user {current_user.id}")
        
        # Parse dates if provided
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        analytics_service = get_analytics_service(db.client)
        breakdown = analytics_service.get_cost_breakdown(
            user_id=current_user.id,
            start_date=start,
            end_date=end,
        )
        
        logger.info(f"✅ Cost breakdown retrieved: ${breakdown.get('total_cost', 0):.4f}")
        return breakdown
        
    except ValueError as e:
        logger.warning(f"Invalid date format: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to get cost breakdown: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cost breakdown"
        )


@router.get("/outcomes")
async def get_outcome_distribution(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """
    Get distribution of call outcomes.
    
    Returns counts for each outcome type:
    - in_transit_update
    - arrival_confirmation
    - emergency_escalation
    - etc.
    """
    try:
        logger.info(f"Fetching outcome distribution for user {current_user.id}")
        
        # Parse dates if provided
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        analytics_service = get_analytics_service(db.client)
        distribution = analytics_service.get_outcome_distribution(
            user_id=current_user.id,
            start_date=start,
            end_date=end,
        )
        
        logger.info(f"✅ Outcome distribution retrieved")
        return distribution
        
    except ValueError as e:
        logger.warning(f"Invalid date format: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to get outcome distribution: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve outcome distribution"
        )


@router.get("/call/{call_id}")
async def get_call_analytics(
    call_id: str,
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """
    Get detailed analytics for a specific call.
    
    Returns:
    - Duration
    - Interruption count
    - Token usage
    - Costs breakdown
    - Additional metrics
    """
    try:
        logger.info(f"Fetching analytics for call {call_id}")
        
        # Verify call belongs to user
        call_response = db.client.table("calls")\
            .select("id")\
            .eq("id", call_id)\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not call_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Call not found"
            )
        
        analytics_service = get_analytics_service(db.client)
        analytics = analytics_service.get_call_analytics(call_id)
        
        if not analytics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analytics not available for this call"
            )
        
        logger.info(f"✅ Analytics retrieved for call {call_id}")
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get call analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve call analytics"
        )


@router.get("/events/{call_id}")
async def get_call_events(
    call_id: str,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(100, description="Maximum number of events", ge=1, le=1000),
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """
    Get event timeline for a specific call.
    
    Returns chronological list of events:
    - User interruptions
    - Keyword detections
    - Sentiment shifts
    - Transcription events
    - LLM interactions
    """
    try:
        logger.info(f"Fetching events for call {call_id}")
        
        # Verify call belongs to user
        call_response = db.client.table("calls")\
            .select("id")\
            .eq("id", call_id)\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not call_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Call not found"
            )
        
        analytics_service = get_analytics_service(db.client)
        events = analytics_service.get_call_events(
            call_id=call_id,
            event_type=event_type,
            limit=limit,
        )
        
        logger.info(f"✅ Retrieved {len(events)} events for call {call_id}")
        return events
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get call events: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve call events"
        )


@router.get("/metrics")
async def get_metrics_overview(
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """
    Get comprehensive metrics overview for dashboards.
    
    Combines summary, costs, and outcome data into
    a single response for efficient dashboard rendering.
    """
    try:
        logger.info(f"Fetching metrics overview for user {current_user.id}")
        
        analytics_service = get_analytics_service(db.client)
        
        # Get all metrics in parallel would be better, but keeping it simple
        summary = analytics_service.get_summary_metrics(current_user.id)
        costs = analytics_service.get_cost_breakdown(current_user.id)
        outcomes = analytics_service.get_outcome_distribution(current_user.id)
        
        overview = {
            "summary": summary,
            "costs": costs,
            "outcomes": outcomes,
        }
        
        logger.info(f"✅ Metrics overview retrieved")
        return overview
        
    except Exception as e:
        logger.error(f"Failed to get metrics overview: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve metrics overview"
        )

