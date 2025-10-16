from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List
import logging
from backend.models.call import CallCreate, WebCallCreate, CallResponse, WebCallResponse
from backend.database import Database, get_db
from backend.services.retell import RetellService, get_retell_service
from backend.utils.auth import get_current_user
from backend.utils.database_helpers import get_call_by_id, get_agent_by_id, update_call_basic_info
from backend.utils.call_processor import process_call_details, build_results_data, save_or_update_results
from backend.utils.webhook_handler import extract_call_id_from_webhook, process_webhook_event
from backend.utils.agent_helpers import ensure_agent_has_retell_id, build_call_metadata, build_call_record
from backend.constants.call_status import WEBHOOK_STATUS_MAPPING, CallStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/calls", tags=["calls"])


@router.post("/phone", response_model=CallResponse, status_code=status.HTTP_201_CREATED)
async def create_phone_call(
    call_data: CallCreate,
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db),
    retell: RetellService=Depends(get_retell_service)
):
    """Create a phone call using Retell AI"""
    # Get and validate agent
    agent = get_agent_by_id(db.client, call_data.agent_configuration_id, current_user.id)

    # Ensure agent has Retell ID
    retell_agent_id = await ensure_agent_has_retell_id(db.client, agent, retell)

    # Build metadata and initiate call
    metadata = build_call_metadata(call_data.driver_name, call_data.load_number)
    retell_call = await retell.initiate_call(retell_agent_id, call_data.phone_number, metadata)

    # Build and insert call record
    call_record = build_call_record(
        user_id=current_user.id,
        agent_configuration_id=call_data.agent_configuration_id,
        call_type="phone",
        driver_name=call_data.driver_name,
        phone_number=call_data.phone_number,
        load_number=call_data.load_number,
        retell_call_id=retell_call.get("call_id")
    )

    response = db.client.table("calls").insert(call_record).execute()
    return response.data[0]


@router.post("/web", response_model=WebCallResponse, status_code=status.HTTP_201_CREATED)
async def create_web_call(
    call_data: WebCallCreate,
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db),
    retell: RetellService=Depends(get_retell_service)
):
    """Create a web call (browser-based) using Retell AI"""
    # Get and validate agent
    agent = get_agent_by_id(db.client, call_data.agent_configuration_id, current_user.id)

    # Ensure agent has Retell ID
    retell_agent_id = await ensure_agent_has_retell_id(db.client, agent, retell)

    # Build metadata and create web call
    metadata = build_call_metadata(call_data.driver_name, call_data.load_number)
    retell_call = await retell.create_web_call(retell_agent_id, metadata)

    # Build and insert call record
    call_record = build_call_record(
        user_id=current_user.id,
        agent_configuration_id=call_data.agent_configuration_id,
        call_type="web",
        driver_name=call_data.driver_name,
        phone_number="WEB_CALL",
        load_number=call_data.load_number,
        retell_call_id=retell_call.get("call_id")
    )

    db.client.table("calls").insert(call_record).execute()

    return WebCallResponse(
        access_token=retell_call["access_token"],
        call_id=retell_call["call_id"]
    )


@router.get("", response_model=List[CallResponse])
async def list_calls(
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db)
):
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
    call = get_call_by_id(db.client, call_id, current_user.id)

    if not call:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call not found")

    return call


@router.get("/{call_id}/full")
async def get_call_full_details(
    call_id: str,
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db)
):
    """Get full call details including transcript and structured results"""
    # Get the call
    call_data = get_call_by_id(db.client, call_id, current_user.id)

    if not call_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call not found")

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

    return {
        "call": call_data,
        "transcript": transcript_response.data[0] if transcript_response.data else None,
        "results": results_response.data[0] if results_response.data else None
    }


@router.delete("/{call_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_call(
    call_id: str,
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db)
):
    response = db.client.table("calls")\
        .delete()\
        .eq("id", call_id)\
        .eq("user_id", current_user.id)\
        .execute()

    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call not found")


@router.post("/{call_id}/refresh", response_model=CallResponse)
async def refresh_call_details(
    call_id: str,
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db),
    retell: RetellService=Depends(get_retell_service)
):
    """Manually fetch and update call details from Retell AI"""
    # Get the call from database
    db_call = get_call_by_id(db.client, call_id, current_user.id)

    if not db_call:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call not found")

    retell_call_id = db_call.get("retell_call_id")

    if not retell_call_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No Retell call ID associated")

    # Fetch details from Retell AI
    logger.info(f"Manually fetching details for call: {retell_call_id}")
    try:
        call_details = await retell.get_call_details(retell_call_id)
    except Exception as e:
        logger.error(f"Error fetching from Retell API: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch from Retell AI: {str(e)}"
        )

    if not call_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call details not found in Retell AI"
        )

    logger.info(f"Fetched call details: {call_details}")

    # Use service key client to bypass RLS
    from backend.database import get_supabase_client
    service_client = get_supabase_client()

    try:
        # Update call basic info
        update_call_basic_info(service_client, db_call["id"], CallStatus.COMPLETED, call_details)

        # Process transcript and results
        process_call_details(service_client, db_call["id"], call_details)

        # Fetch and return updated call
        updated = service_client.table("calls")\
            .select("*")\
            .eq("id", db_call["id"])\
            .execute()

        return updated.data[0]

    except Exception as e:
        logger.error(f"Error updating call: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update call: {str(e)}"
        )


# Webhook endpoint for Retell AI call status updates (no auth required for webhooks)
@router.post("/webhook")
async def webhook_handler(request: Request):
    """
    Handle webhook events from Retell AI.

    This endpoint receives notifications about call status changes and processes them.
    Uses service key to bypass RLS for webhook access.
    """
    # Create database instance using service key for webhooks (bypass RLS)
    from backend.database import get_supabase_client
    db_client = get_supabase_client()

    try:
        body = await request.json()
        logger.info(f"Received webhook: {body}")

        # Extract event type and call ID from payload
        event_type = body.get("event_type") or body.get("event")
        call_id = extract_call_id_from_webhook(body)

        if not call_id:
            logger.error(f"No call_id in webhook payload. Body: {body}")
            return {"status": "error", "message": "No call_id provided"}

        # Process the webhook event
        result = await process_webhook_event(db_client, event_type, call_id)
        return result

    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

