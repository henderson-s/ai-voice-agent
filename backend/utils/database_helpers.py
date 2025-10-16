"""
Database query helpers to reduce duplication in routes.
"""

import logging
from typing import Optional, Dict, Any
from supabase import Client
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


def get_call_by_id(
    db_client: Client,
    call_id: str,
    user_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get call from database by ID or retell_call_id.

    Handles both database ID and Retell call ID formats.
    Eliminates duplicate query logic from multiple route functions.

    Args:
        db_client: Supabase client instance
        call_id: Either database ID or retell_call_id
        user_id: Optional user ID for authorization (None to skip RLS)

    Returns:
        Call data dictionary or None if not found
    """
    # Determine if this is a Retell call ID or database ID
    if call_id.startswith("call_"):
        query = db_client.table("calls").select("*").eq("retell_call_id", call_id)
    else:
        query = db_client.table("calls").select("*").eq("id", call_id)

    # Add user_id filter if provided (for RLS)
    if user_id:
        query = query.eq("user_id", user_id)

    response = query.execute()
    return response.data[0] if response.data else None


def get_agent_by_id(
    db_client: Client,
    agent_id: str,
    user_id: str
) -> Dict[str, Any]:
    """
    Get agent configuration by ID with user authorization.

    Args:
        db_client: Supabase client instance
        agent_id: Agent configuration ID
        user_id: User ID for authorization

    Returns:
        Agent configuration dictionary

    Raises:
        HTTPException: If agent not found
    """
    response = db_client.table("agent_configurations")\
        .select("*")\
        .eq("id", agent_id)\
        .eq("user_id", user_id)\
        .execute()

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    return response.data[0]


def update_call_basic_info(
    db_client: Client,
    call_id: str,
    call_status: str,
    call_details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Update basic call information in database.

    Args:
        db_client: Supabase client instance
        call_id: Database call ID
        call_status: New call status
        call_details: Optional call details from Retell AI
    """
    update_data = {"status": call_status}

    if call_details:
        update_data.update({
            "started_at": call_details.get("started_at"),
            "ended_at": call_details.get("ended_at"),
            "duration_seconds": call_details.get("duration_seconds")
        })

    db_client.table("calls")\
        .update(update_data)\
        .eq("id", call_id)\
        .execute()

    logger.info(f"Updated call {call_id} status to {call_status}")


def ensure_agent_has_retell_id(
    db_client: Client,
    agent: Dict[str, Any],
    retell_service: Any
) -> str:
    """
    Ensure agent has Retell AI ID, creating if necessary.

    Args:
        db_client: Supabase client instance
        agent: Agent configuration dictionary
        retell_service: RetellService instance

    Returns:
        Retell agent ID

    Raises:
        Exception: If agent creation fails
    """
    if not agent.get("retell_agent_id"):
        logger.info(f"Creating agent in Retell AI: {agent['name']}")

        # Import here to avoid circular dependency
        import asyncio
        retell_response = asyncio.create_task(retell_service.create_agent(agent))

        db_client.table("agent_configurations")\
            .update({
                "retell_agent_id": retell_response["agent_id"],
                "retell_llm_id": retell_response["llm_id"]
            })\
            .eq("id", agent["id"])\
            .execute()

        return retell_response["agent_id"]

    return agent["retell_agent_id"]
