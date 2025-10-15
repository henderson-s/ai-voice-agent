# Voice Agent Backend

Professional FastAPI backend for AI-powered voice calling system.

## Features

- ✅ **RESTful API** with FastAPI
- ✅ **Supabase Integration** for database and authentication
- ✅ **Retell AI Integration** for voice calling
- ✅ **Professional Logging** with configurable levels
- ✅ **Global Error Handling** with detailed error messages
- ✅ **Type Safety** with comprehensive type hints
- ✅ **API Documentation** auto-generated at `/docs`

## Quick Start

### 1. Install Dependencies

```bash
pip install -r ../requirements.txt
```

### 2. Configure Environment

Create `.env` file in the `backend/` directory:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
RETELL_API_KEY=your-retell-api-key

# Optional configuration
PORT=8000
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 3. Run the Server

**Option A: Using the run script**
```bash
./run.sh
```

**Option B: Using Python directly**
```bash
cd ..
python -m backend.main
```

**Option C: Using uvicorn directly**
```bash
cd ..
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at: `http://localhost:8000`

## API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration and logging setup
├── database.py          # Supabase client wrapper
├── models/              # Pydantic models
│   ├── auth.py          # Authentication models
│   ├── agent.py         # Agent configuration models
│   └── call.py          # Call-related models
├── routes/              # API route handlers
│   ├── auth.py          # Authentication endpoints
│   ├── agents.py        # Agent CRUD endpoints
│   └── calls.py         # Call management & webhooks
├── services/            # Business logic layer
│   └── retell.py        # Retell AI service
├── utils/               # Utility functions
│   └── auth.py          # JWT authentication utilities
├── .env                 # Environment variables (create from .env.example)
├── .env.example         # Environment template
└── README.md            # This file
```

## API Endpoints

### Authentication (`/auth`)
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `GET /auth/me` - Get current user

### Agents (`/agents`)
- `GET /agents` - List all agents
- `POST /agents` - Create new agent
- `GET /agents/{id}` - Get agent details
- `PATCH /agents/{id}` - Update agent
- `DELETE /agents/{id}` - Delete agent

### Calls (`/calls`)
- `GET /calls` - List all calls
- `POST /calls/phone` - Initiate phone call
- `POST /calls/web` - Create web call
- `GET /calls/{id}` - Get call details
- `GET /calls/{id}/full` - Get call with transcript & results
- `POST /calls/{id}/refresh` - Refresh call data from Retell
- `DELETE /calls/{id}` - Delete call
- `POST /calls/webhook` - Retell AI webhook (no auth)

### Health (`/`)
- `GET /` - API information
- `GET /health` - Health check

## Logging

The application uses Python's built-in logging with professional formatting:

```
2025-01-16 10:30:45 - backend.services.retell - INFO - create_agent:90 - Creating agent: Driver Check-in Agent
```

### Log Levels

Set in `.env` with `LOG_LEVEL`:

- **DEBUG**: Detailed diagnostic information
- **INFO**: General operational events (default)
- **WARNING**: Non-critical issues
- **ERROR**: Error events with stack traces

Example:
```env
LOG_LEVEL=DEBUG  # For development
LOG_LEVEL=INFO   # For production
```

## Error Handling

The backend includes comprehensive error handling:

1. **HTTP Exceptions**: Proper status codes with detailed messages
2. **Validation Errors**: Detailed field-level validation feedback
3. **Unexpected Exceptions**: Safe error responses with logging
4. **All errors logged**: With full context for debugging

## Development

### Running with Auto-Reload

The server automatically reloads when code changes:

```bash
python -m uvicorn backend.main:app --reload
```

### Debugging

Enable DEBUG logging in `.env`:

```env
LOG_LEVEL=DEBUG
```

### Testing the API

Use the interactive documentation at `/docs` or tools like:

- **curl**: Command-line HTTP client
- **Postman**: GUI API client
- **httpie**: User-friendly CLI HTTP client

Example:
```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SUPABASE_URL` | Yes | - | Supabase project URL |
| `SUPABASE_KEY` | Yes | - | Supabase anon public key |
| `SUPABASE_SERVICE_KEY` | Yes | - | Supabase service role key |
| `RETELL_API_KEY` | Yes | - | Retell AI API key |
| `PORT` | No | 8000 | Server port |
| `HOST` | No | 0.0.0.0 | Server host |
| `ENVIRONMENT` | No | development | Environment name |
| `LOG_LEVEL` | No | INFO | Logging level |

## Troubleshooting

### Import Errors

Always run from the project root:
```bash
cd /path/to/voice-agent-v2
python -m backend.main
```

### .env File Not Found

Ensure `.env` is in the `backend/` directory:
```bash
ls backend/.env
```

### Database Connection Issues

Verify Supabase credentials:
- URL format: `https://xxx.supabase.co`
- Keys are valid and not expired
- Database schema is set up (run `db.sql`)

### Port Already in Use

Change the port in `.env`:
```env
PORT=8001
```

## Production Deployment

For production deployment:

1. Set environment variables:
```env
ENVIRONMENT=production
LOG_LEVEL=WARNING
```

2. Use production ASGI server:
```bash
gunicorn backend.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

3. Use process manager (systemd, supervisor, PM2)
4. Setup reverse proxy (nginx, Caddy)
5. Enable HTTPS
6. Configure CORS for production domains

## License

MIT
