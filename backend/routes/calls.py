from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List
import logging
from backend.models.call import CallCreate, WebCallCreate, CallResponse, WebCallResponse
from backend.database import Database, get_db
from backend.services.retell import RetellService, get_retell_service
from backend.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/calls", tags=["calls"])


@router.post("/phone", response_model=CallResponse, status_code=status.HTTP_201_CREATED)
async def create_phone_call(
    call_data: CallCreate,
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db),
    retell: RetellService=Depends(get_retell_service)
):
    agent_response = db.client.table("agent_configurations")\
        .select("*")\
        .eq("id", call_data.agent_configuration_id)\
        .eq("user_id", current_user.id)\
        .execute()
    
    if not agent_response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    
    agent = agent_response.data[0]
    
    if not agent.get("retell_agent_id"):
        retell_response = await retell.create_agent(agent)
        db.client.table("agent_configurations")\
            .update({
                "retell_agent_id": retell_response["agent_id"],
                "retell_llm_id": retell_response["llm_id"]
            })\
            .eq("id", agent["id"])\
            .execute()
        agent["retell_agent_id"] = retell_response["agent_id"]
    
    metadata = {
        "driver_name": call_data.driver_name,
        "load_number": call_data.load_number
    }
    
    retell_call = await retell.initiate_call(
        agent["retell_agent_id"],
        call_data.phone_number,
        metadata
    )
    
    call_record = {
        "user_id": current_user.id,
        "agent_configuration_id": call_data.agent_configuration_id,
        "call_type": "phone",
        "driver_name": call_data.driver_name,
        "phone_number": call_data.phone_number,
        "load_number": call_data.load_number,
        "retell_call_id": retell_call.get("call_id"),
        "status": "initiated"
    }
    
    response = db.client.table("calls").insert(call_record).execute()
    return response.data[0]


@router.post("/web", response_model=WebCallResponse, status_code=status.HTTP_201_CREATED)
async def create_web_call(
    call_data: WebCallCreate,
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db),
    retell: RetellService=Depends(get_retell_service)
):
    agent_response = db.client.table("agent_configurations")\
        .select("*")\
        .eq("id", call_data.agent_configuration_id)\
        .eq("user_id", current_user.id)\
        .execute()
    
    if not agent_response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    
    agent = agent_response.data[0]
    
    if not agent.get("retell_agent_id"):
        retell_response = await retell.create_agent(agent)
        db.client.table("agent_configurations")\
            .update({
                "retell_agent_id": retell_response["agent_id"],
                "retell_llm_id": retell_response["llm_id"]
            })\
            .eq("id", agent["id"])\
            .execute()
        agent["retell_agent_id"] = retell_response["agent_id"]
    
    metadata = {
        "driver_name": call_data.driver_name,
        "load_number": call_data.load_number
    }
    
    retell_call = await retell.create_web_call(agent["retell_agent_id"], metadata)
    
    call_record = {
        "user_id": current_user.id,
        "agent_configuration_id": call_data.agent_configuration_id,
        "call_type": "web",
        "driver_name": call_data.driver_name,
        "phone_number": "WEB_CALL",
        "load_number": call_data.load_number,
        "retell_call_id": retell_call.get("call_id"),
        "status": "initiated"
    }
    
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
    if call_id.startswith("call_"):
        response = db.client.table("calls")\
            .select("*")\
            .eq("retell_call_id", call_id)\
            .eq("user_id", current_user.id)\
            .execute()
    else:
        response = db.client.table("calls")\
            .select("*")\
            .eq("id", call_id)\
            .eq("user_id", current_user.id)\
            .execute()

    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call not found")

    return response.data[0]


