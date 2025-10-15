from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AgentConfigCreate(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: str
    initial_greeting: str
    voice_id: Optional[str] = "11labs-Adrian"
    language: Optional[str] = "en-US"
    enable_backchannel: Optional[bool] = True
    backchannel_words: Optional[List[str]] = ["mm-hmm", "I see", "got it"]
    interruption_sensitivity: Optional[float] = 0.7
    response_delay_ms: Optional[int] = 800
    max_call_duration_seconds: Optional[int] = 600


class AgentConfigUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    initial_greeting: Optional[str] = None
    voice_id: Optional[str] = None
    language: Optional[str] = None
    enable_backchannel: Optional[bool] = None
    backchannel_words: Optional[List[str]] = None
    interruption_sensitivity: Optional[float] = None
    response_delay_ms: Optional[int] = None
    max_call_duration_seconds: Optional[int] = None
    is_active: Optional[bool] = None


class AgentConfigResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    system_prompt: str
    initial_greeting: str
    retell_agent_id: Optional[str]
    retell_llm_id: Optional[str]
    voice_id: str
    language: str
    enable_backchannel: bool
    backchannel_words: List[str]
    interruption_sensitivity: float
    response_delay_ms: int
    max_call_duration_seconds: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

