// ============================================
// Core Types
// ============================================

export interface User {
  id: string;
  email: string;
  created_at: string;
}

// ============================================
// Agent Types
// ============================================

export type ScenarioType = 'driver_checkin' | 'emergency_protocol';

export type AmbientSound =
  | 'call-center'
  | 'coffee-shop'
  | 'convention-hall'
  | 'summer-outdoor'
  | 'mountain-outdoor'
  | 'static-noise'
  | 'off';

export interface AgentConfiguration {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  scenario_type: ScenarioType;
  system_prompt: string;
  initial_greeting: string;
  retell_agent_id?: string;
  retell_llm_id?: string;
  voice_id: string;
  language: string;
  enable_backchannel: boolean;
  backchannel_words: string[];
  enable_filler_words: boolean;
  filler_words: string[];
  interruption_sensitivity: number;
  response_delay_ms: number;
  responsiveness: number;
  ambient_sound: AmbientSound;
  ambient_sound_volume: number;
  max_call_duration_seconds: number;
  enable_auto_end_call: boolean;
  end_call_after_silence_ms: number;
  pronunciation_guide: Record<string, string>;
  reminder_keywords: string[];
  enable_reminder: boolean;
  emergency_keywords: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AgentCreateInput {
  name: string;
  description?: string;
  scenario_type: ScenarioType;
  system_prompt: string;
  initial_greeting: string;
  voice_id?: string;
  language?: string;
  enable_backchannel?: boolean;
  backchannel_words?: string[];
  enable_filler_words?: boolean;
  filler_words?: string[];
  interruption_sensitivity?: number;
  response_delay_ms?: number;
  responsiveness?: number;
  ambient_sound?: AmbientSound;
  ambient_sound_volume?: number;
  max_call_duration_seconds?: number;
  enable_auto_end_call?: boolean;
  end_call_after_silence_ms?: number;
  pronunciation_guide?: Record<string, string>;
  reminder_keywords?: string[];
  enable_reminder?: boolean;
  emergency_keywords?: string[];
}

export interface AgentUpdateInput extends Partial<AgentCreateInput> {
  is_active?: boolean;
}

// ============================================
// Call Types
// ============================================

export type CallType = 'phone' | 'web';
export type CallStatus = 'initiated' | 'in_progress' | 'completed' | 'failed' | 'ended';

export interface Call {
  id: string;
  user_id: string;
  agent_configuration_id: string;
  retell_call_id?: string;
  call_type: CallType;
  status: CallStatus;
  driver_name: string;
  phone_number?: string;
  load_number: string;
  started_at?: string;
  ended_at?: string;
  duration_seconds?: number;
  metadata?: Record<string, any>;
  recording_url?: string;
  public_log_url?: string;
  created_at: string;
  updated_at: string;
}

export interface PhoneCallInput {
  agent_configuration_id: string;
  driver_name: string;
  phone_number: string;
  load_number: string;
}

export interface WebCallInput {
  agent_configuration_id: string;
  driver_name: string;
  load_number: string;
}

export interface WebCallResponse {
  access_token: string;
  call_id: string;
}

// ============================================
// Transcript Types
// ============================================

export interface TranscriptEntry {
  role: 'agent' | 'user';
  content: string;
  timestamp?: string;
}

export interface CallTranscript {
  id: string;
  call_id: string;
  transcript: string;
  transcript_json?: TranscriptEntry[];
  created_at: string;
  updated_at: string;
}

// ============================================
// Call Results Types
// ============================================

export interface CallResults {
  id: string;
  call_id: string;
  scenario_type: ScenarioType;
  is_emergency: boolean;
  call_summary?: string;
  call_outcome?: string;
  // Normal check-in fields
  driver_status?: string;
  current_location?: string;
  eta?: string;
  delay_reason?: string;
  unloading_status?: string;
  dock_door?: string;
  pod_reminder_acknowledged?: boolean;
  // Emergency fields
  emergency_type?: string;
  is_safe?: boolean;
  injuries?: string;
  location_emergency?: string;
  load_secure?: boolean;
  safety_status?: string;
  injury_status?: string;
  escalation_status?: string;
  // Metadata
  analysis_data?: Record<string, any>;
  confidence_score?: number;
  processing_notes?: string;
  created_at: string;
  updated_at: string;
}

export interface FullCallDetails {
  call: Call;
  transcript?: CallTranscript;
  results?: CallResults;
}

// ============================================
// Auth Types
// ============================================

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// ============================================
// API Error Types
// ============================================

export interface APIError {
  detail: string;
  status?: number;
}

// ============================================
// UI State Types
// ============================================

export interface LoadingState {
  isLoading: boolean;
  error: string | null;
}

export interface FormState<T> extends LoadingState {
  data: T;
}