@router.get("/{call_id}/full")
async def get_call_full_details(
    call_id: str,
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db)
):
    """Get full call details including transcript and structured results"""
    # Get the call
    if call_id.startswith("call_"):
        call_response = db.client.table("calls")\
            .select("*")\
            .eq("retell_call_id", call_id)\
            .eq("user_id", current_user.id)\
            .execute()
    else:
        call_response = db.client.table("calls")\
            .select("*")\
            .eq("id", call_id)\
            .eq("user_id", current_user.id)\
            .execute()

    if not call_response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call not found")

    call_data = call_response.data[0]

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
    if call_id.startswith("call_"):
        response = db.client.table("calls")\
            .select("*")\
            .eq("retell_call_id", call_id)\
            .eq("user_id", current_user.id)\
            .execute()
    else:
        response = db.client.table("calls")\
            .select("*")\
            .eq("id", call_id)\
            .eq("user_id", current_user.id)\
            .execute()

    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call not found")

    db_call = response.data[0]
    retell_call_id = db_call.get("retell_call_id")

    if not retell_call_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No Retell call ID associated")

    # Fetch details from Retell AI
    logger.info(f"Manually fetching details for call: {retell_call_id}")
    try:
        call_details = await retell.get_call_details(retell_call_id)
    except Exception as e:
        logger.error(f"Error fetching from Retell API: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch from Retell AI: {str(e)}")

    if not call_details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call details not found in Retell AI")

    logger.info(f"Fetched call details: {call_details}")

    # Update database with fetched details - remove updated_at as trigger handles it
    update_data = {
        "status": "completed",
        "started_at": call_details.get("started_at"),
        "ended_at": call_details.get("ended_at"),
        "duration_seconds": call_details.get("duration_seconds")
    }

    logger.info(f"Updating call {db_call['id']} with data: {update_data}")
    try:
        # Use service key client to bypass RLS
        from backend.database import get_supabase_client
        service_client = get_supabase_client()

        updated = service_client.table("calls")\
            .update(update_data)\
            .eq("id", db_call["id"])\
            .execute()

        logger.info(f"Updated call successfully: {updated.data}")
    except Exception as e:
        logger.error(f"Error updating call: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update call: {str(e)}")

    # Save transcript to call_transcripts table
    transcript_text = call_details.get("transcript")
    transcript_json = call_details.get("transcript_object")

    logger.info(f"Transcript text length: {len(transcript_text) if transcript_text else 0}")
    logger.info(f"Transcript JSON: {transcript_json}")

    if transcript_text:
        try:
            # Use service key client
            from backend.database import get_supabase_client
            service_client = get_supabase_client()

            # Check if transcript already exists
            existing_transcript = service_client.table("call_transcripts")\
                .select("*")\
                .eq("call_id", db_call["id"])\
                .execute()

            if not existing_transcript.data:
                logger.info(f"Inserting transcript for call {db_call['id']}")
                transcript_insert = service_client.table("call_transcripts").insert({
                    "call_id": db_call["id"],
                    "transcript": transcript_text,
                    "transcript_json": transcript_json
                }).execute()
                logger.info(f"✅ Saved transcript for call {db_call['id']}: {transcript_insert.data}")
            else:
                logger.info(f"Transcript already exists for call {db_call['id']}")
        except Exception as e:
            logger.error(f"❌ Error saving transcript: {e}", exc_info=True)
    else:
        logger.warning(f"No transcript text available for call {db_call['id']}")

    # Use Retell's post-call analysis (AI-powered extraction)
    call_analysis = call_details.get("call_analysis", {})
    logger.info(f"📊 Call analysis from Retell: {call_analysis}")

    if call_analysis:
        try:
            # Use service key client
            from backend.database import get_supabase_client
            service_client = get_supabase_client()

            # Retell returns our custom analysis inside custom_analysis_data
            custom_analysis = call_analysis.get("custom_analysis_data", {})

            # If custom_analysis_data exists, use it; otherwise fall back to call_analysis
            analysis_source = custom_analysis if custom_analysis else call_analysis

            # Determine scenario type based on presence of emergency fields
            is_emergency = analysis_source.get("is_emergency", False)
            scenario_type = "emergency_protocol" if is_emergency else "driver_checkin"

            # Build results data from Retell's analysis
            results_data = {
                "call_id": db_call["id"],
                "scenario_type": scenario_type,
                "is_emergency": is_emergency,
                "call_summary": call_analysis.get("call_summary", analysis_source.get("call_summary", "")),
                "analysis_data": call_analysis,
            }

            # Add scenario-specific fields from Retell's extraction
            # Use exact field names from custom_analysis_data (no transformation)
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

            logger.info(f"Preparing to save structured results: {results_data}")

            # Check if results already exist
            existing_results = service_client.table("call_results")\
                .select("*")\
                .eq("call_id", db_call["id"])\
                .execute()

            if existing_results.data:
                logger.info(f"Updating existing results for call {db_call['id']}")
                results_update = service_client.table("call_results")\
                    .update(results_data)\
                    .eq("call_id", db_call["id"])\
                    .execute()
                logger.info(f"✅ Updated structured results: {results_update.data}")
            else:
                logger.info(f"Inserting new structured results for call {db_call['id']}")
                results_insert = service_client.table("call_results").insert(results_data).execute()
                logger.info(f"✅ Saved structured results for call {db_call['id']}: {results_insert.data}")
        except Exception as e:
            logger.error(f"❌ Error analyzing transcript and saving results: {e}", exc_info=True)
    else:
        logger.warning(f"No transcript available for analysis for call {db_call['id']}")

    return updated.data[0]


