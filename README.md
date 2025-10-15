# 🤖 AI Voice Agent for Logistics Operations

An intelligent voice calling system powered by Retell AI that handles driver check-ins and emergency situations through natural phone conversations.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Local Setup](#local-setup)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This system enables automated, intelligent voice conversations with truck drivers for:

1. **Driver Check-ins**: Status updates, location tracking, ETA collection
2. **Emergency Protocol**: Accident/breakdown handling with safety assessment

The AI agent:
- Speaks naturally with backchannel responses ("mm-hmm", "I see")
- Uses dynamic variables (driver name, load number)
- Detects emergencies mid-conversation
- Extracts structured data automatically
- Escalates to human dispatchers when needed

---

## ✨ Features

### Core Capabilities
- ✅ **AI-Powered Voice Calls** via Retell AI
- ✅ **Web & Phone Calling** support
- ✅ **Real-time Transcription** during calls
- ✅ **Automatic Data Extraction** from conversations
- ✅ **Emergency Detection** with safety protocols
- ✅ **Dynamic Greetings** with driver/load info
- ✅ **Multi-scenario Support** (check-in vs emergency)

### Extracted Data (Normal Check-in)
- Call outcome (in-transit update, arrival confirmation)
- Driver status (driving, arrived, unloading, delayed)
- Current location (highway, mile marker, exit)
- ETA (estimated arrival time)
- Delay reasons
- Unloading status
- POD reminder acknowledgment

### Extracted Data (Emergency)
- Emergency type (accident, breakdown, medical, flat tire)
- Safety status
- Injury status
- Emergency location
- Load security status
- Escalation tracking

---

## 🛠 Tech Stack

### Backend
- **FastAPI** (Python 3.11+) - API framework
- **Supabase** - PostgreSQL database with RLS
- **Retell AI** - Voice AI platform
- **httpx** - Async HTTP client
- **Pydantic** - Data validation

### Frontend
- **React 19** with TypeScript
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **Retell Client SDK** - Web calling

### Infrastructure
- **ngrok** (for local webhook testing)
- **Supabase** (database & auth)
- **Retell AI** (voice processing)

---

## 🏗 Architecture

```
┌─────────────┐
│   Frontend  │  React App (Web Calling UI)
│   (React)   │
└──────┬──────┘
       │
       ├─────────────────────┐
       │                     │
       ▼                     ▼
┌─────────────┐       ┌─────────────┐
│   Backend   │◄──────│  Retell AI  │
│  (FastAPI)  │       │   Service   │
└──────┬──────┘       └─────────────┘
       │                     │
       ▼                     │
┌─────────────┐              │
│  Supabase   │              │
│ (PostgreSQL)│              │
└─────────────┘              │
                             │
                  ┌──────────▼─────────┐
                  │   Driver's Phone   │
                  │  (Incoming Call)   │
                  └────────────────────┘
```

### Data Flow

1. **User** creates agent with custom prompts & settings
2. **Backend** syncs agent to Retell AI
3. **User** initiates call (web or phone)
4. **Retell AI** connects and conducts conversation
5. **Webhook** receives call_ended event
6. **Backend** fetches transcript & analysis
7. **AI** extracts structured data
8. **Database** stores results
9. **Frontend** displays structured information

---

## 📦 Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **Supabase Account** ([supabase.com](https://supabase.com))
- **Retell AI Account** ([retellai.com](https://retellai.com))
- **ngrok** (for local webhook testing)

---

## 🚀 Local Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd voice-agent-v2
```

### 2. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Or create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Database Setup

1. Create a new Supabase project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** in Supabase dashboard
3. Copy content from `db.sql` and execute it
4. This creates all tables, indexes, triggers, and RLS policies

### 5. Environment Variables

#### Backend `.env` (in root directory)

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# Retell AI
RETELL_API_KEY=your-retell-api-key

# Optional: Webhook Security
RETELL_WEBHOOK_SECRET=your-webhook-secret

# Server
PORT=8000
```

#### Frontend `.env` (in `frontend/` directory)

```env
VITE_BACKEND_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

### 6. Get API Keys

#### Supabase Keys
1. Go to your Supabase project
2. Navigate to **Settings** → **API**
3. Copy:
   - `URL` (SUPABASE_URL)
   - `anon public` key (SUPABASE_ANON_KEY)
   - `service_role` key (SUPABASE_SERVICE_KEY) - **Keep secret!**

#### Retell AI API Key
1. Sign up at [retellai.com](https://retellai.com)
2. Go to **Dashboard** → **API Keys**
3. Create new API key
4. Copy the key (RETELL_API_KEY)

### 7. Setup ngrok (for webhooks)

```bash
# Install ngrok
brew install ngrok  # macOS
# OR download from https://ngrok.com/download

# Start ngrok
ngrok http 8000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok-free.app`)

### 8. Configure Retell Webhooks

1. Go to Retell AI Dashboard
2. Navigate to **Settings** → **Webhooks**
3. Add webhook URL: `https://your-ngrok-url.ngrok-free.app/calls/webhook`
4. Enable events:
   - ✅ call_started
   - ✅ call_ended
   - ✅ call_analyzed
   - ✅ call_failed

---

## 🏃 Running the Application

### Start Backend

```bash
# From root directory
cd voice-agent-v2
./backend/run.sh

# OR manually
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will run on: `http://localhost:8000`

API Docs available at: `http://localhost:8000/docs`

### Start Frontend

```bash
# From frontend directory
cd frontend
npm run dev
```

Frontend will run on: `http://localhost:5173`

### Start ngrok (for webhooks)

```bash
# In a new terminal
ngrok http 8000
```

Keep ngrok running to receive webhooks from Retell AI.

---

## 💻 Usage

### 1. Create an Account

1. Go to `http://localhost:5173`
2. Click "Sign Up"
3. Enter email and password
4. Verify email (check Supabase dashboard if using test email)

### 2. Create an Agent

1. Navigate to **Agents** page
2. Click **"Create New Agent"**
3. Fill in:
   - **Name**: "Driver Check-in Agent"
   - **Scenario**: "driver_checkin" or "emergency_protocol"
   - **System Prompt**: Instructions for AI behavior
   - **Initial Greeting**: Use `{{driver_name}}` and `{{load_number}}`
4. Expand **Advanced Settings** (optional):
   - Enable backchannel: Yes
   - Ambient sound: call-center
   - Interruption sensitivity: 0.7
   - Responsiveness: 0.8
5. Click **"Create Agent"**

**Example Initial Greeting:**
```
Hi {{driver_name}}, this is Dispatch with a check call on load {{load_number}}. Can you give me an update on your status?
```

### 3. Make a Test Call

1. Go to **Test Call** page
2. Select your agent
3. Enter:
   - **Driver Name**: John Smith
   - **Load Number**: LOAD-12345
4. Click **"Start Web Call"** for browser-based testing
5. Speak naturally with the AI agent
6. End the call when done

### 4. View Results

After the call ends:
- Results display automatically (wait 5-10 seconds)
- View structured data:
  - Call Outcome: "In Transit Update"
  - Driver Status: "Driving"
  - Current Location: "I-10 near Phoenix"
  - ETA: "Tomorrow at 8 AM"
  - Delay Reason: "No delays"
- View full transcript
- Click **"Refresh Data"** if results don't appear

### 5. Call History

- Navigate to **Calls** page
- See all past calls
- Click **"View Details"** for structured results
- Delete old calls

---

## 📁 Project Structure

```
voice-agent-v2/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Environment configuration
│   ├── database.py             # Supabase client
│   ├── models/
│   │   ├── auth.py             # Auth models
│   │   ├── agent.py            # Agent models
│   │   └── call.py             # Call models
│   ├── routes/
│   │   ├── auth.py             # Auth endpoints
│   │   ├── agents.py           # Agent CRUD
│   │   └── calls.py            # Call management & webhooks
│   ├── services/
│   │   └── retell.py           # Retell AI integration
│   └── utils/
│       ├── auth.py             # JWT authentication
│       └── validators.py       # Phone/load validation
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── CallResultsDisplay.tsx  # Results UI
│   │   ├── pages/
│   │   │   ├── Login.tsx       # Login page
│   │   │   ├── Signup.tsx      # Signup page
│   │   │   ├── Agents.tsx      # Agent management
│   │   │   ├── TestCall.tsx    # Call testing
│   │   │   └── Calls.tsx       # Call history
│   │   ├── lib/
│   │   │   └── api.ts          # API client
│   │   └── App.tsx             # Main app
│   ├── package.json
│   └── vite.config.ts
├── db.sql                      # Database schema
├── README.md                   # This file
└── requirements.txt            # Python dependencies
```

---

## 📡 API Documentation

### Authentication

All endpoints require JWT token in header:
```
Authorization: Bearer <your_jwt_token>
```

### Endpoints

#### Agents
- `GET /agents` - List all agents
- `POST /agents` - Create new agent
- `GET /agents/{id}` - Get agent details
- `PUT /agents/{id}` - Update agent
- `DELETE /agents/{id}` - Delete agent

#### Calls
- `GET /calls` - List all calls
- `POST /calls/phone` - Initiate phone call
- `POST /calls/web` - Create web call
- `GET /calls/{id}` - Get call details
- `GET /calls/{id}/full` - Get call with transcript & results
- `POST /calls/{id}/refresh` - Refresh call data from Retell AI
- `DELETE /calls/{id}` - Delete call

#### Webhooks
- `POST /calls/webhook` - Retell AI webhook (no auth required)

Full API docs: `http://localhost:8000/docs`

---


## 📚 Additional Resources

- **Retell AI Docs**: https://docs.retellai.com
- **Supabase Docs**: https://supabase.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com

---

## 🤝 Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review backend logs: `tail -f backend.log`
3. Check browser console (F12)
4. Verify all environment variables are set correctly

---

## 📝 License

MIT License

---

## 🎯 Quick Start Checklist

- [ ] Supabase project created
- [ ] Database schema executed (`db.sql`)
- [ ] Backend `.env` configured
- [ ] Frontend `.env` configured
- [ ] Python dependencies installed
- [ ] Node dependencies installed
- [ ] ngrok installed and running
- [ ] Retell webhook configured
- [ ] Backend running on :8000
- [ ] Frontend running on :5173
- [ ] Test account created
- [ ] First agent created
- [ ] Test call successful

---

**Ready to start!** 🚀

Create your first agent and make a test call to see the AI in action!
