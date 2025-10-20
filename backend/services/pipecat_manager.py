"""
Pipecat pipeline manager for handling active call sessions.

This module manages the lifecycle of Pipecat pipelines with
real audio processing capabilities.
"""

import logging
import asyncio
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from backend.services.pipecat_service import (
    PipecatVoiceService,
    CallContext,
    VoiceServiceConfig,
)

logger = logging.getLogger(__name__)


@dataclass
class CallSession:
    """Represents an active call session."""
    
    call_id: str
    user_id: str
    agent_id: str
    context: CallContext
    started_at: datetime
    components: Optional[dict] = None
    task: Optional[asyncio.Task] = None


class PipecatManagerError(Exception):
    """Base exception for Pipecat manager errors."""
    pass


class PipecatPipelineManager:
    """
    Manages active Pipecat pipeline sessions.
    
    Singleton pattern for centralized session management.
    """

    _instance: Optional['PipecatPipelineManager'] = None
    _lock = asyncio.Lock()

    def __new__(cls):
        """Singleton pattern to ensure single manager instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize pipeline manager."""
        if getattr(self, '_initialized', False):
            return
            
        self.active_sessions: Dict[str, CallSession] = {}
        self.voice_service = PipecatVoiceService()
        self._initialized = True
        logger.info("Pipecat pipeline manager initialized")

    async def create_session(
        self,
        call_id: str,
        user_id: str,
        agent_id: str,
        context: CallContext,
        config: Optional[VoiceServiceConfig] = None,
    ) -> CallSession:
        """
        Create a new call session with Pipecat components.
        
        Args:
            call_id: Unique call identifier
            user_id: User ID who initiated the call
            agent_id: Agent configuration ID
            context: Call context with prompts and variables
            config: Optional voice service configuration
            
        Returns:
            Created CallSession instance
            
        Raises:
            PipecatManagerError: If session creation fails
        """
        async with self._lock:
            if call_id in self.active_sessions:
                logger.warning(f"Session {call_id} already exists")
                raise PipecatManagerError(f"Session {call_id} already active")

            try:
                logger.info(f"Creating session for call {call_id}")
                
                # Create voice service with custom config if provided
                voice_service = PipecatVoiceService(config) if config else self.voice_service
                
                # Create pipeline components
                components = await voice_service.create_pipeline_components(context)
                
                # Create session
                session = CallSession(
                    call_id=call_id,
                    user_id=user_id,
                    agent_id=agent_id,
                    context=context,
                    started_at=datetime.utcnow(),
                    components=components,
                )
                
                # Store session
                self.active_sessions[call_id] = session
                
                logger.info(f"✅ Session {call_id} created with pipeline components")
                return session
                
            except Exception as e:
                logger.error(f"Failed to create session {call_id}: {e}", exc_info=True)
                raise PipecatManagerError(f"Session creation failed: {str(e)}")

    async def end_session(self, call_id: str) -> None:
        """
        End a call session and cleanup resources.
        
        Args:
            call_id: Call identifier
        """
        async with self._lock:
            session = self.active_sessions.get(call_id)
            if not session:
                logger.warning(f"Session {call_id} not found for cleanup")
                return

            try:
                logger.info(f"Ending session {call_id}")
                
                # Cancel running task
                if session.task and not session.task.done():
                    session.task.cancel()
                    try:
                        await session.task
                    except asyncio.CancelledError:
                        logger.debug(f"Task for {call_id} cancelled")
                
                # Remove from active sessions
                del self.active_sessions[call_id]
                
                duration = (datetime.utcnow() - session.started_at).total_seconds()
                logger.info(f"✅ Session {call_id} ended after {duration:.2f}s")
                
            except Exception as e:
                logger.error(f"Error ending session {call_id}: {e}", exc_info=True)

    def get_session(self, call_id: str) -> Optional[CallSession]:
        """
        Get an active session by call ID.
        
        Args:
            call_id: Call identifier
            
        Returns:
            CallSession if found, None otherwise
        """
        return self.active_sessions.get(call_id)

    def get_active_sessions(self) -> Dict[str, CallSession]:
        """
        Get all active sessions.
        
        Returns:
            Dictionary of active sessions
        """
        return self.active_sessions.copy()

    def get_session_count(self) -> int:
        """
        Get count of active sessions.
        
        Returns:
            Number of active sessions
        """
        return len(self.active_sessions)


# Global singleton instance
_manager: Optional[PipecatPipelineManager] = None


def get_pipeline_manager() -> PipecatPipelineManager:
    """
    Get the global pipeline manager instance.
    
    Returns:
        PipecatPipelineManager singleton instance
    """
    global _manager
    if _manager is None:
        _manager = PipecatPipelineManager()
    return _manager
