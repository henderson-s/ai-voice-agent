from pydantic import BaseModel
from typing import Optional
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
    initiated_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]
    created_at: datetime


class WebCallResponse(BaseModel):
    access_token: str
    call_id: str

