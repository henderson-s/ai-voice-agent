"""
WebSocket handler for Pipecat voice calls.

Manages real-time bidirectional audio streaming between
browser and Pipecat voice pipeline.
"""

import logging
import json
import asyncio
from typing import Optional, Dict, Any

from fastapi import WebSocket, WebSocketDisconnect

from backend.services.pipecat_manager import get_pipeline_manager
from backend.services.pipecat_service import get_pipecat_service
from backend.observers.analytics_observer import AnalyticsObserver
from backend.database import get_supabase_client

logger = logging.getLogger(__name__)


class CallWebSocketHandler:
    """
    Handles WebSocket connections for voice calls.
    
    Manages bidirectional audio streaming and integrates
    with Pipecat pipelines for voice processing.
    """

    def __init__(self, websocket: WebSocket, call_id: str):
        """
        Initialize WebSocket handler.
        
        Args:
            websocket: FastAPI WebSocket connection
            call_id: Database call ID
        """
        self.websocket = websocket
        self.call_id = call_id
        self.pipeline_manager = get_pipeline_manager()
        self.pipecat_service = get_pipecat_service()
        self.session = None
        self.running = False
        self.db_client = get_supabase_client()
        self.pipeline_runner = None
        logger.info(f"WebSocket handler initialized for call {call_id}")

    async def handle_connection(self) -> None:
        """
        Handle WebSocket connection lifecycle.
        
        Manages the complete flow from connection to disconnection,
        including pipeline setup, audio streaming, and cleanup.
        """
        try:
            # Accept WebSocket connection
            await self.websocket.accept()
            logger.info(f"WebSocket connected for call {self.call_id}")
            
            # Get session from pipeline manager
            self.session = self.pipeline_manager.get_session(self.call_id)
            if not self.session:
                await self._send_error("Call session not found")
                await self.websocket.close()
                return
            
            # Update call status
            self._update_call_status("in_progress")
            
            # Send ready message
            await self._send_message({
                "type": "ready",
                "call_id": self.call_id,
                "message": "Connected to voice pipeline"
            })
            
            # Start message processing loop
            self.running = True
            await self._message_loop()
            
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for call {self.call_id}")
        except Exception as e:
            logger.error(f"WebSocket error for call {self.call_id}: {e}", exc_info=True)
            await self._send_error(str(e))
        finally:
            await self._cleanup()

    async def _message_loop(self) -> None:
        """
        Main message processing loop.
        
        Receives messages from client and processes them
        through the Pipecat pipeline.
        """
        try:
            while self.running:
                # Receive message from client
                data = await self.websocket.receive()
                
                # Handle different message types
                if "text" in data:
                    await self._handle_text_message(data["text"])
                elif "bytes" in data:
                    await self._handle_audio_data(data["bytes"])
                    
        except WebSocketDisconnect:
            logger.info(f"Client disconnected from call {self.call_id}")
            self.running = False
        except Exception as e:
            logger.error(f"Error in message loop: {e}", exc_info=True)
            self.running = False

    async def _handle_text_message(self, message: str) -> None:
        """
        Handle text messages from client.
        
        Args:
            message: JSON string message from client
        """
        try:
            msg = json.loads(message)
            msg_type = msg.get("type")
            
            logger.debug(f"Received message type: {msg_type}")
            
            if msg_type == "start":
                await self._handle_start()
            elif msg_type == "stop":
                await self._handle_stop()
            elif msg_type == "transcript":
                await self._handle_transcript(msg.get("text", ""))
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON message: {e}")
        except Exception as e:
            logger.error(f"Error handling text message: {e}", exc_info=True)

    async def _handle_audio_data(self, audio_bytes: bytes) -> None:
        """
        Handle audio data from client.
        
        Processes through Pipecat pipeline: Audio → STT → LLM → TTS → Audio
        
        Args:
            audio_bytes: Raw audio data from client (16kHz, 16-bit PCM)
        """
        try:
            if not self.pipeline_runner:
                logger.warning("Pipeline runner not started")
                return
            
            # Send audio to Pipecat pipeline
            await self.pipeline_runner.process_audio(audio_bytes)
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}", exc_info=True)

    async def _handle_start(self) -> None:
        """Handle call start event and create Pipecat pipeline."""
        logger.info(f"Starting Pipecat pipeline for {self.call_id}")
        
        try:
            if not self.session:
                raise Exception("Session not found")
            
            # Create Pipecat pipeline runner
            self.pipeline_runner = await self.pipecat_service.create_pipeline_runner(
                call_id=self.call_id,
                websocket=self.websocket,
                context=self.session.context,
                on_transcript_callback=self._send_transcript,
                on_audio_callback=self._send_audio,
            )
            
            # Start the pipeline (agent will speak first!)
            await self.pipeline_runner.start_pipeline()
            
            # Send started status
            await self._send_message({
                "type": "started",
                "call_id": self.call_id,
            })
            
            self._update_call_status("in_progress")
            logger.info("✅ Pipecat pipeline started - agent will speak first!")
            
        except Exception as e:
            logger.error(f"Failed to start Pipecat pipeline: {e}", exc_info=True)
            await self._send_error(f"Failed to start call: {str(e)}")

    async def _handle_stop(self) -> None:
        """Handle call stop event and save results."""
        logger.info(f"Stopping call {self.call_id}")
        
        self.running = False
        
        # Stop Pipecat pipeline
        if self.pipeline_runner:
            await self.pipeline_runner.stop_pipeline()
        
        await self._send_message({
            "type": "stopped",
            "call_id": self.call_id,
        })
        
        # End the session
        await self.pipeline_manager.end_session(self.call_id)
        self._update_call_status("completed")

    async def _handle_transcript(self, text: str) -> None:
        """
        Handle transcript text from STT.
        
        Args:
            text: Transcribed text
        """
        logger.debug(f"Transcript: {text}")
        
        # Broadcast transcript to client
        await self._send_message({
            "type": "transcript",
            "text": text,
            "timestamp": asyncio.get_event_loop().time(),
        })

    async def _send_transcript(self, transcript_data: Dict[str, Any]) -> None:
        """
        Send transcript update to client (called by audio processor).
        
        Args:
            transcript_data: Transcript information
        """
        await self._send_message(transcript_data)

    async def _send_audio(self, audio_bytes: bytes) -> None:
        """
        Send audio data to client for playback.
        
        Args:
            audio_bytes: Audio bytes to send
        """
        try:
            # Send audio as binary message
            await self.websocket.send_bytes(audio_bytes)
            logger.debug(f"Sent {len(audio_bytes)} bytes of audio to client")
        except Exception as e:
            logger.error(f"Failed to send audio: {e}", exc_info=True)

    async def _send_message(self, message: Dict[str, Any]) -> None:
        """
        Send JSON message to client.
        
        Args:
            message: Message dictionary to send
        """
        try:
            await self.websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}", exc_info=True)

    async def _send_error(self, error: str) -> None:
        """
        Send error message to client.
        
        Args:
            error: Error message string
        """
        await self._send_message({
            "type": "error",
            "error": error,
        })

    def _update_call_status(self, status: str) -> None:
        """
        Update call status in database.
        
        Args:
            status: New call status
        """
        try:
            self.db_client.table("calls")\
                .update({"status": status})\
                .eq("id", self.call_id)\
                .execute()
            logger.debug(f"Updated call {self.call_id} status to {status}")
        except Exception as e:
            logger.error(f"Failed to update call status: {e}", exc_info=True)

    async def _cleanup(self) -> None:
        """Clean up resources and close connection."""
        logger.info(f"Cleaning up WebSocket for call {self.call_id}")
        
        try:
            # Stop Pipecat pipeline
            if self.pipeline_runner:
                await self.pipeline_runner.stop_pipeline()
                self.pipeline_runner = None
            
            # End session if still active
            if self.session:
                await self.pipeline_manager.end_session(self.call_id)
            
            # Update final status
            self._update_call_status("completed")
            
            # Close WebSocket if still open
            if not self.websocket.client_state.DISCONNECTED:
                await self.websocket.close()
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)

