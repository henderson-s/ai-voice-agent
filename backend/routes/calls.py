"""
Call management routes with Pipecat integration.

Handles voice call creation, management, and result processing
using Pipecat AI framework instead of Retell AI.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.models.call import CallCreate, WebCallCreate, CallResponse
from backend.database import Database, get_db
from backend.services.pipecat_manager import get_pipeline_manager, PipecatManagerError
from backend.services.pipecat_service import CallContext, VoiceServiceConfig
from backend.utils.auth import get_current_user
from backend.utils.database_helpers import get_call_by_id, get_agent_by_id
from backend.constants.call_status import CallStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/calls", tags=["calls"])


# ============================================
# Response Models
# ============================================

class PipecatCallResponse(BaseModel):
    """Response for Pipecat call creation."""
    call_id: str
    session_id: str
    status: str


# ============================================
# Call Endpoints
# ============================================

@router.post("/web", response_model=PipecatCallResponse, status_code=status.HTTP_201_CREATED)
async def create_web_call(
    call_data: WebCallCreate,
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db),
):
    """
    Create a web-based voice call using Pipecat.
    
    This endpoint creates a call record and initializes a Pipecat
    pipeline session for browser-based voice calling.
    """
    try:
        logger.info(f"Creating web call for user {current_user.id}")
        
        # Get and validate agent configuration
        agent = get_agent_by_id(db.client, call_data.agent_configuration_id, current_user.id)
        
        # Create call record in database
        call_record = {
            "user_id": current_user.id,
            "agent_configuration_id": call_data.agent_configuration_id,
            "call_type": "web",
            "driver_name": call_data.driver_name,
            "phone_number": "WEB_CALL",
            "load_number": call_data.load_number,
            "status": CallStatus.INITIATED,
        }
        
        response = db.client.table("calls").insert(call_record).execute()
        call = response.data[0]
        
        # Build call context from agent configuration with variable substitution
        initial_greeting = agent["initial_greeting"].replace(
            "{{driver_name}}", call_data.driver_name
        ).replace(
            "{{load_number}}", call_data.load_number
        )
        
        context = CallContext(
            driver_name=call_data.driver_name,
            load_number=call_data.load_number,
            scenario_type=agent.get("scenario_type", "driver_checkin"),
            system_prompt=agent["system_prompt"],
            initial_greeting=initial_greeting,
            emergency_keywords=agent.get("emergency_keywords", [
                "accident", "crash", "emergency", "help", "breakdown", "medical", "injury"
            ]),
        )
        
        # Create voice service config from agent settings
        voice_config = VoiceServiceConfig(
            openai_model="gpt-4",
            cartesia_voice_id=agent.get("voice_id", "a0e99841-438c-4a64-b679-ae501e7d6091"),
            deepgram_model="nova-2",
            language=agent.get("language", "en"),
        )
        
        # Create Pipecat session
        manager = get_pipeline_manager()
        session = await manager.create_session(
            call_id=call["id"],
            user_id=current_user.id,
            agent_id=call_data.agent_configuration_id,
            context=context,
            config=voice_config,
        )
        
        logger.info(f"✅ Web call created: {call['id']}")
        
        return PipecatCallResponse(
            call_id=call["id"],
            session_id=call["id"],  # Using call_id as session_id
            status="initiated",
        )
        
    except PipecatManagerError as e:
        logger.error(f"Pipecat session creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create call session: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to create web call: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create web call: {str(e)}"
        )


@router.get("", response_model=List[CallResponse])
async def list_calls(
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db)
):
    """List all calls for the current user."""
    response = db.client.table("calls")\
        .select("*")\
        .eq("user_id", current_user.id)\
        .order("created_at", desc=True)\
        .limit(100)\
        .execute()
    return response.data


@router.get("/{call_id}", response_model=CallResponse)
async def get_call(
    call_id: str,
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db)
):
    """Get a specific call by ID."""
    call = get_call_by_id(db.client, call_id, current_user.id)
    
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )
    
    return call


@router.get("/{call_id}/full")
async def get_call_full_details(
    call_id: str,
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db)
):
    """
    Get full call details including transcript and structured results.
    """
    # Get the call
    call_data = get_call_by_id(db.client, call_id, current_user.id)
    
    if not call_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )
    
    # Get transcript
    transcript_response = db.client.table("call_transcripts")\
        .select("*")\
        .eq("call_id", call_data["id"])\
        .execute()
    
    # Get results
    results_response = db.client.table("call_results")\
        .select("*")\
        .eq("call_id", call_data["id"])\
        .execute()
    
    # Get analytics
    analytics_response = db.client.table("call_analytics")\
        .select("*")\
        .eq("call_id", call_data["id"])\
        .execute()
    
    return {
        "call": call_data,
        "transcript": transcript_response.data[0] if transcript_response.data else None,
        "results": results_response.data[0] if results_response.data else None,
        "analytics": analytics_response.data[0] if analytics_response.data else None,
    }


@router.delete("/{call_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_call(
    call_id: str,
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db)
):
    """Delete a call and all associated data."""
    response = db.client.table("calls")\
        .delete()\
        .eq("id", call_id)\
        .eq("user_id", current_user.id)\
        .execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )


@router.post("/{call_id}/end", response_model=CallResponse)
async def end_call(
    call_id: str,
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db),
):
    """
    End an active call session.
    
    This stops the Pipecat pipeline and processes final results.
    """
    try:
        logger.info(f"Ending call {call_id}")
        
        # Verify call belongs to user
        call = get_call_by_id(db.client, call_id, current_user.id)
        if not call:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Call not found"
            )
        
        # End the Pipecat session
        manager = get_pipeline_manager()
        await manager.end_session(call_id)
        
        # Update call status
        updated = db.client.table("calls")\
            .update({"status": CallStatus.COMPLETED})\
            .eq("id", call_id)\
            .execute()
        
        logger.info(f"✅ Call {call_id} ended successfully")
        return updated.data[0]
        
    except Exception as e:
        logger.error(f"Failed to end call: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end call: {str(e)}"
        )


@router.get("/sessions/active")
async def get_active_sessions(
    current_user=Depends(get_current_user),
):
    """
    Get count of active call sessions.
    
    Useful for monitoring system load.
    """
    try:
        manager = get_pipeline_manager()
        count = manager.get_session_count()
        
        return {
            "active_sessions": count,
            "user_id": current_user.id,
        }
        
    except Exception as e:
        logger.error(f"Failed to get active sessions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve active sessions"
        )
