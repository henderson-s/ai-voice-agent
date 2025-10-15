from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from backend.routes import auth, agents, calls

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Voice Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(calls.router)


@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Voice Agent API starting up...")
    logger.info("✅ CORS enabled for: http://localhost:5173, http://localhost:3000")


@app.get("/health")
async def health_check():
    return {"status": "ok"}

