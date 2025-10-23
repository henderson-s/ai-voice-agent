"""
Direct audio processing without full Pipecat pipeline complexity.

This provides a working implementation that:
- Processes user audio with Deepgram
- Generates responses with OpenAI  
- Synthesizes speech with Cartesia
- Works with WebSocket streaming
"""

import logging
import asyncio
import base64
from typing import Dict, Any, Optional, Callable
from io import BytesIO

from openai import AsyncOpenAI
from backend.config import get_settings
from backend.database import get_supabase_client

logger = logging.getLogger(__name__)


class AudioProcessor:
    """
    Processes audio for voice calls using direct API integration.
    
    Simpler than full Pipecat pipeline but fully functional.
    """

    def __init__(
        self,
        call_id: str,
        system_prompt: str,
        initial_greeting: str,
        on_transcript_callback: Optional[Callable] = None,
        on_audio_callback: Optional[Callable] = None,
    ):
        """
        Initialize audio processor.
        
        Args:
            call_id: Call identifier
            system_prompt: System instructions
            initial_greeting: Agent's first message
            on_transcript_callback: Callback for transcript updates
            on_audio_callback: Callback for audio output
        """
        self.call_id = call_id
        self.system_prompt = system_prompt
        self.initial_greeting = initial_greeting
        self.on_transcript = on_transcript_callback
        self.on_audio = on_audio_callback
        
        settings = get_settings()
        
        # Initialize clients
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.deepgram_api_key = settings.deepgram_api_key
        self.cartesia_api_key = settings.cartesia_api_key
        self.scenario_type = None
        self.db_client = get_supabase_client()
        self.start_time = None
        self.total_tokens = 0
        
        # Conversation history
        self.messages = [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": initial_greeting},
        ]
        
        # Deepgram connection
        self.dg_connection = None
        
        # Flags
        self.started = False
        self.greeting_sent = False
        
        logger.info(f"Audio processor initialized for call {call_id}")

    async def start(self) -> None:
        """
        Start the audio processor.
        
        Sends initial greeting and sets up Deepgram connection.
        """
        try:
            if self.started:
                logger.warning("Audio processor already started")
                return
            
            logger.info("Starting audio processor")
            
            # Record start time
            from datetime import datetime
            self.start_time = datetime.utcnow()
            
            # Setup Deepgram first
            await self._setup_deepgram()
            
            # Send initial greeting ONCE (agent speaks first!)
            if not self.greeting_sent:
                logger.info("🎙️ Sending initial greeting TEXT ONLY (FIRST TIME)")
                
                if self.on_transcript:
                    await self.on_transcript({
                        "type": "transcript",
                        "text": self.initial_greeting,
                        "role": "agent",
                        "source": "initial_greeting",
                    })
                
                # DON'T send audio for initial greeting to avoid WebSocket disconnect
                # Audio will be sent for subsequent responses
                self.greeting_sent = True
                logger.info("✅ Initial greeting TEXT sent (no audio to prevent disconnect)")
            
            self.started = True
            logger.info("✅ Audio processor started - agent spoke first!")
            
        except Exception as e:
            logger.error(f"Failed to start audio processor: {e}", exc_info=True)
            raise

    async def _setup_deepgram(self) -> None:
        """Setup Deepgram for transcription (using REST API for simplicity)."""
        try:
            # We'll use REST API instead of WebSocket for more reliability
            # Audio will be buffered and sent in chunks
            self.audio_buffer = bytearray()
            self.buffer_size = 16000 * 2  # 1 second of 16kHz 16-bit audio
            logger.info("✅ Deepgram transcription ready (REST API mode)")
            
        except Exception as e:
            logger.error(f"Failed to setup Deepgram: {e}", exc_info=True)


    async def _generate_response(self) -> None:
        """Generate AI response using OpenAI."""
        try:
            logger.info("Generating AI response...")
            
            # Call OpenAI
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=self.messages,
                temperature=0.7,
                max_tokens=150,
            )
            
            assistant_message = response.choices[0].message.content
            
            # Track tokens
            if response.usage:
                self.total_tokens += response.usage.total_tokens
                logger.debug(f"Tokens used: {response.usage.total_tokens}, Total: {self.total_tokens}")
            
            logger.info(f"🤖 Agent responds: {assistant_message}")
            
            # Add to conversation history
            self.messages.append({
                "role": "assistant",
                "content": assistant_message,
            })
            
            # Send transcript to frontend
            if self.on_transcript:
                logger.info(f"📤 Sending agent response transcript to frontend")
                await self.on_transcript({
                    "type": "transcript",
                    "text": assistant_message,
                    "role": "agent",
                    "source": "llm_response",  # Debug marker
                })
            
            # Synthesize speech
            await self._synthesize_speech(assistant_message)
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}", exc_info=True)

    async def _synthesize_speech(self, text: str) -> None:
        """
        Synthesize speech using Cartesia.
        
        Args:
            text: Text to convert to speech
        """
        try:
            import httpx
            
            logger.debug(f"Synthesizing speech: {text[:50]}...")
            
            # Call Cartesia TTS API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.cartesia.ai/tts/bytes",
                    headers={
                        "X-API-Key": self.cartesia_api_key,
                        "Cartesia-Version": "2024-06-10",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model_id": "sonic-english",
                        "transcript": text,
                        "voice": {
                            "mode": "id",
                            "id": "a0e99841-438c-4a64-b679-ae501e7d6091"
                        },
                        "output_format": {
                            "container": "raw",
                            "encoding": "pcm_s16le",
                            "sample_rate": 16000,
                        },
                    },
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    audio_bytes = response.content
                    logger.info(f"✅ Generated {len(audio_bytes)} bytes of audio")
                    
                    # Send audio to frontend for playback
                    if self.on_audio:
                        await self.on_audio(audio_bytes)
                else:
                    logger.error(f"Cartesia API error: {response.status_code} - {response.text}")
                    
        except Exception as e:
            logger.error(f"Failed to synthesize speech: {e}", exc_info=True)

    async def process_audio_input(self, audio_bytes: bytes) -> None:
        """
        Process incoming audio from user.
        
        Args:
            audio_bytes: Raw audio bytes (16kHz, 16-bit PCM)
        """
        try:
            # Buffer audio
            self.audio_buffer.extend(audio_bytes)
            
            # When we have enough audio, transcribe it
            if len(self.audio_buffer) >= self.buffer_size:
                await self._transcribe_audio_chunk()
                
        except Exception as e:
            logger.error(f"Error processing audio: {e}", exc_info=True)
    
    async def _transcribe_audio_chunk(self) -> None:
        """Transcribe buffered audio using Deepgram REST API."""
        try:
            import httpx
            
            # Get audio chunk
            audio_chunk = bytes(self.audio_buffer)
            self.audio_buffer = bytearray()  # Clear buffer
            
            logger.debug(f"Transcribing {len(audio_chunk)} bytes with Deepgram")
            
            # Call Deepgram API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.deepgram.com/v1/listen",
                    params={
                        "model": "nova-2",
                        "language": "en",
                        "smart_format": "true",
                        "encoding": "linear16",
                        "sample_rate": "16000",
                        "channels": "1",
                    },
                    headers={
                        "Authorization": f"Token {self.deepgram_api_key}",
                    },
                    content=audio_chunk,
                    timeout=10.0,
                )
                
                if response.status_code == 200:
                    result = response.json()
                    transcript = result.get("results", {}).get("channels", [{}])[0].get("alternatives", [{}])[0].get("transcript", "")
                    
                    if transcript.strip():
                        logger.info(f"👤 User said: {transcript}")
                        await self._handle_user_transcript(transcript)
                    else:
                        logger.debug("Empty transcript from Deepgram")
                else:
                    error_text = response.text
                    logger.error(f"Deepgram API error: {response.status_code} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}", exc_info=True)
    
    async def _handle_user_transcript(self, transcript: str) -> None:
        """
        Handle transcribed user speech.
        
        Args:
            transcript: Transcribed text from user
        """
        try:
            # Send to frontend
            if self.on_transcript:
                await self.on_transcript({
                    "type": "transcript",
                    "text": transcript,
                    "role": "user",
                })
            
            # Add to conversation history
            self.messages.append({
                "role": "user",
                "content": transcript,
            })
            
            # Generate AI response
            await self._generate_response()
            
        except Exception as e:
            logger.error(f"Error handling transcript: {e}", exc_info=True)

    async def stop(self, scenario_type: str = "driver_checkin") -> None:
        """Stop the audio processor and save call results."""
        try:
            logger.info(f"Stopping audio processor for call {self.call_id}")
            
            # Process any remaining buffered audio
            if len(self.audio_buffer) > 0:
                await self._transcribe_audio_chunk()
            
            # Calculate call duration
            from datetime import datetime
            duration_ms = 0
            if self.start_time:
                duration = datetime.utcnow() - self.start_time
                duration_ms = int(duration.total_seconds() * 1000)
            
            # Analyze conversation and save results
            await self._save_call_results(scenario_type)
            
            # Save analytics
            await self._save_analytics(duration_ms)
            
            logger.info("✅ Audio processor stopped, results and analytics saved")
            
        except Exception as e:
            logger.error(f"Error stopping audio processor: {e}", exc_info=True)
    
    async def _save_call_results(self, scenario_type: str) -> None:
        """
        Analyze conversation and save results to database.
        
        Args:
            scenario_type: Scenario type for analysis schema
        """
        try:
            from backend.services.call_analyzer import get_call_analyzer
            from backend.utils.call_processor import build_results_data, save_or_update_results
            
            logger.info(f"Analyzing call {self.call_id} for results extraction")
            
            # Analyze conversation
            analyzer = get_call_analyzer()
            extracted_data = await analyzer.analyze_conversation(
                self.messages,
                scenario_type
            )
            
            if not extracted_data:
                logger.warning("No data extracted from conversation")
                return
            
            # Build results data
            results_data = {
                "call_id": self.call_id,
                "scenario_type": scenario_type,
                "is_emergency": extracted_data.get("is_emergency", False),
                "call_summary": extracted_data.get("call_summary", ""),
                "call_outcome": extracted_data.get("call_outcome"),
                "analysis_data": extracted_data,
            }
            
            # Add scenario-specific fields
            if not extracted_data.get("is_emergency"):
                results_data.update({
                    "driver_status": extracted_data.get("driver_status"),
                    "current_location": extracted_data.get("current_location"),
                    "eta": extracted_data.get("eta"),
                    "delay_reason": extracted_data.get("delay_reason"),
                    "unloading_status": extracted_data.get("unloading_status"),
                    "pod_reminder_acknowledged": extracted_data.get("pod_reminder_acknowledged"),
                })
            else:
                results_data.update({
                    "emergency_type": extracted_data.get("emergency_type"),
                    "safety_status": extracted_data.get("safety_status"),
                    "injury_status": extracted_data.get("injury_status"),
                    "location_emergency": extracted_data.get("location_emergency"),
                    "load_secure": extracted_data.get("load_secure"),
                })
            
            # Save to database
            save_or_update_results(self.db_client, self.call_id, results_data)
            
            # Save transcript
            conversation_text = "\n".join([
                f"{msg['role'].upper()}: {msg['content']}"
                for msg in self.messages
                if msg['role'] != 'system'
            ])
            
            # Check if transcript exists
            existing = self.db_client.table("call_transcripts")\
                .select("*")\
                .eq("call_id", self.call_id)\
                .execute()
            
            if not existing.data:
                self.db_client.table("call_transcripts").insert({
                    "call_id": self.call_id,
                    "transcript": conversation_text,
                    "transcript_json": self.messages,
                }).execute()
                logger.info("✅ Call transcript saved")
            
            logger.info("✅ Call results saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save call results: {e}", exc_info=True)

    async def _save_analytics(self, duration_ms: int) -> None:
        """
        Save analytics metrics to database.
        
        Args:
            duration_ms: Call duration in milliseconds
        """
        try:
            # Estimate costs (rough estimates)
            # OpenAI: ~$0.01 per 1K tokens for GPT-4
            llm_cost = (self.total_tokens / 1000) * 0.01
            
            # Cartesia: ~$0.05 per 1K characters
            total_agent_text = sum(
                len(msg["content"]) for msg in self.messages if msg["role"] == "assistant"
            )
            tts_cost = (total_agent_text / 1000) * 0.05
            
            # Deepgram: ~$0.0125 per minute
            stt_cost = (duration_ms / 60000) * 0.0125
            
            total_cost = llm_cost + tts_cost + stt_cost
            
            # Save to database
            analytics_data = {
                "call_id": self.call_id,
                "total_duration_ms": duration_ms,
                "interruption_count": 0,  # TODO: Track interruptions
                "sentiment_shifts": 0,
                "keywords_detected": 0,  # TODO: Track from observer
                "tokens_spent": self.total_tokens,
                "llm_cost": round(llm_cost, 4),
                "tts_cost": round(tts_cost, 4),
                "stt_cost": round(stt_cost, 4),
                "total_cost": round(total_cost, 4),
            }
            
            logger.info(f"💾 Saving analytics: {analytics_data}")
            result = self.db_client.table("call_analytics").insert(analytics_data).execute()
            logger.info(f"✅ Analytics saved successfully: ${total_cost:.4f}, {self.total_tokens} tokens, Duration: {duration_ms}ms")
            logger.debug(f"Database response: {result.data}")
            
        except Exception as e:
            logger.error(f"Failed to save analytics: {e}", exc_info=True)

    def get_conversation_history(self) -> list:
        """Get the conversation history."""
        return self.messages.copy()

