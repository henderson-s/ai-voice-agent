import httpx
from typing import Dict, Any, Optional
from backend.config import get_settings


class RetellService:
    BASE_URL = "https://api.retellai.com"
    
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.retell_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_llm_config(self, system_prompt: str, initial_greeting: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/create-retell-llm",
                headers=self.headers,
                json={
                    "general_prompt": system_prompt,
                    "begin_message": initial_greeting,
                    "default_dynamic_variables": {
                        "driver_name": "Driver",
                        "load_number": "LOAD-000"
                    }
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    async def create_agent(self, config: Dict[str, Any]) -> Dict[str, Any]:
        llm_response = await self.create_llm_config(
            config["system_prompt"],
            config["initial_greeting"]
        )

        # Build agent payload with all advanced settings
        agent_payload = {
            "response_engine": {
                "type": "retell-llm",
                "llm_id": llm_response["llm_id"]
            },
            "voice_id": "11labs-Adrian",
        }

        # Add agent_name if provided
        if config.get("name"):
            agent_payload["agent_name"] = config["name"]

        # Add language if provided (defaults to en-US in Retell)
        if config.get("language"):
            agent_payload["language"] = config.get("language")

        # Enable backchannel
        if config.get("enable_backchannel", True):  # Default to True
            agent_payload["enable_backchannel"] = True
            if config.get("backchannel_words"):
                agent_payload["backchannel_words"] = config.get("backchannel_words")

        # Add interruption sensitivity (0.0 to 1.0)
        if config.get("interruption_sensitivity") is not None:
            agent_payload["interruption_sensitivity"] = float(config.get("interruption_sensitivity"))

        # Add responsiveness (0.0 to 1.0)
        if config.get("responsiveness") is not None:
            agent_payload["responsiveness"] = float(config.get("responsiveness"))

        # Add ambient sound
        ambient_sound = config.get("ambient_sound")
        if ambient_sound and ambient_sound != "off":
            agent_payload["ambient_sound"] = ambient_sound
            if config.get("ambient_sound_volume") is not None:
                agent_payload["ambient_sound_volume"] = float(config.get("ambient_sound_volume"))

        # Add pronunciation guide if provided
        if config.get("pronunciation_guide"):
            agent_payload["pronunciation_guide"] = config.get("pronunciation_guide")

        # Add post-call analysis fields for structured data extraction
        scenario_type = config.get("scenario_type", "driver_checkin")
        agent_payload["post_call_analysis_data"] = self._build_analysis_schema(scenario_type)

        try:
            async with httpx.AsyncClient() as client:
                print(f"DEBUG: Sending minimal payload: {agent_payload}")
                response = await client.post(
                    f"{self.BASE_URL}/create-agent",
                    headers=self.headers,
                    json=agent_payload,
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                result["llm_id"] = llm_response["llm_id"]
                return result
        except httpx.HTTPStatusError as e:
            # Log the full error response for debugging
            error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
            print(f"Retell API Error: {error_detail}")
            print(f"Payload sent: {agent_payload}")
            raise
    
    async def initiate_call(self, agent_id: str, phone_number: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/create-phone-number-call",
                headers=self.headers,
                json={
                    "agent_id": agent_id,
                    "to_number": phone_number,
                    "metadata": metadata,
                    "retell_llm_dynamic_variables": metadata
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    async def create_web_call(self, agent_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/v2/create-web-call",
                headers=self.headers,
                json={
                    "agent_id": agent_id,
                    "metadata": metadata,
                    "retell_llm_dynamic_variables": metadata
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def get_call_details(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Fetch call details from Retell AI API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/v2/get-call/{call_id}",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                # Transform the response to match our database schema
                result = {
                    "call_id": data.get("call_id"),
                    "status": data.get("call_status"),
                    "started_at": self._convert_timestamp(data.get("start_timestamp")),
                    "ended_at": self._convert_timestamp(data.get("end_timestamp")),
                    "duration_seconds": int(data.get("call_duration", 0) / 1000) if data.get("call_duration") else None,
                    "transcript": self._format_transcript(data.get("transcript")),
                    "transcript_object": data.get("transcript"),  # Keep original for reference
                    "call_analysis": data.get("call_analysis"),
                    "metadata": data.get("metadata"),
                    "recording_url": data.get("recording_url"),
                    "public_log_url": data.get("public_log_url")
                }

                return result
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
        except Exception as e:
            print(f"Error fetching call details: {e}")
            return None

    def _convert_timestamp(self, timestamp) -> Optional[str]:
        """Convert timestamp from milliseconds to ISO format"""
        if not timestamp:
            return None

        try:
            # Check if it's a string or number
            if isinstance(timestamp, str):
                # Try to parse if it's already ISO format
                from datetime import datetime
                try:
                    datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    return timestamp  # Already in correct format
                except:
                    # Try as milliseconds
                    timestamp = int(timestamp)

            if isinstance(timestamp, (int, float)):
                # Convert from milliseconds to seconds
                from datetime import datetime
                dt = datetime.fromtimestamp(timestamp / 1000)
                return dt.isoformat()

            return None
        except Exception as e:
            print(f"Error converting timestamp {timestamp}: {e}")
            return None

    def _build_analysis_schema(self, scenario_type: str) -> list:
        """Build post-call analysis schema based on scenario type"""
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
                    "name": "emergency_location",
                    "description": "Specific location of the emergency (highway, mile marker, etc.)",
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
                    "description": "Driver's current location (highway, city, mile marker, etc.)",
                    "examples": ["I-10 near Phoenix", "Exit 42 on I-15", "At delivery location"]
                },
                {
                    "type": "string",
                    "name": "eta",
                    "description": "Estimated time of arrival mentioned by driver",
                    "examples": ["Tomorrow at 8 AM", "In 2 hours", "Around 3 PM today"]
                },
                {
                    "type": "string",
                    "name": "delay_reason",
                    "description": "Reason for any delays if mentioned",
                    "examples": ["Heavy traffic", "Weather conditions", "No delays", "Vehicle maintenance"]
                },
                {
                    "type": "string",
                    "name": "unloading_status",
                    "description": "Status of unloading if driver has arrived",
                    "examples": ["At dock 12", "Waiting for door assignment", "Unloading in progress", "N/A"]
                },
                {
                    "type": "boolean",
                    "name": "pod_reminder_acknowledged",
                    "description": "Whether driver acknowledged the POD (Proof of Delivery) reminder"
                },
                {
                    "type": "string",
                    "name": "call_summary",
                    "description": "Brief summary of the check-in call"
                }
            ]

    def _format_transcript(self, transcript_data) -> str:
        """Format transcript array into readable string"""
        if not transcript_data:
            return ""

        if isinstance(transcript_data, str):
            return transcript_data

        if isinstance(transcript_data, list):
            lines = []
            for item in transcript_data:
                role = item.get("role", "unknown")
                content = item.get("content", "")
                timestamp = item.get("timestamp", "")

                # Format with role and content
                role_label = "Agent" if role == "agent" else "User"
                lines.append(f"[{role_label}]: {content}")

            return "\n".join(lines)

        return str(transcript_data)


def get_retell_service() -> RetellService:
    return RetellService()

