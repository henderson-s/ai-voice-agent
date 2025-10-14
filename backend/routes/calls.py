from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from backend.models.call import CallCreate, WebCallCreate, CallResponse, WebCallResponse
from backend.database import Database, get_db
from backend.services.retell import RetellService, get_retell_service
from backend.utils.auth import get_current_user

router = APIRouter(prefix="/calls", tags=["calls"])


@router.post("/phone", response_model=CallResponse, status_code=status.HTTP_201_CREATED)
async def create_phone_call(
    call_data: CallCreate,
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db),
    retell: RetellService=Depends(get_retell_service)
):
    agent_response = db.client.table("agent_configurations")\
        .select("*")\
        .eq("id", call_data.agent_configuration_id)\
        .eq("user_id", current_user.id)\
        .execute()
    
    if not agent_response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    
    agent = agent_response.data[0]
    
    if not agent.get("retell_agent_id"):
        retell_response = await retell.create_agent(agent)
        db.client.table("agent_configurations")\
            .update({
                "retell_agent_id": retell_response["agent_id"],
                "retell_llm_id": retell_response["llm_id"]
            })\
            .eq("id", agent["id"])\
            .execute()
        agent["retell_agent_id"] = retell_response["agent_id"]
    
    metadata = {
        "driver_name": call_data.driver_name,
        "load_number": call_data.load_number
    }
    
    retell_call = await retell.initiate_call(
        agent["retell_agent_id"],
        call_data.phone_number,
        metadata
    )
    
    call_record = {
        "user_id": current_user.id,
        "agent_configuration_id": call_data.agent_configuration_id,
        "driver_name": call_data.driver_name,
        "phone_number": call_data.phone_number,
        "load_number": call_data.load_number,
        "retell_call_id": retell_call.get("call_id"),
        "status": "initiated"
    }
    
    response = db.client.table("calls").insert(call_record).execute()
    return response.data[0]


@router.post("/web", response_model=WebCallResponse, status_code=status.HTTP_201_CREATED)
async def create_web_call(
    call_data: WebCallCreate,
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db),
    retell: RetellService=Depends(get_retell_service)
):
    agent_response = db.client.table("agent_configurations")\
        .select("*")\
        .eq("id", call_data.agent_configuration_id)\
        .eq("user_id", current_user.id)\
        .execute()
    
    if not agent_response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    
    agent = agent_response.data[0]
    
    if not agent.get("retell_agent_id"):
        retell_response = await retell.create_agent(agent)
        db.client.table("agent_configurations")\
            .update({
                "retell_agent_id": retell_response["agent_id"],
                "retell_llm_id": retell_response["llm_id"]
            })\
            .eq("id", agent["id"])\
            .execute()
        agent["retell_agent_id"] = retell_response["agent_id"]
    
    metadata = {
        "driver_name": call_data.driver_name,
        "load_number": call_data.load_number
    }
    
    retell_call = await retell.create_web_call(agent["retell_agent_id"], metadata)
    
    call_record = {
        "user_id": current_user.id,
        "agent_configuration_id": call_data.agent_configuration_id,
        "driver_name": call_data.driver_name,
        "phone_number": "WEB_CALL",
        "load_number": call_data.load_number,
        "retell_call_id": retell_call.get("call_id"),
        "status": "initiated"
    }
    
    db.client.table("calls").insert(call_record).execute()
    
    return WebCallResponse(
        access_token=retell_call["access_token"],
        call_id=retell_call["call_id"]
    )


@router.get("", response_model=List[CallResponse])
async def list_calls(
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db)
):
    response = db.client.table("calls")\
        .select("*")\
        .eq("user_id", current_user.id)\
        .order("created_at", desc=True)\
        .limit(100)\
        .execute()
    return response.data


@router.get("/{call_id}", response_model=CallResponse)
async def get_call(
    call_id: str,
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db)
):
    if call_id.startswith("call_"):
        response = db.client.table("calls")\
            .select("*")\
            .eq("retell_call_id", call_id)\
            .eq("user_id", current_user.id)\
            .execute()
    else:
        response = db.client.table("calls")\
            .select("*")\
            .eq("id", call_id)\
            .eq("user_id", current_user.id)\
            .execute()
    
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call not found")
    
    return response.data[0]

