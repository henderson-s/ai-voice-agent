/**
 * Constants for Agent Configuration
 */

import type { AgentCreateInput, ScenarioType } from '../types';

export const DEFAULT_SYSTEM_PROMPT = `You are a professional dispatch agent calling truck drivers about their loads. Your role is to gather information and handle any situation that arises during the call.

NORMAL CHECK-IN FLOW:
- Start with an open-ended question about their current status
- If driving: ask about location, ETA, and any delays
- If arrived: ask about unloading status and timeline
- Always remind them about the POD (Proof of Delivery) at the end
- Be conversational, professional, and adaptive

EMERGENCY PROTOCOL:
If the driver mentions ANY emergency (accident, blowout, breakdown, medical issue, injury, etc.):
1. IMMEDIATELY switch to emergency mode
2. Confirm: "Are you safe right now?"
3. Ask: "Is anyone injured?"
4. Get: "What is your exact location?"
5. Verify: "Is the load secure?"
6. Say: "I'm connecting you to a human dispatcher right now for immediate assistance"

CONVERSATION STYLE:
- Be professional but warm
- Handle unclear responses by politely asking them to repeat
- If one-word answers, gently probe for detail
- Stay calm at all times
- Adapt your questions based on their responses
- Never be pushy or aggressive`;

export const DEFAULT_INITIAL_GREETING = 'Hi {{driver_name}}, this is Dispatch with a check call on load {{load_number}}. Can you give me an update on your status?';

export const DEFAULT_AGENT_FORM_DATA: AgentCreateInput = {
  name: '',
  description: '',
  scenario_type: 'driver_checkin' as ScenarioType,
  system_prompt: DEFAULT_SYSTEM_PROMPT,
  initial_greeting: DEFAULT_INITIAL_GREETING,
  voice_id: '11labs-Adrian',
  language: 'en-US',
  enable_backchannel: true,
  backchannel_words: ['mm-hmm', 'I see', 'got it', 'okay'],
  enable_filler_words: true,
  filler_words: ['um', 'uh', 'hmm', 'let me see'],
  interruption_sensitivity: 0.7,
  response_delay_ms: 800,
  responsiveness: 0.8,
  ambient_sound: 'call-center',
  ambient_sound_volume: 0.5,
  max_call_duration_seconds: 600,
  enable_auto_end_call: true,
  end_call_after_silence_ms: 10000,
  pronunciation_guide: {},
  reminder_keywords: ['POD', 'proof of delivery', 'paperwork'],
  enable_reminder: true,
  emergency_keywords: ['accident', 'crash', 'emergency', 'help', 'breakdown', 'broke down', 'medical', 'injury', 'blowout', 'flat tire', 'broke', 'stuck']
};

export const VOICE_OPTIONS = [
  { value: '11labs-Adrian', label: 'Adrian (Default)' },
];

export const LANGUAGE_OPTIONS = [
  { value: 'en-US', label: 'English (US)' },
  { value: 'es-ES', label: 'Spanish' },
];

export const SCENARIO_TYPE_OPTIONS = [
  { value: 'driver_checkin', label: 'Driver Check-in (Standard)' },
  { value: 'emergency_protocol', label: 'Emergency Protocol (Dynamic Pivot)' },
];

export const AMBIENT_SOUND_OPTIONS = [
  { value: 'call-center', label: 'Call Center' },
  { value: 'coffee-shop', label: 'Coffee Shop' },
  { value: 'convention-hall', label: 'Convention Hall' },
  { value: 'summer-outdoor', label: 'Summer Outdoor' },
  { value: 'mountain-outdoor', label: 'Mountain Outdoor' },
  { value: 'static-noise', label: 'Static Noise' },
];
