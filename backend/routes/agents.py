from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from backend.models.agent import AgentConfigCreate, AgentConfigUpdate, AgentConfigResponse
from backend.database import Database, get_db
from backend.utils.auth import get_current_user

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=AgentConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent: AgentConfigCreate,
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db)
):
    data = agent.model_dump()
    data["user_id"] = current_user.id
    
    response = db.client.table("agent_configurations").insert(data).execute()
    return response.data[0]


@router.get("", response_model=List[AgentConfigResponse])
async def list_agents(
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db)
):
    response = db.client.table("agent_configurations")\
        .select("*")\
        .eq("user_id", current_user.id)\
        .eq("is_active", True)\
        .order("created_at", desc=True)\
        .execute()
    return response.data


@router.get("/{agent_id}", response_model=AgentConfigResponse)
async def get_agent(
    agent_id: str,
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db)
):
    response = db.client.table("agent_configurations")\
        .select("*")\
        .eq("id", agent_id)\
        .eq("user_id", current_user.id)\
        .execute()
    
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    
    return response.data[0]


@router.patch("/{agent_id}", response_model=AgentConfigResponse)
async def update_agent(
    agent_id: str,
    agent_update: AgentConfigUpdate,
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db)
):
    data = agent_update.model_dump(exclude_none=True)
    data["updated_at"] = "NOW()"
    
    response = db.client.table("agent_configurations")\
        .update(data)\
        .eq("id", agent_id)\
        .eq("user_id", current_user.id)\
        .execute()
    
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    
    return response.data[0]


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db)
):
    response = db.client.table("agent_configurations")\
        .update({"is_active": False, "updated_at": "NOW()"})\
        .eq("id", agent_id)\
        .eq("user_id", current_user.id)\
        .execute()
    
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

