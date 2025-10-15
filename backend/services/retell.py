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
                    "begin_message": initial_greeting
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
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/create-agent",
                headers=self.headers,
                json={
                    "response_engine": {
                        "type": "retell-llm",
                        "llm_id": llm_response["llm_id"]
                    },
                    "voice_id": config.get("voice_id", "11labs-Adrian"),
                    "agent_name": config["name"],
                    "language": config.get("language", "en-US"),
                    "enable_backchannel": config.get("enable_backchannel", True),
                    "backchannel_words": config.get("backchannel_words", ["mm-hmm"]),
                    "interruption_sensitivity": config.get("interruption_sensitivity", 0.7),
                    "max_call_duration_ms": config.get("max_call_duration_seconds", 600) * 1000
                },
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            result["llm_id"] = llm_response["llm_id"]
            return result
    
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


def get_retell_service() -> RetellService:
    return RetellService()