# Webhook endpoint for Retell AI call status updates (no auth required for webhooks)
@router.post("/webhook")
async def webhook_handler(request: Request):
    # Create a new database instance using service key for webhooks (bypass RLS)
    from backend.database import get_supabase_client
    db_client = get_supabase_client()

    try:
        body = await request.json()
        logger.info(f"Received webhook: {body}")

        # Handle different webhook payload structures
        event_type = body.get("event_type") or body.get("event")
        call_id = None

        # Try different ways to get call_id
        if body.get("call_id"):
            call_id = body["call_id"]
        elif body.get("call") and body["call"].get("call_id"):
            call_id = body["call"]["call_id"]

        if not call_id:
            logger.error(f"No call_id in webhook payload. Body: {body}")
            return {"status": "error", "message": "No call_id provided"}

        # Find the call in our database by retell_call_id (using service key, no RLS)
        call_response = db_client.table("calls")\
            .select("*")\
            .eq("retell_call_id", call_id)\
            .execute()
        
        if not call_response.data:
            logger.warning(f"Call not found in database: {call_id}")
            return {"status": "error", "message": "Call not found"}
        
        db_call = call_response.data[0]
        
        # Update call status based on event type
        status_mapping = {
            "call_started": "in_progress",
            "call_ended": "completed",
            "call_analyzed": "completed",
            "call_failed": "failed"
        }
        
        new_status = status_mapping.get(event_type)
        if new_status:
            # Update call status
            update_data = {"status": new_status}

            if event_type == "call_ended":
                # Fetch full call details from Retell AI
                try:
                    retell = RetellService()
                    call_details = await retell.get_call_details(call_id)

                    if call_details:
                        # Update calls table with basic info
                        update_data.update({
                            "ended_at": call_details.get("ended_at"),
                            "started_at": call_details.get("started_at"),
                            "duration_seconds": call_details.get("duration_seconds")
                        })

                        # Update calls table
                        db_client.table("calls")\
                            .update(update_data)\
                            .eq("id", db_call["id"])\
                            .execute()

                        logger.info(f"Updated call {db_call['id']} status to {new_status}")

                        # Save transcript to call_transcripts table
                        transcript_text = call_details.get("transcript")
                        transcript_json = call_details.get("transcript_object")

                        if transcript_text:
                            try:
                                db_client.table("call_transcripts").insert({
                                    "call_id": db_call["id"],
                                    "transcript": transcript_text,
                                    "transcript_json": transcript_json
                                }).execute()
                                logger.info(f"Saved transcript for call {db_call['id']}")
                            except Exception as transcript_error:
                                logger.error(f"Error saving transcript: {transcript_error}")

                        # Use Retell's post-call analysis (AI-powered extraction)
                        call_analysis = call_details.get("call_analysis", {})

                        if call_analysis:
                            try:
                                logger.info(f"📊 Webhook - Retell analysis data: {call_analysis}")

                                # Retell returns our custom analysis inside custom_analysis_data
                                custom_analysis = call_analysis.get("custom_analysis_data", {})

                                # If custom_analysis_data exists, use it; otherwise fall back to call_analysis
                                analysis_source = custom_analysis if custom_analysis else call_analysis

                                # Determine scenario type based on presence of emergency fields
                                is_emergency = analysis_source.get("is_emergency", False)
                                scenario_type = "emergency_protocol" if is_emergency else "driver_checkin"

                                # Build results data from Retell's analysis
                                results_data = {
                                    "call_id": db_call["id"],
                                    "scenario_type": scenario_type,
                                    "is_emergency": is_emergency,
                                    "call_summary": call_analysis.get("call_summary", analysis_source.get("call_summary", "")),
                                    "analysis_data": call_analysis,
                                }

                                # Add scenario-specific fields from Retell's extraction
                                # Use exact field names from custom_analysis_data (no transformation)
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

                                logger.info(f"Webhook - Saving structured results: {results_data}")

                                # Insert or update results
                                existing_results = db_client.table("call_results")\
                                    .select("*")\
                                    .eq("call_id", db_call["id"])\
                                    .execute()

                                if existing_results.data:
                                    db_client.table("call_results")\
                                        .update(results_data)\
                                        .eq("call_id", db_call["id"])\
                                        .execute()
                                    logger.info(f"✅ Webhook - Updated structured results for call {db_call['id']}")
                                else:
                                    db_client.table("call_results").insert(results_data).execute()
                                    logger.info(f"✅ Webhook - Saved structured results for call {db_call['id']}")

                            except Exception as results_error:
                                logger.error(f"❌ Webhook - Error saving results: {results_error}", exc_info=True)

                    else:
                        logger.warning(f"Could not fetch call details for {call_id}")
                        # Still update status
                        db_client.table("calls")\
                            .update(update_data)\
                            .eq("id", db_call["id"])\
                            .execute()

                except Exception as e:
                    logger.error(f"Error processing call_ended: {e}", exc_info=True)

            elif event_type == "call_analyzed":
                # Handle additional analysis updates
                try:
                    retell = RetellService()
                    call_details = await retell.get_call_details(call_id)

                    if call_details and call_details.get("call_analysis"):
                        # Update or insert analysis results
                        analysis_data = {
                            "call_summary": call_details["call_analysis"].get("call_summary"),
                            "analysis_data": call_details["call_analysis"]
                        }

                        # Try to update existing record, or insert if not exists
                        existing = db_client.table("call_results")\
                            .select("*")\
                            .eq("call_id", db_call["id"])\
                            .execute()

                        if existing.data:
                            db_client.table("call_results")\
                                .update(analysis_data)\
                                .eq("call_id", db_call["id"])\
                                .execute()
                        else:
                            analysis_data["call_id"] = db_call["id"]
                            db_client.table("call_results").insert(analysis_data).execute()

                        logger.info(f"Updated analysis for call {db_call['id']}")
                except Exception as e:
                    logger.error(f"Error processing call_analyzed: {e}")

            else:
                # For other events, just update status
                try:
                    db_client.table("calls")\
                        .update(update_data)\
                        .eq("id", db_call["id"])\
                        .execute()
                    logger.info(f"Updated call {db_call['id']} status to {new_status}")
                except Exception as update_error:
                    logger.error(f"Error updating status: {update_error}", exc_info=True)
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

