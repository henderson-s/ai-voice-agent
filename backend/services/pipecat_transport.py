"""
WebSocket Transport for Pipecat Pipeline.

This module provides a transport layer that connects Pipecat pipelines
to WebSocket connections for real-time audio streaming.
"""

import logging
import asyncio
from typing import Optional, Callable, Any, Dict
from io import BytesIO

from pipecat.transports.base_transport import BaseTransport
from pipecat.frames.frames import Frame, AudioRawFrame, TextFrame, LLMMessagesFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams

logger = logging.getLogger(__name__)


class WebSocketTransport(BaseTransport):
    """
    WebSocket transport for Pipecat pipelines.
    
    Handles bidirectional audio streaming between browser and Pipecat pipeline.
    """
    
    def __init__(
        self,
        websocket,
        call_id: str,
        on_transcript_callback: Optional[Callable] = None,
        on_audio_callback: Optional[Callable] = None,
    ):
        """
        Initialize WebSocket transport.
        
        Args:
            websocket: FastAPI WebSocket connection
            call_id: Call identifier
            on_transcript_callback: Callback for transcript events
            on_audio_callback: Callback for audio output
        """
        super().__init__()
        self.websocket = websocket
        self.call_id = call_id
        self.on_transcript = on_transcript_callback
        self.on_audio = on_audio_callback
        
        # Audio processing state
        self.audio_buffer = bytearray()
        self.buffer_size = 16000 * 2  # 1 second of 16kHz 16-bit audio
        self.is_connected = False
        
        logger.info(f"WebSocket transport initialized for call {call_id}")

    async def start(self) -> None:
        """Start the transport."""
        self.is_connected = True
        logger.info("WebSocket transport started")

    async def stop(self) -> None:
        """Stop the transport."""
        self.is_connected = False
        logger.info("WebSocket transport stopped")

    async def send_audio(self, audio: bytes) -> None:
        """
        Send audio data to client.
        
        Args:
            audio: Raw audio bytes (16kHz, 16-bit PCM)
        """
        try:
            if self.is_connected and self.websocket:
                await self.websocket.send_bytes(audio)
                logger.debug(f"Sent {len(audio)} bytes of audio to client")
        except Exception as e:
            logger.error(f"Failed to send audio: {e}", exc_info=True)

    async def send_transcript(self, text: str, role: str = "agent") -> None:
        """
        Send transcript to client.
        
        Args:
            text: Transcript text
            role: Speaker role (user or agent)
        """
        try:
            if self.on_transcript:
                await self.on_transcript({
                    "type": "transcript",
                    "text": text,
                    "role": role,
                })
            logger.debug(f"Transcript [{role}]: {text}")
        except Exception as e:
            logger.error(f"Failed to send transcript: {e}", exc_info=True)

    async def process_audio_input(self, audio_bytes: bytes) -> None:
        """
        Process incoming audio from client.
        
        Args:
            audio_bytes: Raw audio bytes from client
        """
        try:
            # Buffer audio
            self.audio_buffer.extend(audio_bytes)
            
            # When we have enough audio, process it
            if len(self.audio_buffer) >= self.buffer_size:
                await self._process_audio_chunk()
                
        except Exception as e:
            logger.error(f"Error processing audio: {e}", exc_info=True)
    
    async def _process_audio_chunk(self) -> None:
        """Process buffered audio chunk."""
        try:
            # Get audio chunk
            audio_chunk = bytes(self.audio_buffer)
            self.audio_buffer = bytearray()  # Clear buffer
            
            # Create AudioRawFrame for Pipecat pipeline
            audio_frame = AudioRawFrame(
                audio=audio_chunk,
                sample_rate=16000,
                num_channels=1,
            )
            
            # Send to pipeline
            await self._send_frame_to_pipeline(audio_frame)
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}", exc_info=True)

    async def _send_frame_to_pipeline(self, frame: Frame) -> None:
        """
        Send frame to Pipecat pipeline.
        
        Args:
            frame: Pipecat frame to process
        """
        try:
            # This will be implemented when we connect to the pipeline
            # For now, we'll store the frame for processing
            if hasattr(self, 'pipeline_task') and self.pipeline_task:
                await self.pipeline_task.queue_frame(frame)
            else:
                logger.warning("No pipeline task available for frame processing")
                
        except Exception as e:
            logger.error(f"Error sending frame to pipeline: {e}", exc_info=True)

    async def _handle_pipeline_output(self, frame: Frame) -> None:
        """
        Handle output from Pipecat pipeline.
        
        Args:
            frame: Output frame from pipeline
        """
        try:
            if isinstance(frame, AudioRawFrame):
                # Send audio to client
                await self.send_audio(frame.audio)
                
            elif isinstance(frame, TextFrame):
                # Send transcript to client
                await self.send_transcript(frame.text, "agent")
                
        except Exception as e:
            logger.error(f"Error handling pipeline output: {e}", exc_info=True)

    def set_pipeline_task(self, task: PipelineTask) -> None:
        """
        Set the pipeline task for this transport.
        
        Args:
            task: Pipecat pipeline task
        """
        self.pipeline_task = task
        logger.info("Pipeline task connected to transport")


