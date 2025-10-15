from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class AgentConfigCreate(BaseModel):
    name: str
    description: Optional[str] = None
    scenario_type: Optional[str] = "driver_checkin"  # 'driver_checkin' or 'emergency_protocol'
    system_prompt: str
    initial_greeting: str

    # Voice settings
    voice_id: Optional[str] = "11labs-Adrian"
    language: Optional[str] = "en-US"

    # Advanced human-like settings
    enable_backchannel: Optional[bool] = True
    backchannel_words: Optional[List[str]] = ["mm-hmm", "I see", "got it"]
    enable_filler_words: Optional[bool] = True
    filler_words: Optional[List[str]] = ["um", "uh", "hmm", "let me see"]

    # Conversation dynamics
    interruption_sensitivity: Optional[float] = 0.7
    response_delay_ms: Optional[int] = 800
    responsiveness: Optional[float] = 0.8

    # Ambient sound (Valid values: coffee-shop, convention-hall, summer-outdoor, mountain-outdoor, static-noise, call-center, or null)
    ambient_sound: Optional[str] = "call-center"
    ambient_sound_volume: Optional[float] = 0.5  # Range: 0-2, default: 1

    # Call duration
    max_call_duration_seconds: Optional[int] = 600
    enable_auto_end_call: Optional[bool] = True
    end_call_after_silence_ms: Optional[int] = 10000

    # Pronunciation
    pronunciation_guide: Optional[Dict[str, str]] = {}

    # Scenario-specific settings
    reminder_keywords: Optional[List[str]] = ["POD", "proof of delivery", "paperwork"]
    enable_reminder: Optional[bool] = True
    emergency_keywords: Optional[List[str]] = [
        "accident", "crash", "emergency", "help",
        "breakdown", "broke down", "medical", "injury",
        "blowout", "flat tire", "broke", "stuck"
    ]


class AgentConfigUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    scenario_type: Optional[str] = None
    system_prompt: Optional[str] = None
    initial_greeting: Optional[str] = None
    voice_id: Optional[str] = None
    language: Optional[str] = None
    enable_backchannel: Optional[bool] = None
    backchannel_words: Optional[List[str]] = None
    enable_filler_words: Optional[bool] = None
    filler_words: Optional[List[str]] = None
    interruption_sensitivity: Optional[float] = None
    response_delay_ms: Optional[int] = None
    responsiveness: Optional[float] = None
    ambient_sound: Optional[str] = None
    ambient_sound_volume: Optional[float] = None
    max_call_duration_seconds: Optional[int] = None
    enable_auto_end_call: Optional[bool] = None
    end_call_after_silence_ms: Optional[int] = None
    pronunciation_guide: Optional[Dict[str, str]] = None
    reminder_keywords: Optional[List[str]] = None
    enable_reminder: Optional[bool] = None
    emergency_keywords: Optional[List[str]] = None
    is_active: Optional[bool] = None


class AgentConfigResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    scenario_type: str
    system_prompt: str
    initial_greeting: str
    retell_agent_id: Optional[str]
    retell_llm_id: Optional[str]
    voice_id: str
    language: str
    enable_backchannel: bool
    backchannel_words: List[str]
    enable_filler_words: bool
    filler_words: List[str]
    interruption_sensitivity: float
    response_delay_ms: int
    responsiveness: float
    ambient_sound: str
    ambient_sound_volume: float
    max_call_duration_seconds: int
    enable_auto_end_call: bool
    end_call_after_silence_ms: int
    pronunciation_guide: Dict[str, str]
    reminder_keywords: List[str]
    enable_reminder: bool
    emergency_keywords: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

