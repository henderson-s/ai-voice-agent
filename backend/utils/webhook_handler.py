"""
Webhook event processing utilities.
Extracted to reduce complexity in route handlers.
"""

import logging
from typing import Dict, Any, Optional
from supabase import Client
from backend.services.retell import RetellService
from backend.utils.database_helpers import update_call_basic_info
from backend.utils.call_processor import process_call_details, build_results_data, save_or_update_results
from backend.constants.call_status import WEBHOOK_STATUS_MAPPING

logger = logging.getLogger(__name__)


def extract_call_id_from_webhook(body: Dict[str, Any]) -> Optional[str]:
    """
    Extract call ID from webhook payload.

    Args:
        body: Webhook payload

    Returns:
        Call ID or None if not found
    """
    # Try different ways to get call_id
    if body.get("call_id"):
        return body["call_id"]
    elif body.get("call") and body["call"].get("call_id"):
        return body["call"]["call_id"]

    return None


async def handle_call_ended_event(
    db_client: Client,
    db_call: Dict[str, Any],
    call_id: str
) -> None:
    """
    Handle call_ended webhook event.

    Fetches full call details from Retell AI and saves transcript and results.

    Args:
        db_client: Supabase client instance
        db_call: Call record from database
        call_id: Retell call ID
    """
    try:
        retell = RetellService()
        call_details = await retell.get_call_details(call_id)

        if call_details:
            # Update call basic info
            update_call_basic_info(
                db_client,
                db_call["id"],
                "completed",
                call_details
            )

            # Process transcript and results
            process_call_details(db_client, db_call["id"], call_details)

            logger.info(f"✅ Successfully processed call_ended event for {call_id}")
        else:
            logger.warning(f"Could not fetch call details for {call_id}")
            # Still update status
            update_call_basic_info(db_client, db_call["id"], "completed")

    except Exception as e:
        logger.error(f"Error processing call_ended: {e}", exc_info=True)
        raise


async def handle_call_analyzed_event(
    db_client: Client,
    db_call: Dict[str, Any],
    call_id: str
) -> None:
    """
    Handle call_analyzed webhook event.

    Updates analysis results from Retell AI.

    Args:
        db_client: Supabase client instance
        db_call: Call record from database
        call_id: Retell call ID
    """
    try:
        retell = RetellService()
        call_details = await retell.get_call_details(call_id)

        if call_details and call_details.get("call_analysis"):
            call_analysis = call_details["call_analysis"]
            results_data = build_results_data(db_call["id"], call_analysis)
            save_or_update_results(db_client, db_call["id"], results_data)
            logger.info(f"✅ Updated analysis for call {db_call['id']}")

    except Exception as e:
        logger.error(f"Error processing call_analyzed: {e}", exc_info=True)


def handle_simple_status_event(
    db_client: Client,
    db_call: Dict[str, Any],
    new_status: str
) -> None:
    """
    Handle simple status change events (call_started, call_failed).

    Args:
        db_client: Supabase client instance
        db_call: Call record from database
        new_status: New status to set
    """
    try:
        update_call_basic_info(db_client, db_call["id"], new_status)
        logger.info(f"✅ Updated call {db_call['id']} status to {new_status}")
    except Exception as e:
        logger.error(f"Error updating status: {e}", exc_info=True)
        raise


async def process_webhook_event(
    db_client: Client,
    event_type: str,
    call_id: str
) -> Dict[str, str]:
    """
    Process webhook event from Retell AI.

    Args:
        db_client: Supabase client instance (with service key, no RLS)
        event_type: Type of webhook event
        call_id: Retell call ID

    Returns:
        Response dictionary with status

    Raises:
        Exception: If call not found or processing fails
    """
    # Find the call in database by retell_call_id
    call_response = db_client.table("calls")\
        .select("*")\
        .eq("retell_call_id", call_id)\
        .execute()

    if not call_response.data:
        logger.warning(f"Call not found in database: {call_id}")
        return {"status": "error", "message": "Call not found"}

    db_call = call_response.data[0]

    # Get new status from mapping
    new_status = WEBHOOK_STATUS_MAPPING.get(event_type)

    if not new_status:
        logger.warning(f"Unknown event type: {event_type}")
        return {"status": "success", "message": "Event type not handled"}

    # Route to appropriate handler based on event type
    if event_type == "call_ended":
        await handle_call_ended_event(db_client, db_call, call_id)
    elif event_type == "call_analyzed":
        await handle_call_analyzed_event(db_client, db_call, call_id)
    else:
        # Simple status change events (call_started, call_failed)
        handle_simple_status_event(db_client, db_call, new_status)

    return {"status": "success"}
