"""
Agent management helper functions.
Reduces duplication in call creation endpoints.
"""

import logging
from typing import Dict, Any
from supabase import Client
from backend.services.retell import RetellService

logger = logging.getLogger(__name__)


async def ensure_agent_has_retell_id(
    db_client: Client,
    agent: Dict[str, Any],
    retell: RetellService
) -> str:
    """
    Ensure agent has Retell AI ID, creating if necessary.

    This function eliminates duplicate agent creation logic that appeared
    in both create_phone_call and create_web_call endpoints.

    Args:
        db_client: Supabase client instance
        agent: Agent configuration dictionary
        retell: RetellService instance

    Returns:
        Retell agent ID (string)

    Raises:
        Exception: If agent creation fails
    """
    # Check if agent already has Retell ID
    if agent.get("retell_agent_id"):
        return agent["retell_agent_id"]

    # Create agent in Retell AI
    logger.info(f"Creating agent in Retell AI: {agent['name']}")
    retell_response = await retell.create_agent(agent)

    # Update database with Retell IDs
    db_client.table("agent_configurations")\
        .update({
            "retell_agent_id": retell_response["agent_id"],
            "retell_llm_id": retell_response["llm_id"]
        })\
        .eq("id", agent["id"])\
        .execute()

    logger.info(f"✅ Agent created in Retell AI: {retell_response['agent_id']}")
    return retell_response["agent_id"]


def build_call_metadata(driver_name: str, load_number: str) -> Dict[str, str]:
    """
    Build metadata dictionary for Retell AI calls.

    Args:
        driver_name: Name of the driver
        load_number: Load/shipment number

    Returns:
        Dictionary with metadata and dynamic variables
    """
    return {
        "driver_name": driver_name,
        "load_number": load_number
    }


def build_call_record(
    user_id: str,
    agent_configuration_id: str,
    call_type: str,
    driver_name: str,
    phone_number: str,
    load_number: str,
    retell_call_id: str
) -> Dict[str, Any]:
    """
    Build call record for database insertion.

    Args:
        user_id: User ID
        agent_configuration_id: Agent configuration ID
        call_type: Type of call ("phone" or "web")
        driver_name: Driver name
        phone_number: Phone number (or "WEB_CALL" for web calls)
        load_number: Load number
        retell_call_id: Retell call ID

    Returns:
        Dictionary ready for database insertion
    """
    return {
        "user_id": user_id,
        "agent_configuration_id": agent_configuration_id,
        "call_type": call_type,
        "driver_name": driver_name,
        "phone_number": phone_number,
        "load_number": load_number,
        "retell_call_id": retell_call_id,
        "status": "initiated"
    }
