from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class CallCreate(BaseModel):
    agent_configuration_id: str
    driver_name: str
    phone_number: str
    load_number: str


class WebCallCreate(BaseModel):
    agent_configuration_id: str
    driver_name: str
    load_number: str


class CallResponse(BaseModel):
    id: str
    user_id: str
    agent_configuration_id: Optional[str]
    driver_name: str
    phone_number: str
    load_number: str
    retell_call_id: Optional[str]
    status: str
    call_type: str
    initiated_at: datetime
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    created_at: datetime


class WebCallResponse(BaseModel):
    access_token: str
    call_id: str


class CallTranscriptResponse(BaseModel):
    id: str
    call_id: str
    transcript: str
    transcript_json: Optional[List[Dict[str, Any]]] = None
    created_at: datetime


class CallResultsResponse(BaseModel):
    id: str
    call_id: str
    scenario_type: Optional[str] = None
    call_outcome: Optional[str] = None
    driver_status: Optional[str] = None
    current_location: Optional[str] = None
    eta: Optional[str] = None
    delays: Optional[str] = None
    is_emergency: Optional[bool] = False
    emergency_type: Optional[str] = None
    call_summary: Optional[str] = None
    analysis_data: Optional[Dict[str, Any]] = None
    created_at: datetime


