"""
Utility functions for processing call data from Retell AI.
Extracted to eliminate code duplication in routes.
"""

import logging
from typing import Dict, Any, Optional
from supabase import Client

logger = logging.getLogger(__name__)


def build_results_data(
    call_id: str,
    call_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build structured results data from Retell's call analysis.

    This function eliminates 48 lines of duplicate code that appeared
    twice in routes/calls.py (lines 355-376 and 520-540).

    Args:
        call_id: Database ID of the call
        call_analysis: Analysis data from Retell AI

    Returns:
        Dictionary containing structured results ready for database insertion
    """
    # Retell returns our custom analysis inside custom_analysis_data
    custom_analysis = call_analysis.get("custom_analysis_data", {})

    # If custom_analysis_data exists, use it; otherwise fall back to call_analysis
    analysis_source = custom_analysis if custom_analysis else call_analysis

    # Determine scenario type based on presence of emergency fields
    is_emergency = analysis_source.get("is_emergency", False)
    scenario_type = "emergency_protocol" if is_emergency else "driver_checkin"

    # Build base results data
    results_data = {
        "call_id": call_id,
        "scenario_type": scenario_type,
        "is_emergency": is_emergency,
        "call_summary": call_analysis.get("call_summary", analysis_source.get("call_summary", "")),
        "analysis_data": call_analysis,
    }

    # Add scenario-specific fields from Retell's extraction
    if not is_emergency:
        # Normal check-in fields - direct mapping
        results_data.update({
            "call_outcome": analysis_source.get("call_outcome"),
            "driver_status": analysis_source.get("driver_status"),
            "current_location": analysis_source.get("current_location"),
            "eta": analysis_source.get("eta"),
            "delay_reason": analysis_source.get("delay_reason"),
            "unloading_status": analysis_source.get("unloading_status"),
            "pod_reminder_acknowledged": analysis_source.get("pod_reminder_acknowledged"),
        })
    else:
        # Emergency fields - direct mapping
        results_data.update({
            "call_outcome": "emergency_escalation",
            "emergency_type": analysis_source.get("emergency_type"),
            "safety_status": analysis_source.get("safety_status"),
            "injury_status": analysis_source.get("injury_status"),
            "location_emergency": analysis_source.get("emergency_location"),
            "load_secure": analysis_source.get("load_secure"),
        })

    return results_data


def save_transcript(
    db_client: Client,
    call_id: str,
    transcript_text: Optional[str],
    transcript_json: Optional[Any]
) -> bool:
    """
    Save call transcript to database.

    Args:
        db_client: Supabase client instance
        call_id: Database ID of the call
        transcript_text: Transcript as formatted text
        transcript_json: Transcript as JSON object

    Returns:
        True if transcript was saved, False otherwise
    """
    if not transcript_text:
        logger.warning(f"No transcript text available for call {call_id}")
        return False

    try:
        # Check if transcript already exists
        existing_transcript = db_client.table("call_transcripts")\
            .select("*")\
            .eq("call_id", call_id)\
            .execute()

        if not existing_transcript.data:
            logger.info(f"Inserting transcript for call {call_id}")
            db_client.table("call_transcripts").insert({
                "call_id": call_id,
                "transcript": transcript_text,
                "transcript_json": transcript_json
            }).execute()
            logger.info(f"✅ Saved transcript for call {call_id}")
            return True
        else:
            logger.info(f"Transcript already exists for call {call_id}")
            return False

    except Exception as e:
        logger.error(f"❌ Error saving transcript: {e}", exc_info=True)
        return False


def save_or_update_results(
    db_client: Client,
    call_id: str,
    results_data: Dict[str, Any]
) -> bool:
    """
    Save or update structured call results in database.

    Args:
        db_client: Supabase client instance
        call_id: Database ID of the call
        results_data: Structured results dictionary

    Returns:
        True if results were saved/updated, False otherwise
    """
    try:
        logger.info(f"Preparing to save structured results: {results_data}")

        # Check if results already exist
        existing_results = db_client.table("call_results")\
            .select("*")\
            .eq("call_id", call_id)\
            .execute()

        if existing_results.data:
            logger.info(f"Updating existing results for call {call_id}")
            db_client.table("call_results")\
                .update(results_data)\
                .eq("call_id", call_id)\
                .execute()
            logger.info(f"✅ Updated structured results for call {call_id}")
        else:
            logger.info(f"Inserting new structured results for call {call_id}")
            db_client.table("call_results").insert(results_data).execute()
            logger.info(f"✅ Saved structured results for call {call_id}")

        return True

    except Exception as e:
        logger.error(f"❌ Error saving results: {e}", exc_info=True)
        return False


def process_call_details(
    db_client: Client,
    call_id: str,
    call_details: Dict[str, Any]
) -> None:
    """
    Process call details from Retell AI and save to database.

    Saves both transcript and structured results.
    Eliminates duplicate code from refresh_call_details and webhook_handler.

    Args:
        db_client: Supabase client instance
        call_id: Database ID of the call
        call_details: Call details from Retell AI
    """
    # Save transcript
    transcript_text = call_details.get("transcript")
    transcript_json = call_details.get("transcript_object")
    save_transcript(db_client, call_id, transcript_text, transcript_json)

    # Process and save results
    call_analysis = call_details.get("call_analysis", {})

    if call_analysis:
        logger.info(f"📊 Call analysis from Retell: {call_analysis}")
        results_data = build_results_data(call_id, call_analysis)
        save_or_update_results(db_client, call_id, results_data)
    else:
        logger.warning(f"No call analysis available for call {call_id}")