class PipecatPipelineRunner:
    """
    Runner for Pipecat pipelines with WebSocket transport.
    
    Manages the complete pipeline lifecycle including:
    - Pipeline creation and configuration
    - Transport setup
    - Pipeline execution
    - Cleanup
    """
    
    def __init__(
        self,
        call_id: str,
        websocket,
        system_prompt: str,
        initial_greeting: str,
        scenario_type: str,
        emergency_keywords: list[str],
        on_transcript_callback: Optional[Callable] = None,
        on_audio_callback: Optional[Callable] = None,
    ):
        """
        Initialize pipeline runner.
        
        Args:
            call_id: Call identifier
            websocket: WebSocket connection
            system_prompt: System instructions
            initial_greeting: Initial agent message
            scenario_type: Scenario type
            emergency_keywords: Emergency detection keywords
            on_transcript_callback: Transcript callback
            on_audio_callback: Audio callback
        """
        self.call_id = call_id
        self.websocket = websocket
        self.system_prompt = system_prompt
        self.initial_greeting = initial_greeting
        self.scenario_type = scenario_type
        self.emergency_keywords = emergency_keywords
        self.on_transcript = on_transcript_callback
        self.on_audio = on_audio_callback
        
        # Pipeline components
        self.transport: Optional[WebSocketTransport] = None
        self.pipeline: Optional[Pipeline] = None
        self.task: Optional[PipelineTask] = None
        self.runner: Optional[PipelineRunner] = None
        
        # Execution state
        self.is_running = False
        self.is_started = False
        
        logger.info(f"Pipeline runner initialized for call {call_id}")

    async def create_pipeline(self) -> None:
        """Create the Pipecat pipeline with all components."""
        try:
            from backend.bot.voice_bot import create_voice_bot
            
            logger.info(f"Creating Pipecat pipeline for call {self.call_id}")
            
            # Create transport
            self.transport = WebSocketTransport(
                websocket=self.websocket,
                call_id=self.call_id,
                on_transcript_callback=self.on_transcript,
                on_audio_callback=self.on_audio,
            )
            
            # Create voice bot pipeline
            bot_data = await create_voice_bot(
                call_id=self.call_id,
                system_prompt=self.system_prompt,
                initial_greeting=self.initial_greeting,
                scenario_type=self.scenario_type,
                emergency_keywords=self.emergency_keywords,
                on_transcript_callback=self.on_transcript,
            )
            
            self.pipeline = bot_data["pipeline"]
            
            # Create pipeline task
            self.task = PipelineTask(
                self.pipeline,
                params=PipelineParams(
                    allow_interruptions=True,
                    enable_metrics=True,
                    enable_usage_metrics=True,
                ),
            )
            
            # Connect transport to task
            self.transport.set_pipeline_task(self.task)
            
            # Create runner
            self.runner = PipelineRunner()
            
            logger.info("✅ Pipecat pipeline created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create pipeline: {e}", exc_info=True)
            raise

    async def start_pipeline(self) -> None:
        """Start the pipeline execution."""
        try:
            if self.is_started:
                logger.warning("Pipeline already started")
                return
                
            logger.info(f"Starting Pipecat pipeline for call {self.call_id}")
            
            # Start transport
            await self.transport.start()
            
            # Set initial messages (agent speaks first!)
            initial_messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "assistant", "content": self.initial_greeting},
            ]
            
            await self.task.queue_frame(LLMMessagesFrame(initial_messages))
            
            # Start pipeline execution
            self.is_running = True
            self.is_started = True
            
            # Run pipeline in background
            asyncio.create_task(self._run_pipeline())
            
            logger.info("✅ Pipecat pipeline started - agent will speak first!")
            
        except Exception as e:
            logger.error(f"Failed to start pipeline: {e}", exc_info=True)
            raise

    async def _run_pipeline(self) -> None:
        """Run the pipeline in background."""
        try:
            await self.runner.run(self.task)
            logger.info("✅ Pipeline execution completed")
        except Exception as e:
            logger.error(f"Pipeline execution error: {e}", exc_info=True)
        finally:
            self.is_running = False

    async def process_audio(self, audio_bytes: bytes) -> None:
        """
        Process incoming audio through the pipeline.
        
        Args:
            audio_bytes: Raw audio bytes from client
        """
        try:
            if self.transport and self.is_running:
                await self.transport.process_audio_input(audio_bytes)
            else:
                logger.warning("Pipeline not ready for audio processing")
        except Exception as e:
            logger.error(f"Error processing audio: {e}", exc_info=True)

    async def stop_pipeline(self) -> None:
        """Stop the pipeline execution."""
        try:
            logger.info(f"Stopping Pipecat pipeline for call {self.call_id}")
            
            # Stop transport
            if self.transport:
                await self.transport.stop()
            
            # Cancel pipeline task
            if self.task:
                await self.task.queue_frame(EndFrame())
            
            self.is_running = False
            self.is_started = False
            
            logger.info("✅ Pipecat pipeline stopped")
            
        except Exception as e:
            logger.error(f"Error stopping pipeline: {e}", exc_info=True)

    def is_pipeline_running(self) -> bool:
        """Check if pipeline is currently running."""
        return self.is_running
