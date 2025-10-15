from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import logging
from backend.models.agent import AgentConfigCreate, AgentConfigUpdate, AgentConfigResponse
from backend.database import Database, get_db
from backend.services.retell import RetellService, get_retell_service
from backend.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=AgentConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent: AgentConfigCreate,
    current_user=Depends(get_current_user),
    db: Database=Depends(get_db),
    retell: RetellService=Depends(get_retell_service)
):
    """Create agent in database and immediately sync with Retell AI"""
    data = agent.model_dump()
    data["user_id"] = current_user.id

    # First, insert into database
    response = db.client.table("agent_configurations").insert(data).execute()
    agent_record = response.data[0]

    # Immediately create in Retell AI
    try:
        logger.info(f"Creating agent in Retell AI: {agent_record['name']}")
        retell_response = await retell.create_agent(agent_record)

        # Update database with Retell IDs
        db.client.table("agent_configurations")\
            .update({
                "retell_agent_id": retell_response["agent_id"],
                "retell_llm_id": retell_response["llm_id"]
            })\
            .eq("id", agent_record["id"])\
            .execute()

        # Fetch updated record to return
        updated_response = db.client.table("agent_configurations")\
            .select("*")\
            .eq("id", agent_record["id"])\
            .execute()

        logger.info(f"✅ Agent created in Retell AI: {retell_response['agent_id']}")
        return updated_response.data[0]

    except Exception as e:
        logger.error(f"❌ Failed to create agent in Retell AI: {str(e)}")
        # Agent exists in DB but not in Retell - will be created on first call
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent saved to database but failed to sync with Retell AI: {str(e)}"
        )


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


