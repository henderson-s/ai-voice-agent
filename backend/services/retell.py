"""
Retell AI service for voice agent management and call operations.
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

import httpx

from backend.config import get_settings


logger = logging.getLogger(__name__)


class RetellService:
    """
    Service for interacting with Retell AI API.

    Handles agent creation, call initiation, and data retrieval.
    """

    BASE_URL = "https://api.retellai.com"

    def __init__(self):
        """Initialize Retell service with API credentials."""
        settings = get_settings()
        self.api_key = settings.retell_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        logger.debug("Retell service initialized")

    async def create_llm_config(
        self,
        system_prompt: str,
        initial_greeting: str
    ) -> Dict[str, Any]:
        """
        Create LLM configuration for Retell agent.

        Args:
            system_prompt: System-level prompt for agent behavior
            initial_greeting: Initial message the agent will say

        Returns:
            Dict containing llm_id and other configuration details

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        logger.info("Creating LLM configuration")

        payload = {
            "general_prompt": system_prompt,
            "begin_message": initial_greeting,
            "default_dynamic_variables": {
                "driver_name": "Driver",
                "load_number": "LOAD-000"
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/create-retell-llm",
                headers=self.headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

        logger.info(f"LLM configuration created: {result.get('llm_id')}")
        return result

    async def create_agent(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create Retell AI agent with full configuration.

        Args:
            config: Agent configuration dictionary

        Returns:
            Dict containing agent_id and other agent details

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        logger.info(f"Creating agent: {config.get('name')}")

        # Create LLM configuration first
        llm_response = await self.create_llm_config(
            config["system_prompt"],
            config["initial_greeting"]
        )

        # Build agent payload
        agent_payload = self._build_agent_payload(config, llm_response["llm_id"])

        try:
            async with httpx.AsyncClient() as client:
                logger.debug(f"Sending agent creation request: {agent_payload.get('agent_name')}")
                response = await client.post(
                    f"{self.BASE_URL}/create-agent",
                    headers=self.headers,
                    json=agent_payload,
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                result["llm_id"] = llm_response["llm_id"]

            logger.info(f"Agent created successfully: {result.get('agent_id')}")
            return result

        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
            logger.error(f"Failed to create agent: {error_detail}")
            logger.debug(f"Payload sent: {agent_payload}")
            raise

    async def initiate_call(
        self,
        agent_id: str,
        phone_number: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Initiate phone call through Retell AI.

        Args:
            agent_id: ID of the agent to use
            phone_number: Phone number to call (E.164 format)
            metadata: Call metadata and dynamic variables

        Returns:
            Dict containing call_id and call details

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        logger.info(f"Initiating call to {phone_number} with agent {agent_id}")

        payload = {
            "agent_id": agent_id,
            "to_number": phone_number,
            "metadata": metadata,
            "retell_llm_dynamic_variables": metadata
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/create-phone-number-call",
                headers=self.headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

        logger.info(f"Call initiated successfully: {result.get('call_id')}")
        return result

    async def create_web_call(
        self,
        agent_id: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create web call through Retell AI.

        Args:
            agent_id: ID of the agent to use
            metadata: Call metadata and dynamic variables

        Returns:
            Dict containing access_token and call details

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        logger.info(f"Creating web call with agent {agent_id}")

        payload = {
            "agent_id": agent_id,
            "metadata": metadata,
            "retell_llm_dynamic_variables": metadata
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/v2/create-web-call",
                headers=self.headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

        logger.info(f"Web call created successfully: {result.get('call_id')}")
        return result

    async def get_call_details(self, call_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch call details from Retell AI API.

        Args:
            call_id: ID of the call to retrieve

        Returns:
            Dict containing call details or None if not found

        Raises:
            httpx.HTTPStatusError: If API request fails (except 404)
        """
        logger.info(f"Fetching call details for: {call_id}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/v2/get-call/{call_id}",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

            # Transform response to match database schema
            result = {
                "call_id": data.get("call_id"),
                "status": data.get("call_status"),
                "started_at": self._convert_timestamp(data.get("start_timestamp")),
                "ended_at": self._convert_timestamp(data.get("end_timestamp")),
                "duration_seconds": int(data.get("call_duration", 0) / 1000) if data.get("call_duration") else None,
                "transcript": self._format_transcript(data.get("transcript")),
                "transcript_object": data.get("transcript"),
                "call_analysis": data.get("call_analysis"),
                "metadata": data.get("metadata"),
                "recording_url": data.get("recording_url"),
                "public_log_url": data.get("public_log_url")
            }

            logger.debug(f"Call details retrieved for: {call_id}")
            return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Call not found: {call_id}")
                return None
            logger.error(f"Failed to fetch call details: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error fetching call details: {e}")
            return None

    def _build_agent_payload(
        self,
        config: Dict[str, Any],
        llm_id: str
    ) -> Dict[str, Any]:
        """
        Build agent creation payload from configuration.

        Args:
            config: Agent configuration dictionary
            llm_id: ID of created LLM configuration

        Returns:
            Dict containing complete agent payload
        """
        agent_payload = {
            "response_engine": {
                "type": "retell-llm",
                "llm_id": llm_id
            },
            "voice_id": config.get("voice_id", "11labs-Adrian"),
        }

        # Add optional fields
        if config.get("name"):
            agent_payload["agent_name"] = config["name"]

        if config.get("language"):
            agent_payload["language"] = config["language"]

        if config.get("enable_backchannel", True):
            agent_payload["enable_backchannel"] = True
            if config.get("backchannel_words"):
                agent_payload["backchannel_words"] = config["backchannel_words"]

        if config.get("interruption_sensitivity") is not None:
            agent_payload["interruption_sensitivity"] = float(config["interruption_sensitivity"])

        if config.get("responsiveness") is not None:
            agent_payload["responsiveness"] = float(config["responsiveness"])

        ambient_sound = config.get("ambient_sound")
        if ambient_sound and ambient_sound != "off":
            agent_payload["ambient_sound"] = ambient_sound
            if config.get("ambient_sound_volume") is not None:
                agent_payload["ambient_sound_volume"] = float(config["ambient_sound_volume"])

        if config.get("pronunciation_guide"):
            agent_payload["pronunciation_guide"] = config["pronunciation_guide"]

        # Add post-call analysis schema
        scenario_type = config.get("scenario_type", "driver_checkin")
        agent_payload["post_call_analysis_data"] = self._build_analysis_schema(scenario_type)

        return agent_payload

    def _build_analysis_schema(self, scenario_type: str) -> List[Dict[str, Any]]:
        """
        Build post-call analysis schema based on scenario type.

        Args:
            scenario_type: Type of scenario ('driver_checkin' or 'emergency_protocol')

        Returns:
            List of field definitions for post-call analysis
        """
        if scenario_type == "emergency_protocol":
            return [
                {
                    "type": "boolean",
                    "name": "is_emergency",
                    "description": "Whether this call involves an emergency situation"
                },
                {
                    "type": "enum",
                    "name": "emergency_type",
                    "description": "Type of emergency if applicable",
                    "choices": ["accident", "breakdown", "medical", "flat_tire", "other", "none"]
                },
                {
                    "type": "string",
                    "name": "safety_status",
                    "description": "Driver's confirmation of safety status",
                    "examples": ["Driver confirmed everyone is safe", "Driver reported unsafe conditions"]
                },
                {
                    "type": "enum",
                    "name": "injury_status",
                    "description": "Whether there are any injuries",
                    "choices": ["no_injuries", "injuries_reported", "unknown"]
                },
                {
                    "type": "string",
                    "name": "location_emergency",
                    "description": "Specific location of the emergency",
                    "examples": ["I-10 near exit 42", "Mile marker 123 on I-15"]
                },
                {
                    "type": "boolean",
                    "name": "load_secure",
                    "description": "Whether the load/cargo is secure"
                },
                {
                    "type": "string",
                    "name": "call_summary",
                    "description": "Brief summary of the emergency call"
                }
            ]
        else:  # driver_checkin (default)
            return [
                {
                    "type": "enum",
                    "name": "call_outcome",
                    "description": "The outcome or purpose of the call",
                    "choices": ["in_transit_update", "arrival_confirmation", "delay_notification", "other"]
                },
                {
                    "type": "enum",
                    "name": "driver_status",
                    "description": "Current status of the driver",
                    "choices": ["driving", "arrived", "unloading", "delayed", "other"]
                },
                {
                    "type": "string",
                    "name": "current_location",
                    "description": "Driver's current location",
                    "examples": ["I-10 near Phoenix", "Exit 42 on I-15", "At delivery location"]
                },
                {
                    "type": "string",
                    "name": "eta",
                    "description": "Estimated time of arrival",
                    "examples": ["Tomorrow at 8 AM", "In 2 hours", "Around 3 PM today"]
                },
                {
                    "type": "string",
                    "name": "delay_reason",
                    "description": "Reason for any delays if mentioned",
                    "examples": ["Heavy traffic", "Weather conditions", "No delays"]
                },
                {
                    "type": "string",
                    "name": "unloading_status",
                    "description": "Status of unloading if driver has arrived",
                    "examples": ["At dock 12", "Waiting for door assignment", "N/A"]
                },
                {
                    "type": "boolean",
                    "name": "pod_reminder_acknowledged",
                    "description": "Whether driver acknowledged the POD reminder"
                },
                {
                    "type": "string",
                    "name": "call_summary",
                    "description": "Brief summary of the check-in call"
                }
            ]

    def _convert_timestamp(self, timestamp: Any) -> Optional[str]:
        """
        Convert timestamp to ISO format.

        Args:
            timestamp: Timestamp in various formats (milliseconds, ISO string, etc.)

        Returns:
            ISO formatted timestamp string or None
        """
        if not timestamp:
            return None

        try:
            if isinstance(timestamp, str):
                # Try to parse if already ISO format
                try:
                    datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    return timestamp
                except ValueError:
                    timestamp = int(timestamp)

            if isinstance(timestamp, (int, float)):
                # Convert from milliseconds to seconds
                dt = datetime.fromtimestamp(timestamp / 1000)
                return dt.isoformat()

            return None

        except Exception as e:
            logger.warning(f"Failed to convert timestamp {timestamp}: {e}")
            return None

    def _format_transcript(self, transcript_data: Any) -> str:
        """
        Format transcript data into readable string.

        Args:
            transcript_data: Transcript in various formats

        Returns:
            Formatted transcript string
        """
        if not transcript_data:
            return ""

        if isinstance(transcript_data, str):
            return transcript_data

        if isinstance(transcript_data, list):
            lines = []
            for item in transcript_data:
                role = item.get("role", "unknown")
                content = item.get("content", "")
                role_label = "Agent" if role == "agent" else "User"
                lines.append(f"[{role_label}]: {content}")
            return "\n".join(lines)

        return str(transcript_data)


def get_retell_service() -> RetellService:
    """
    Dependency injection function for FastAPI routes.

    Returns:
        RetellService: Retell service instance
    """
    return RetellService()
