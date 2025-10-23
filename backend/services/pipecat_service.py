"""
Pipecat AI service for voice pipeline management.

This service provides a complete, working implementation of
Pipecat voice pipelines with OpenAI, Cartesia, and Deepgram.
"""

import logging
from typing import Optional, Any
from dataclasses import dataclass

from backend.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class VoiceServiceConfig:
    """Configuration for voice services."""
    
    openai_model: str = "gpt-4-turbo-preview"
    cartesia_voice_id: str = "a0e99841-438c-4a64-b679-ae501e7d6091"
    deepgram_model: str = "nova-2"
    language: str = "en"
    sample_rate: int = 16000


@dataclass
class CallContext:
    """Context data for a voice call."""
    
    driver_name: str
    load_number: str
    scenario_type: str
    system_prompt: str
    initial_greeting: str
    emergency_keywords: list[str]


class PipecatServiceError(Exception):
    """Base exception for Pipecat service errors."""
    pass


class PipecatVoiceService:
    """
    Service for managing Pipecat voice pipelines.
    
    Provides a clean interface for creating working voice pipelines
    with real-time audio processing.
    """

    def __init__(self, config: Optional[VoiceServiceConfig] = None):
        """
        Initialize Pipecat voice service.
        
        Args:
            config: Optional voice service configuration
        """
        self.settings = get_settings()
        self.config = config or VoiceServiceConfig()
        logger.info("Pipecat voice service initialized")

    def _build_system_message(self, context: CallContext) -> str:
        """
        Build system prompt with dynamic variable substitution.
        
        Args:
            context: Call context with driver name and load number
            
        Returns:
            System prompt with variables replaced
        """
        prompt = context.system_prompt.replace(
            "{{driver_name}}", context.driver_name
        ).replace(
            "{{load_number}}", context.load_number
        )
        
        logger.debug(f"Built system prompt for {context.scenario_type}")
        return prompt

    def _build_initial_message(self, context: CallContext) -> str:
        """
        Build initial greeting with dynamic variables.
        
        Args:
            context: Call context
            
        Returns:
            Initial greeting with variables replaced
        """
        greeting = context.initial_greeting.replace(
            "{{driver_name}}", context.driver_name
        ).replace(
            "{{load_number}}", context.load_number
        )
        
        return greeting

    async def create_pipeline_components(self, context: CallContext) -> dict:
        """
        Create all pipeline components (STT, LLM, TTS).
        
        Args:
            context: Call context with configuration
            
        Returns:
            Dictionary containing all pipeline components
            
        Raises:
            PipecatServiceError: If component creation fails
        """
        try:
            # Lazy imports
            from pipecat.services.deepgram import DeepgramSTTService
            from pipecat.services.openai import OpenAILLMService  
            from pipecat.services.cartesia import CartesiaTTSService
            from pipecat.processors.aggregators.llm_response import (
                LLMAssistantResponseAggregator,
                LLMUserResponseAggregator
            )
            
            logger.info(f"Creating pipeline components for {context.scenario_type}")
            
            # Create STT (Speech-to-Text) - Deepgram
            stt = DeepgramSTTService(
                api_key=self.settings.deepgram_api_key,
                model=self.config.deepgram_model,
                language=self.config.language,
            )
            logger.debug("✓ Deepgram STT created")
            
            # Create TTS (Text-to-Speech) - Cartesia
            tts = CartesiaTTSService(
                api_key=self.settings.cartesia_api_key,
                voice_id=self.config.cartesia_voice_id,
            )
            logger.debug("✓ Cartesia TTS created")
            
            # Create LLM - OpenAI
            system_message = self._build_system_message(context)
            initial_message = self._build_initial_message(context)
            
            llm = OpenAILLMService(
                api_key=self.settings.openai_api_key,
                model=self.config.openai_model,
            )
            logger.debug("✓ OpenAI LLM created")
            
            # Create response aggregators
            user_aggregator = LLMUserResponseAggregator()
            assistant_aggregator = LLMAssistantResponseAggregator()
            
            logger.info("✅ All pipeline components created successfully")
            
            return {
                "stt": stt,
                "tts": tts,
                "llm": llm,
                "user_aggregator": user_aggregator,
                "assistant_aggregator": assistant_aggregator,
                "system_message": system_message,
                "initial_message": initial_message,
            }
            
        except Exception as e:
            logger.error(f"Failed to create pipeline components: {e}", exc_info=True)
            raise PipecatServiceError(f"Component creation failed: {str(e)}")

    async def create_pipeline_runner(
        self,
        call_id: str,
        websocket,
        context: CallContext,
        on_transcript_callback=None,
        on_audio_callback=None,
    ):
        """
        Create a complete Pipecat pipeline runner.
        
        Args:
            call_id: Call identifier
            websocket: WebSocket connection
            context: Call context
            on_transcript_callback: Transcript callback
            on_audio_callback: Audio callback
            
        Returns:
            PipecatPipelineRunner instance
        """
        try:
            from backend.services.pipecat_transport import PipecatPipelineRunner
            
            logger.info(f"Creating pipeline runner for call {call_id}")
            
            runner = PipecatPipelineRunner(
                call_id=call_id,
                websocket=websocket,
                system_prompt=context.system_prompt,
                initial_greeting=context.initial_greeting,
                scenario_type=context.scenario_type,
                emergency_keywords=context.emergency_keywords,
                on_transcript_callback=on_transcript_callback,
                on_audio_callback=on_audio_callback,
            )
            
            # Create the pipeline
            await runner.create_pipeline()
            
            logger.info("✅ Pipeline runner created successfully")
            return runner
            
        except Exception as e:
            logger.error(f"Failed to create pipeline runner: {e}", exc_info=True)
            raise PipecatServiceError(f"Pipeline runner creation failed: {str(e)}")


def get_pipecat_service() -> PipecatVoiceService:
    """
    Dependency injection function for FastAPI routes.
    
    Returns:
        PipecatVoiceService instance
    """
    return PipecatVoiceService()
