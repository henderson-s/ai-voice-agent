/**
 * WebSocket utilities for Pipecat voice calls.
 * 
 * Provides functional interface for managing WebSocket connections
 * and audio streaming with the Pipecat backend.
 */

import { API_URL } from '../config';

export interface TranscriptMessage {
  type: 'transcript';
  text: string;
  role: 'user' | 'agent';
  timestamp: number;
}

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

export interface WebSocketCallbacks {
  onTranscript?: (transcript: TranscriptMessage) => void;
  onStatus?: (status: string) => void;
  onError?: (error: string) => void;
}

interface WebSocketState {
  ws: WebSocket | null;
  mediaStream: MediaStream | null;
  audioContext: AudioContext | null;
  processor: ScriptProcessorNode | null;
  outputAudioContext: AudioContext | null;
  startSent: boolean;
  callbacks: WebSocketCallbacks;
}

/**
 * Create and manage a Pipecat WebSocket connection for voice calls.
 * 
 * @param callId - The call ID to connect to
 * @param callbacks - Callback functions for events
 * @returns Object with control functions
 */
export function createPipecatWebSocket(callId: string, callbacks: WebSocketCallbacks = {}) {
  const state: WebSocketState = {
    ws: null,
    mediaStream: null,
    audioContext: null,
    processor: null,
    outputAudioContext: null,
    startSent: false,
    callbacks,
  };

  /**
   * Connect to WebSocket server.
   */
  async function connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = API_URL.replace('http', 'ws') + `/ws/call/${callId}`;
        state.ws = new WebSocket(wsUrl);

        state.ws.onopen = () => {
          console.log('✅ WebSocket connected');
          resolve();
        };

        state.ws.onmessage = (event) => {
          if (event.data instanceof ArrayBuffer || event.data instanceof Blob) {
            playAudio(event.data);
          } else {
            try {
              const message = JSON.parse(event.data);
              handleMessage(message);
            } catch (e) {
              console.error('Failed to parse message:', e);
            }
          }
        };

        state.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          state.callbacks.onError?.('WebSocket connection error');
          reject(error);
        };

        state.ws.onclose = () => {
          console.log('WebSocket closed');
          cleanup();
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Start capturing and streaming audio from microphone.
   */
  async function startAudio(): Promise<void> {
    try {
      // Request microphone access
      state.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000,
        },
      });

      // Create audio context for processing
      state.audioContext = new AudioContext({ sampleRate: 16000 });
      const source = state.audioContext.createMediaStreamSource(state.mediaStream);

      // Create processor for audio data
      state.processor = state.audioContext.createScriptProcessor(4096, 1, 1);

      state.processor.onaudioprocess = (event) => {
        if (state.ws && state.ws.readyState === WebSocket.OPEN) {
          const audioData = event.inputBuffer.getChannelData(0);
          
          // Convert float32 to int16 PCM
          const int16Data = new Int16Array(audioData.length);
          for (let i = 0; i < audioData.length; i++) {
            const s = Math.max(-1, Math.min(1, audioData[i]));
            int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
          }

          // Send audio data to backend
          state.ws.send(int16Data.buffer);
        }
      };

      source.connect(state.processor);
      state.processor.connect(state.audioContext.destination);

      // Send start message ONLY ONCE
      if (!state.startSent) {
        console.log('📤 Sending start message to backend');
        sendMessage({ type: 'start' });
        state.startSent = true;
      }
      
      console.log('🎤 Audio streaming started');
    } catch (error) {
      console.error('Failed to start audio:', error);
      state.callbacks.onError?.('Failed to access microphone');
      throw error;
    }
  }

  /**
   * Stop audio streaming and end call.
   */
  async function stopAudio(): Promise<void> {
    sendMessage({ type: 'stop' });
    cleanup();
  }

  /**
   * Handle incoming WebSocket messages.
   */
  function handleMessage(message: WebSocketMessage): void {
    console.log('📨 Received:', message.type, message);

    switch (message.type) {
      case 'ready':
        state.callbacks.onStatus?.('ready');
        break;

      case 'started':
        state.callbacks.onStatus?.('started');
        console.log('✅ Call started - agent will speak first');
        break;

      case 'transcript':
        console.log(`📝 Transcript [${message.role}]: ${message.text}`);
        if (state.callbacks.onTranscript) {
          state.callbacks.onTranscript({
            type: 'transcript',
            text: message.text,
            role: message.role || 'user',
            timestamp: message.timestamp || Date.now(),
          });
        }
        break;

      case 'stopped':
        state.callbacks.onStatus?.('stopped');
        cleanup();
        break;

      case 'error':
        console.error('❌ WebSocket error:', message.error);
        state.callbacks.onError?.(message.error || 'Unknown error');
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  }

  /**
   * Send JSON message to backend.
   */
  function sendMessage(message: any): void {
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
      state.ws.send(JSON.stringify(message));
    } else {
      console.warn('Cannot send message - WebSocket not open');
    }
  }

  /**
   * Play incoming audio from agent.
   */
  async function playAudio(audioData: ArrayBuffer | Blob): Promise<void> {
    try {
      // Create output audio context if not exists
      if (!state.outputAudioContext) {
        state.outputAudioContext = new AudioContext({ sampleRate: 16000 });
      }

      // Convert Blob to ArrayBuffer if needed
      let arrayBuffer: ArrayBuffer;
      if (audioData instanceof Blob) {
        arrayBuffer = await audioData.arrayBuffer();
      } else {
        arrayBuffer = audioData;
      }

      // Convert Int16 PCM to Float32 for Web Audio API
      const int16Array = new Int16Array(arrayBuffer);
      const float32Array = new Float32Array(int16Array.length);
      
      for (let i = 0; i < int16Array.length; i++) {
        float32Array[i] = int16Array[i] / 32768.0;
      }

      // Create audio buffer
      const audioBuffer = state.outputAudioContext.createBuffer(
        1, // mono
        float32Array.length,
        16000 // sample rate
      );

      // Copy data to buffer
      audioBuffer.getChannelData(0).set(float32Array);

      // Create source and play
      const source = state.outputAudioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(state.outputAudioContext.destination);
      source.start();

      console.log('🔊 Playing agent audio');
    } catch (error) {
      console.error('Failed to play audio:', error);
    }
  }

  /**
   * Cleanup all resources.
   */
  function cleanup(): void {
    console.log('🧹 Cleaning up WebSocket resources');

    // Stop audio processing
    if (state.processor) {
      state.processor.disconnect();
      state.processor = null;
    }

    // Close input audio context
    if (state.audioContext) {
      state.audioContext.close();
      state.audioContext = null;
    }

    // Close output audio context
    if (state.outputAudioContext) {
      state.outputAudioContext.close();
      state.outputAudioContext = null;
    }

    // Stop media stream
    if (state.mediaStream) {
      state.mediaStream.getTracks().forEach((track) => track.stop());
      state.mediaStream = null;
    }

    // Close WebSocket
    if (state.ws) {
      state.ws.close();
      state.ws = null;
    }

    console.log('✅ Cleanup complete');
  }

  /**
   * Check if WebSocket is connected.
   */
  function isConnected(): boolean {
    return state.ws !== null && state.ws.readyState === WebSocket.OPEN;
  }

  // Return public API
  return {
    connect,
    startAudio,
    stopAudio,
    isConnected,
    cleanup,
  };
}
