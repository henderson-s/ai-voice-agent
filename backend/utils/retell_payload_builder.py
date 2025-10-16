"""
Retell AI payload builders.
Extracted from retell.py service to reduce function complexity.
"""

from typing import Dict, Any, List


def build_llm_payload(system_prompt: str, initial_greeting: str) -> Dict[str, Any]:
    """
    Build LLM configuration payload for Retell AI.

    Args:
        system_prompt: System-level prompt for agent behavior
        initial_greeting: Initial message the agent will say

    Returns:
        Dictionary containing LLM configuration payload
    """
    return {
        "general_prompt": system_prompt,
        "begin_message": initial_greeting,
        "default_dynamic_variables": {
            "driver_name": "Driver",
            "load_number": "LOAD-000"
        }
    }


def build_response_engine(llm_id: str) -> Dict[str, str]:
    """
    Build response engine configuration.

    Args:
        llm_id: ID of created LLM configuration

    Returns:
        Dictionary containing response engine configuration
    """
    return {
        "type": "retell-llm",
        "llm_id": llm_id
    }


def add_optional_voice_settings(
    payload: Dict[str, Any],
    config: Dict[str, Any]
) -> None:
    """
    Add optional voice settings to agent payload (mutates payload).

    Args:
        payload: Agent payload dictionary (will be mutated)
        config: Agent configuration dictionary
    """
    if config.get("language"):
        payload["language"] = config["language"]

    if config.get("enable_backchannel", True):
        payload["enable_backchannel"] = True
        if config.get("backchannel_words"):
            payload["backchannel_words"] = config["backchannel_words"]

    if config.get("interruption_sensitivity") is not None:
        payload["interruption_sensitivity"] = float(config["interruption_sensitivity"])

    if config.get("responsiveness") is not None:
        payload["responsiveness"] = float(config["responsiveness"])


def add_optional_ambient_sound(
    payload: Dict[str, Any],
    config: Dict[str, Any]
) -> None:
    """
    Add ambient sound settings to agent payload (mutates payload).

    Args:
        payload: Agent payload dictionary (will be mutated)
        config: Agent configuration dictionary
    """
    ambient_sound = config.get("ambient_sound")
    if ambient_sound and ambient_sound != "off":
        payload["ambient_sound"] = ambient_sound
        if config.get("ambient_sound_volume") is not None:
            payload["ambient_sound_volume"] = float(config["ambient_sound_volume"])


def add_pronunciation_guide(
    payload: Dict[str, Any],
    config: Dict[str, Any]
) -> None:
    """
    Add pronunciation guide to agent payload (mutates payload).

    Args:
        payload: Agent payload dictionary (will be mutated)
        config: Agent configuration dictionary
    """
    if config.get("pronunciation_guide"):
        payload["pronunciation_guide"] = config["pronunciation_guide"]


def build_agent_payload(
    config: Dict[str, Any],
    llm_id: str,
    analysis_schema: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Build complete agent creation payload from configuration.

    This function eliminates a 55-line method in retell.py that was hard to read.

    Args:
        config: Agent configuration dictionary
        llm_id: ID of created LLM configuration
        analysis_schema: Post-call analysis schema

    Returns:
        Dictionary containing complete agent payload
    """
    # Start with required fields
    agent_payload = {
        "response_engine": build_response_engine(llm_id),
        "voice_id": config.get("voice_id", "11labs-Adrian"),
    }

    # Add agent name if provided
    if config.get("name"):
        agent_payload["agent_name"] = config["name"]

    # Add optional settings in logical groups
    add_optional_voice_settings(agent_payload, config)
    add_optional_ambient_sound(agent_payload, config)
    add_pronunciation_guide(agent_payload, config)

    # Add post-call analysis schema
    agent_payload["post_call_analysis_data"] = analysis_schema

    return agent_payload
