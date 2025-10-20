"""
RTVI Analytics Observer for tracking voice call events.

This module provides analytics tracking for Pipecat voice calls
without depending on specific Pipecat frame types.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

from backend.database import get_supabase_client

logger = logging.getLogger(__name__)


class AnalyticsEvent:
    """Constants for analytics event types."""
    
    USER_STARTED_SPEAKING = "user_started_speaking"
    USER_STOPPED_SPEAKING = "user_stopped_speaking"
    USER_INTERRUPTION = "user_interruption"
    TRANSCRIPTION = "transcription"
    LLM_RESPONSE_START = "llm_response_start"
    LLM_RESPONSE_END = "llm_response_end"
    SENTIMENT_SHIFT = "sentiment_shift"
    KEYWORD_DETECTED = "keyword_detected"
    CALL_STARTED = "call_started"
    CALL_ENDED = "call_ended"


class AnalyticsObserver:
    """
    Analytics Observer for tracking call events.
    
    Captures events during voice calls and stores them
    in Supabase for analytics and reporting.
    """

    def __init__(
        self,
        call_id: str,
        scenario_type: str,
        emergency_keywords: Optional[list[str]] = None,
    ):
        """
        Initialize analytics observer.
        
        Args:
            call_id: Database call ID for event association
            scenario_type: Scenario type (driver_checkin, emergency_protocol)
            emergency_keywords: Keywords to detect for emergency scenarios
        """
        self.call_id = call_id
        self.scenario_type = scenario_type
        self.emergency_keywords = emergency_keywords or [
            "emergency", "accident", "breakdown", "help", "injury"
        ]
        
        # Analytics tracking
        self.metrics = {
            "interruption_count": 0,
            "sentiment_shifts": 0,
            "keywords_detected": 0,
            "user_speaking_time": 0.0,
            "agent_speaking_time": 0.0,
            "total_tokens": 0,
            "llm_calls": 0,
        }
        
        self.user_speaking_start: Optional[datetime] = None
        self.agent_speaking: bool = False
        
        self.db_client = get_supabase_client()
        logger.info(f"Analytics observer initialized for call {call_id}")

    async def track_user_started_speaking(self) -> None:
        """Track when user starts speaking."""
        self.user_speaking_start = datetime.utcnow()
        
        # Check for interruption
        if self.agent_speaking:
            self.metrics["interruption_count"] += 1
            await self._log_event(
                AnalyticsEvent.USER_INTERRUPTION,
                {"interruption_number": self.metrics["interruption_count"]}
            )
            logger.debug(f"User interruption detected (#{self.metrics['interruption_count']})")
        
        await self._log_event(AnalyticsEvent.USER_STARTED_SPEAKING)

    async def track_user_stopped_speaking(self) -> None:
        """Track when user stops speaking."""
        if self.user_speaking_start:
            duration = (datetime.utcnow() - self.user_speaking_start).total_seconds()
            self.metrics["user_speaking_time"] += duration
            self.user_speaking_start = None
        
        await self._log_event(AnalyticsEvent.USER_STOPPED_SPEAKING)

    async def track_transcription(self, text: str, role: str = "user") -> None:
        """
        Track transcription and detect keywords.
        
        Args:
            text: Transcribed text
            role: Speaker role (user or agent)
        """
        text_lower = text.lower()
        
        # Detect emergency keywords
        for keyword in self.emergency_keywords:
            if keyword.lower() in text_lower:
                self.metrics["keywords_detected"] += 1
                await self._log_event(
                    AnalyticsEvent.KEYWORD_DETECTED,
                    {
                        "keyword": keyword,
                        "text": text,
                        "role": role,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                logger.info(f"Emergency keyword detected: {keyword}")
        
        await self._log_event(
            AnalyticsEvent.TRANSCRIPTION,
            {"text": text, "role": role}
        )

    async def track_llm_start(self) -> None:
        """Track LLM response start."""
        self.agent_speaking = True
        self.metrics["llm_calls"] += 1
        await self._log_event(AnalyticsEvent.LLM_RESPONSE_START)

    async def track_llm_end(self, tokens: int = 0) -> None:
        """
        Track LLM response end and token usage.
        
        Args:
            tokens: Number of tokens used
        """
        self.agent_speaking = False
        
        if tokens > 0:
            self.metrics["total_tokens"] += tokens
        
        await self._log_event(
            AnalyticsEvent.LLM_RESPONSE_END,
            {"tokens": self.metrics["total_tokens"]}
        )

    async def track_call_started(self) -> None:
        """Track call started event."""
        await self._log_event(AnalyticsEvent.CALL_STARTED)

    async def track_call_ended(self) -> None:
        """Track call ended event."""
        await self._log_event(AnalyticsEvent.CALL_ENDED)

    async def _log_event(
        self,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an analytics event to the database.
        
        Args:
            event_type: Type of event
            event_data: Additional event data
        """
        try:
            data = {
                "call_id": self.call_id,
                "event_type": event_type,
                "event_data": event_data or {},
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            self.db_client.table("analytics_events").insert(data).execute()
            logger.debug(f"Logged event: {event_type}")
            
        except Exception as e:
            logger.error(f"Failed to log event {event_type}: {e}", exc_info=True)

    async def save_final_metrics(
        self,
        duration_ms: int,
        llm_cost: Decimal = Decimal("0.0"),
        tts_cost: Decimal = Decimal("0.0"),
        stt_cost: Decimal = Decimal("0.0"),
    ) -> None:
        """
        Save final call analytics metrics.
        
        Args:
            duration_ms: Total call duration in milliseconds
            llm_cost: Total LLM cost
            tts_cost: Total TTS cost
            stt_cost: Total STT cost
        """
        try:
            total_cost = llm_cost + tts_cost + stt_cost
            
            analytics_data = {
                "call_id": self.call_id,
                "total_duration_ms": duration_ms,
                "interruption_count": self.metrics["interruption_count"],
                "sentiment_shifts": self.metrics["sentiment_shifts"],
                "keywords_detected": self.metrics["keywords_detected"],
                "tokens_spent": self.metrics["total_tokens"],
                "llm_cost": float(llm_cost),
                "tts_cost": float(tts_cost),
                "stt_cost": float(stt_cost),
                "total_cost": float(total_cost),
            }
            
            self.db_client.table("call_analytics").insert(analytics_data).execute()
            logger.info(f"✅ Final metrics saved for call {self.call_id}")
            
        except Exception as e:
            logger.error(f"Failed to save final metrics: {e}", exc_info=True)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current analytics metrics.
        
        Returns:
            Dictionary of current metrics
        """
        return self.metrics.copy()
