"""
Voice bot implementation with Pipecat.

Creates a complete voice bot that:
- Speaks first with initial greeting
- Listens to user input
- Responds intelligently
- Provides real-time transcription
"""

import logging
from typing import List, Dict, Any

from pipecat.frames.frames import (
    Frame,
    LLMMessagesFrame,
    TextFrame,
    EndFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.processors.aggregators.llm_response import (
    LLMAssistantResponseAggregator,
    LLMUserResponseAggregator,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.services.openai import OpenAILLMService
from pipecat.services.cartesia import CartesiaTTSService
from pipecat.services.deepgram import DeepgramSTTService

from backend.config import get_settings
from backend.observers.analytics_observer import AnalyticsObserver

logger = logging.getLogger(__name__)


class TranscriptLogger(FrameProcessor):
    """
    Processor that logs transcripts and sends them via callback.
    """

    def __init__(self, on_transcript_callback=None, analytics_observer=None):
        """
        Initialize transcript logger.
        
        Args:
            on_transcript_callback: Callback function for transcript events
            analytics_observer: Analytics observer for event tracking
        """
        super().__init__()
        self.on_transcript = on_transcript_callback
        self.analytics_observer = analytics_observer

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Process frames and extract transcripts."""
        await super().process_frame(frame, direction)

        # Track frame processing in analytics
        if self.analytics_observer:
            frame_type = type(frame).__name__
            direction_str = "upstream" if direction == FrameDirection.UPSTREAM else "downstream"
            await self.analytics_observer.track_frame_processing(frame_type, direction_str)

        # Track user transcripts (from STT)
        if isinstance(frame, TextFrame) and direction == FrameDirection.UPSTREAM:
            text = frame.text
            logger.info(f"👤 User: {text}")
            
            # Send to frontend via callback
            if self.on_transcript:
                await self.on_transcript({
                    "type": "transcript",
                    "text": text,
                    "role": "user",
                })
            
            # Track in analytics
            if self.analytics_observer:
                await self.analytics_observer.track_transcription(text, "user")
        
        # Track agent responses (from LLM)
        elif isinstance(frame, TextFrame) and direction == FrameDirection.DOWNSTREAM:
            text = frame.text
            logger.info(f"🤖 Agent: {text}")
            
            # Send to frontend via callback
            if self.on_transcript:
                await self.on_transcript({
                    "type": "transcript",
                    "text": text,
                    "role": "agent",
                })
            
            # Track in analytics
            if self.analytics_observer:
                await self.analytics_observer.track_transcription(text, "agent")

        return frame


async def create_voice_bot(
    call_id: str,
    system_prompt: str,
    initial_greeting: str,
    scenario_type: str,
    emergency_keywords: List[str],
    on_transcript_callback=None,
    voice_config: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Create a complete voice bot pipeline.
    
    Args:
        call_id: Database call ID
        system_prompt: System instructions for the agent
        initial_greeting: First message agent will say
        scenario_type: Scenario type (driver_checkin, emergency_protocol)
        emergency_keywords: Keywords to detect
        on_transcript_callback: Callback for transcript events
        voice_config: Voice service configuration
        
    Returns:
        Configured Pipeline ready to run
    """
    settings = get_settings()
    config = voice_config or {}
    
    logger.info(f"Creating voice bot for call {call_id}")
    
    # ============================================
    # 1. Create Services
    # ============================================
    
    # STT - Deepgram (Speech to Text)
    stt = DeepgramSTTService(
        api_key=settings.deepgram_api_key,
        model=config.get("deepgram_model", "nova-2"),
        language=config.get("language", "en"),
    )
    
    # TTS - Cartesia (Text to Speech)
    tts = CartesiaTTSService(
        api_key=settings.cartesia_api_key,
        voice_id=config.get("cartesia_voice_id", "a0e99841-438c-4a64-b679-ae501e7d6091"),
    )
    
    # LLM - OpenAI
    llm = OpenAILLMService(
        api_key=settings.openai_api_key,
        model=config.get("openai_model", "gpt-4-turbo-preview"),
    )
    
    # ============================================
    # 2. Create Analytics Observer
    # ============================================
    
    analytics_observer = AnalyticsObserver(
        call_id=call_id,
        scenario_type=scenario_type,
        emergency_keywords=emergency_keywords,
    )
    
    # ============================================
    # 3. Create Transcript Logger
    # ============================================
    
    transcript_logger = TranscriptLogger(
        on_transcript_callback=on_transcript_callback,
        analytics_observer=analytics_observer,
    )
    
    # ============================================
    # 4. Create Response Aggregators
    # ============================================
    
    user_aggregator = LLMUserResponseAggregator()
    assistant_aggregator = LLMAssistantResponseAggregator()
    
    # ============================================
    # 5. Build Initial Messages (Agent speaks first!)
    # ============================================
    
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "assistant",
            "content": initial_greeting,
        },
    ]
    
    logger.info("✅ Voice bot configured - agent will speak first")
    logger.debug(f"Initial greeting: {initial_greeting}")
    
    # ============================================
    # 6. Create Pipeline
    # ============================================
    
    pipeline = Pipeline([
        stt,                      # Input: Audio → Text
        user_aggregator,          # Aggregate user messages
        llm,                      # Process with AI
        assistant_aggregator,     # Aggregate AI responses
        transcript_logger,        # Log transcripts
        tts,                      # Output: Text → Audio
    ])
    
    # ============================================
    # 7. Return Complete Bot Configuration
    # ============================================
    
    return {
        "pipeline": pipeline,
        "messages": messages,
        "analytics_observer": analytics_observer,
        "initial_greeting": initial_greeting,
        "stt": stt,
        "tts": tts,
        "llm": llm,
        "user_aggregator": user_aggregator,
        "assistant_aggregator": assistant_aggregator,
    }


async def run_voice_bot(
    bot_data: Dict[str, Any],
    transport,
) -> None:
    """
    Run the voice bot pipeline.
    
    Args:
        bot_data: Dictionary containing pipeline and config
        transport: Transport layer for audio I/O
    """
    try:
        pipeline = bot_data["pipeline"]
        messages = bot_data["messages"]
        
        # Create pipeline task
        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                allow_interruptions=True,
                enable_metrics=True,
                enable_usage_metrics=True,
            ),
        )
        
        # Set initial context (this makes agent speak first!)
        await task.queue_frame(LLMMessagesFrame(messages))
        
        # Run the pipeline
        runner = PipelineRunner()
        await runner.run(task)
        
        logger.info("✅ Voice bot pipeline completed")
        
    except Exception as e:
        logger.error(f"Voice bot error: {e}", exc_info=True)
        raise

