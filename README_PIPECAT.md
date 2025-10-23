# 🎙️ AI Voice Agent - Pipecat Edition

## Complete Migration Guide & Setup Instructions

---

## 📋 Table of Contents

- [Overview](#overview)
- [What Changed: Retell → Pipecat](#what-changed)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
- [How It Works](#how-it-works)
- [Making Your First Call](#making-your-first-call)
- [Analytics Dashboard](#analytics-dashboard)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)

---

## 🎯 Overview

An AI-powered voice calling system for logistics operations that handles driver check-ins and emergency situations through natural phone conversations. **Now powered by Pipecat with OpenAI, Cartesia, and Deepgram.**

### Key Features:
- ✅ **Self-hosted voice pipeline** (no vendor lock-in)
- ✅ **Real-time transcription** (see conversation as it happens)
- ✅ **Agent speaks first** with personalized greeting
- ✅ **Bidirectional audio streaming** via WebSocket
- ✅ **Cost tracking** per service (LLM, TTS, STT)
- ✅ **Analytics dashboard** with metrics and charts
- ✅ **Structured data extraction** from conversations

---

## 🔄 What Changed: Retell → Pipecat

### **Removed:**
- ❌ Retell AI SDK and API
- ❌ External webhook dependencies
- ❌ Vendor-specific limitations

### **Added:**
- ✅ **Pipecat Framework** - Open-source voice pipeline
- ✅ **OpenAI GPT-4** - Conversation intelligence
- ✅ **Cartesia TTS** - High-quality text-to-speech
- ✅ **Deepgram STT** - Accurate speech-to-text
- ✅ **WebSocket Audio Streaming** - Real-time communication
- ✅ **Analytics Tracking** - Comprehensive metrics
- ✅ **Cost Breakdown** - Per-service cost monitoring

### **Maintained:**
- ✅ All agent configurations
- ✅ Driver check-in scenario
- ✅ Emergency protocol scenario
- ✅ Structured data extraction
- ✅ Call history and results
- ✅ User authentication

---

## 🛠 Tech Stack

### **Backend**
- **FastAPI** - API framework
- **Pipecat** - Voice pipeline orchestration
- **OpenAI** - GPT-4 for conversations
- **Cartesia** - Text-to-speech synthesis
- **Deepgram** - Speech-to-text transcription
- **Supabase** - PostgreSQL database with RLS
- **WebSockets** - Real-time audio streaming

### **Frontend**
- **React 19** + TypeScript
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **Web Audio API** - Browser audio processing

---

## 📦 Prerequisites

### **Required:**
- **Python 3.11** (NOT 3.14 - Pipecat doesn't support it yet)
- **Node.js 18+**
- **Supabase Account** - [supabase.com](https://supabase.com)
- **OpenAI API Key** - [platform.openai.com](https://platform.openai.com/api-keys)
- **Cartesia API Key** - [cartesia.ai](https://cartesia.ai)
- **Deepgram API Key** - [console.deepgram.com](https://console.deepgram.com)

### **Python Version Note:**
```bash
# Check your Python version
python --version

# If you have Python 3.14, install 3.11:
brew install python@3.11

# Use Python 3.11 for this project
python3.11 -m venv venv
source venv/bin/activate
```

---

## 🚀 Setup Instructions

### **Step 1: Clone and Install Dependencies**

```bash
# Navigate to project
cd voice-agent-v2

# Backend setup
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend setup (in new terminal)
cd frontend
npm install
```

### **Step 2: Database Setup**

1. **Create Supabase Project**
   - Go to [supabase.com](https://supabase.com)
   - Create new project
   - Note your credentials

2. **Run Database Migration**
   - Go to **SQL Editor** in Supabase dashboard
   - Copy **ALL** contents from `db_complete_pipecat.sql`
   - Click **Run**

3. **Verify Tables Created**
   ```sql
   SELECT table_name 
   FROM information_schema.tables 
   WHERE table_schema = 'public' 
   ORDER BY table_name;
   ```
   
   **Expected tables:**
   - `agent_configurations`
   - `analytics_events`
   - `call_analytics`
   - `call_results`
   - `call_transcripts`
   - `calls`

### **Step 3: Environment Variables**

**Backend** - Create `backend/.env`:
```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-public-key
SUPABASE_SERVICE_KEY=your-service-role-key

# AI Services (REQUIRED)
OPENAI_API_KEY=sk-...
CARTESIA_API_KEY=...
DEEPGRAM_API_KEY=...

# Server Configuration
PORT=8000
HOST=0.0.0.0
ENVIRONMENT=development
LOG_LEVEL=INFO

# Pipecat Configuration
ENABLE_ANALYTICS=true
MAX_CALL_DURATION=600
```

**Frontend** - Create `frontend/.env`:
```env
VITE_BACKEND_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-public-key
```

### **Step 4: Start Services**

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
./run.sh

# Terminal 2: Frontend
cd frontend
npm run dev
```

**Backend runs on:** `http://localhost:8000`  
**Frontend runs on:** `http://localhost:5173`

---

## 🎙️ How It Works

### **Complete Call Flow:**

```
1. User clicks "Start Web Call"
   ↓
2. Frontend creates call via /calls/web API
   ↓
3. Backend creates session with CallContext
   ↓
4. Frontend opens WebSocket to /ws/call/{id}
   ↓
5. Backend accepts connection, sends "ready"
   ↓
6. Frontend requests microphone access
   ↓
7. Frontend sends "start" message
   ↓
8. Backend creates AudioProcessor with:
   - OpenAI client for LLM
   - Deepgram for STT
   - Cartesia for TTS
   ↓
9. 🎤 AGENT SPEAKS FIRST!
   - Initial greeting sent to frontend
   - Example: "Hi John, this is Dispatch with a check call on load LOAD-12345..."
   ↓
10. User speaks into microphone
   ↓
11. Audio captured (16kHz, 16-bit PCM, mono)
   ↓
12. Sent to backend via WebSocket (binary)
   ↓
13. Backend buffers audio (1 second chunks)
   ↓
14. Sent to Deepgram API → Transcribed to text
   ↓
15. Text sent to frontend → Displayed in transcript
   ↓
16. Text sent to OpenAI GPT-4 → Response generated
   ↓
17. Response sent to frontend → Displayed in transcript
   ↓
18. Response sent to Cartesia → Audio synthesized
   ↓
19. Audio sent to frontend → Played in browser
   ↓
20. Conversation continues...
   ↓
21. User ends call
   ↓
22. Backend analyzes conversation with OpenAI
   ↓
23. Structured data extracted and saved
   ↓
24. Analytics metrics calculated and saved
   ↓
25. Results displayed in frontend
```

### **Architecture:**

```
┌─────────────────────────────────────────────┐
│         Browser (Frontend)                  │
│  - Microphone capture                       │
│  - Audio streaming (WebSocket)             │
│  - Transcript display                       │
│  - Audio playback                          │
└──────────────┬──────────────────────────────┘
               │ WebSocket
               │ (ws://localhost:8000/ws/call/{id})
               │
┌──────────────▼──────────────────────────────┐
│      FastAPI Backend                        │
│  ┌──────────────────────────────────────┐  │
│  │  WebSocket Handler                   │  │
│  │  - Receives audio bytes              │  │
│  │  - Sends transcripts                 │  │
│  │  - Sends audio responses             │  │
│  └──────────┬───────────────────────────┘  │
│             │                                │
│  ┌──────────▼───────────────────────────┐  │
│  │  AudioProcessor                      │  │
│  │  ┌────────────────────────────────┐ │  │
│  │  │ Deepgram → OpenAI → Cartesia   │ │  │
│  │  │   (STT)      (LLM)     (TTS)    │ │  │
│  │  └────────────────────────────────┘ │  │
│  └──────────┬───────────────────────────┘  │
└─────────────┼────────────────────────────────┘
              │
┌─────────────▼────────────────────────────────┐
│         Supabase (PostgreSQL)                │
│  - calls, call_transcripts, call_results    │
│  - call_analytics, analytics_events         │
└──────────────────────────────────────────────┘
```

---

## 📞 Making Your First Call

### **1. Create an Account**
1. Go to `http://localhost:5173`
2. Click "Sign Up"
3. Create account

### **2. Create an Agent**
1. Navigate to **Agents**
2. Click **"Create New Agent"**
3. Fill in:
   - **Name:** "Dispatch Agent"
   - **Scenario:** "driver_checkin"
   - **System Prompt:**
     ```
     You are a professional dispatch agent calling truck drivers.
     Ask about their status, location, ETA, and any delays.
     Be conversational and professional.
     ```
   - **Initial Greeting:**
     ```
     Hi {{driver_name}}, this is Dispatch with a check call on load {{load_number}}. Can you give me an update on your status?
     ```
4. Click **Create**

### **3. Make a Test Call**
1. Navigate to **Test Call**
2. Select your agent
3. Enter:
   - **Driver Name:** "John Smith"
   - **Load Number:** "LOAD-12345"
4. Click **"🎙️ Start Web Call"**
5. **Allow microphone** when browser asks
6. **Listen** to agent's greeting: "Hi John Smith, this is Dispatch with a check call on load LOAD-12345..."
7. **Speak:** "Hey, I'm on I-10 near Phoenix, should arrive around 3 PM"
8. **See your words** appear in transcript after ~1 second
9. **See and hear** agent's response
10. **Continue conversation**
11. Click **"End Call"** when done

### **4. View Results**
- Structured data displays automatically
- See extracted information:
  - Call outcome
  - Driver status
  - Current location
  - ETA
  - Delays
- View full transcript
- Check analytics

---

## 📊 Analytics Dashboard

Navigate to **Analytics** to see:

### **Key Metrics Cards:**
- 📞 **Total Calls** - Number of calls made
- ⏱️ **Average Duration** - Average call length
- 💰 **Total Cost** - Sum of all service costs
- 🔄 **Interruptions** - User interruption count

### **Cost Breakdown:**
- **LLM (OpenAI)** - Conversation processing costs
- **TTS (Cartesia)** - Speech synthesis costs
- **STT (Deepgram)** - Transcription costs
- **Total** - Sum with percentage breakdown

### **Token Usage:**
- Total tokens across all calls
- Average tokens per call
- Usage metrics

### **Call Outcomes:**
- Distribution chart
- Call counts per outcome type
- Percentage breakdown

### **Additional Stats:**
- Average interruptions per call
- Cost per call
- Tokens per call

---

## 🐛 Troubleshooting

### **Issue: "Python 3.14 not supported"**
```bash
# Install Python 3.11
brew install python@3.11

# Create new venv
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **Issue: "Table call_analytics does not exist"**
**Solution:** Run the database migration `db_complete_pipecat.sql` in Supabase SQL Editor

### **Issue: "Microphone not working"**
- Must use HTTPS or localhost
- Check browser microphone permissions
- Try different browser

### **Issue: "Can't hear agent"**
- Check browser audio permissions
- Verify Cartesia API key is valid
- Check browser console for audio errors

### **Issue: "Agent speaks twice"**
**Fixed in latest version** - Restart both backend and frontend

### **Issue: "User speech not transcribed"**
- Speak clearly and loudly
- Wait ~1 second for transcription
- Check Deepgram API key is valid
- Verify backend logs show "User said: ..."

### **Issue: "Analytics showing 0"**
1. Check if migration was run
2. Make a complete call (start and end properly)
3. Check backend logs for "Analytics saved successfully"
4. Run this in Supabase to populate test data:
   ```sql
   INSERT INTO call_analytics (call_id, total_duration_ms, tokens_spent, llm_cost, tts_cost, stt_cost, total_cost)
   SELECT id, 60000, 350, 0.0035, 0.0018, 0.0013, 0.0066
   FROM calls WHERE id NOT IN (SELECT call_id FROM call_analytics) LIMIT 5;
   ```

### **Issue: "Duplicate initial messages"**
**Solution:** Make sure both backend and frontend are restarted after latest updates

---

## 📡 API Reference

### **REST Endpoints:**

#### **Agents:**
```bash
GET    /agents              # List all agents
POST   /agents              # Create agent
GET    /agents/{id}         # Get agent details
PATCH  /agents/{id}         # Update agent
DELETE /agents/{id}         # Delete agent
```

#### **Calls:**
```bash
GET    /calls               # List all calls
POST   /calls/web           # Create web call
GET    /calls/{id}          # Get call details
GET    /calls/{id}/full     # Get call with transcript & results
POST   /calls/{id}/end      # End active call
DELETE /calls/{id}          # Delete call
```

#### **Analytics:**
```bash
GET    /analytics/metrics              # Comprehensive overview
GET    /analytics/summary              # High-level summary
GET    /analytics/cost-breakdown       # Service-wise costs
GET    /analytics/outcomes             # Call outcome distribution
GET    /analytics/call/{id}            # Call-specific analytics
GET    /analytics/events/{id}          # Event timeline for call
```

### **WebSocket Endpoint:**

```
ws://localhost:8000/ws/call/{call_id}
```

**Client → Server Messages:**
```json
{"type": "start"}           // Start call processing
{"type": "stop"}            // Stop call
[Binary Audio Data]         // 16kHz, 16-bit PCM audio
```

**Server → Client Messages:**
```json
{"type": "ready", "call_id": "..."}                           // Connection ready
{"type": "started", "call_id": "..."}                         // Call started
{"type": "transcript", "text": "...", "role": "agent|user"}   // Transcript update
{"type": "stopped", "call_id": "..."}                         // Call stopped
{"type": "error", "error": "..."}                            // Error occurred
[Binary Audio Data]                                           // Agent's speech audio
```

---

## 🎨 Features in Detail

### **1. Agent Speaks First**
- Initial greeting is sent immediately when call starts
- Dynamic variables replaced: `{{driver_name}}`, `{{load_number}}`
- Example: "Hi John Smith, this is Dispatch with a check call on load LOAD-12345..."

### **2. Real-Time Transcription**
- User speech transcribed as you speak (~1 second delay)
- Agent responses shown before audio plays
- Speaker labels (👤 You, 🤖 Agent)
- Auto-scrolling transcript panel

### **3. Structured Data Extraction**
After call ends, AI analyzes and extracts:

**Driver Check-in:**
- Call outcome (in_transit_update, arrival_confirmation, etc.)
- Driver status (driving, arrived, delayed)
- Current location
- ETA
- Delay reason
- Unloading status
- POD reminder acknowledgment

**Emergency Protocol:**
- Emergency type (accident, breakdown, medical, flat_tire)
- Safety status
- Injury status
- Emergency location
- Load security status

### **4. Analytics Tracking**
Automatically tracks:
- Call duration (milliseconds)
- Token usage (per call and total)
- Cost breakdown (LLM, TTS, STT)
- Interruption count (future feature)
- Keywords detected (future feature)
- Sentiment shifts (future feature)

---

## 💰 Cost Tracking

### **How Costs Are Calculated:**

**OpenAI (LLM):**
- ~$0.01 per 1,000 tokens
- Tracked from API usage response

**Cartesia (TTS):**
- ~$0.05 per 1,000 characters
- Calculated from agent response length

**Deepgram (STT):**
- ~$0.0125 per minute
- Calculated from call duration

**Total:**
- Sum of all three services
- Displayed per call and in aggregate

---

## 📁 Project Structure

```
voice-agent-v2/
├── backend/
│   ├── main.py                      # FastAPI app with WebSocket
│   ├── config.py                    # Settings (OpenAI, Cartesia, Deepgram)
│   ├── database.py                  # Supabase client
│   ├── models/
│   │   ├── agent.py                 # Agent models (with Pipecat fields)
│   │   ├── call.py                  # Call models
│   │   └── auth.py                  # Auth models
│   ├── routes/
│   │   ├── agents.py                # Agent CRUD (no Retell)
│   │   ├── calls.py                 # Call management (Pipecat)
│   │   ├── analytics.py             # Analytics endpoints
│   │   └── auth.py                  # Authentication
│   ├── services/
│   │   ├── pipecat_service.py       # Pipecat components
│   │   ├── pipecat_manager.py       # Session management
│   │   ├── audio_processor.py       # Audio processing pipeline
│   │   ├── analytics_service.py     # Analytics queries
│   │   └── call_analyzer.py         # Result extraction
│   ├── websockets/
│   │   └── call_handler.py          # WebSocket audio streaming
│   ├── observers/
│   │   └── analytics_observer.py    # RTVI event tracking
│   ├── bot/
│   │   └── voice_bot.py             # Voice bot implementation
│   ├── utils/
│   │   ├── auth.py                  # JWT authentication
│   │   ├── call_processor.py        # Call data processing
│   │   ├── database_helpers.py      # DB utilities
│   │   └── ...
│   └── requirements.txt             # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Agents.tsx           # Agent management
│   │   │   ├── TestCall.tsx         # Web calling interface
│   │   │   ├── Calls.tsx            # Call history
│   │   │   ├── Analytics.tsx        # Analytics dashboard
│   │   │   ├── Login.tsx            # Authentication
│   │   │   └── Register.tsx
│   │   ├── components/
│   │   │   ├── agents/              # Agent UI components
│   │   │   ├── calls/               # Call UI components
│   │   │   ├── layout/              # Layout components
│   │   │   └── ui/                  # Reusable UI components
│   │   ├── utils/
│   │   │   └── websocket.ts         # WebSocket client
│   │   ├── lib/
│   │   │   └── api.ts               # API client
│   │   └── types/
│   │       └── index.ts             # TypeScript types
│   └── package.json
├── db_complete_pipecat.sql          # Complete database schema
└── README_PIPECAT.md                # This file
```

---

## 🔐 Security

### **Row Level Security (RLS):**
- All data is user-scoped
- Users can only see their own:
  - Agents
  - Calls
  - Transcripts
  - Results
  - Analytics

### **API Keys:**
- Never commit `.env` files
- Use different keys for dev/prod
- Rotate keys periodically
- Service role key bypasses RLS (for webhooks/background jobs)

---

## 🎯 Testing Checklist

- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Can create account
- [ ] Can create agents
- [ ] Can start web call
- [ ] Microphone permission granted
- [ ] Hear agent's initial greeting
- [ ] See agent's greeting in transcript
- [ ] Speak and see transcription appear
- [ ] Hear agent's response
- [ ] End call successfully
- [ ] See structured results
- [ ] Analytics dashboard shows data

---

## 📈 Performance Tips

### **Reduce Latency:**
- Use `gpt-4-turbo-preview` instead of `gpt-4` (faster)
- Adjust buffer size in audio_processor.py (trade-off: latency vs accuracy)
- Use faster Deepgram model: `nova-2-general` or `base`

### **Reduce Costs:**
- Use `gpt-3.5-turbo` for simpler conversations
- Reduce max_tokens in responses
- Use shorter system prompts

### **Improve Accuracy:**
- Speak clearly and loudly
- Reduce background noise
- Use better microphone
- Increase buffer size for better transcription

---

## 🔧 Configuration Options

### **Agent Configuration:**

All agents support these fields:

**AI Providers:**
- `llm_provider` - Default: "openai"
- `llm_model` - Default: "gpt-4-turbo-preview"
- `tts_provider` - Default: "cartesia"
- `tts_voice_id` - Cartesia voice ID
- `stt_provider` - Default: "deepgram"

**Conversation Settings:**
- `interruption_sensitivity` - 0.0 to 1.0
- `responsiveness` - 0.0 to 1.0
- `enable_backchannel` - True/False
- `backchannel_words` - ["mm-hmm", "I see", ...]
- `enable_filler_words` - True/False

**Call Duration:**
- `max_call_duration_seconds` - Default: 600 (10 minutes)
- `enable_auto_end_call` - Auto-end on silence
- `end_call_after_silence_ms` - Default: 10000 (10 seconds)

**Keywords:**
- `emergency_keywords` - For emergency detection
- `reminder_keywords` - For POD reminders

---

## 📚 Additional Resources

- **Pipecat Docs:** https://docs.pipecat.ai
- **OpenAI API:** https://platform.openai.com/docs
- **Cartesia Docs:** https://docs.cartesia.ai
- **Deepgram API:** https://developers.deepgram.com
- **Supabase Docs:** https://supabase.com/docs

---

## 🎊 Success!

You now have a fully functional, self-hosted voice agent system with:
- ✅ Real-time voice conversations
- ✅ Automatic data extraction
- ✅ Comprehensive analytics
- ✅ Cost tracking
- ✅ Professional UI
- ✅ Clean, maintainable code

**Start making calls and enjoy your Pipecat-powered voice agent!** 🚀🎙️

---

## 💡 Quick Commands Reference

```bash
# Start backend
cd backend && ./run.sh

# Start frontend
cd frontend && npm run dev

# Check Python version
python --version

# Install dependencies
pip install -r backend/requirements.txt
npm install

# View API docs
http://localhost:8000/docs

# Access application
http://localhost:5173
```

---

**Questions or issues?** Check the troubleshooting section above or review the backend logs for detailed error messages.

