"""
FastAPI application entry point for Voice Agent API.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.config import setup_logging, get_settings
from backend.routes import auth, agents, calls


# Setup logging before any other imports
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    settings = get_settings()
    logger.info("=" * 60)
    logger.info("🚀 Voice Agent API Starting")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Port: {settings.port}")
    logger.info(f"Log Level: {settings.log_level}")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("👋 Voice Agent API Shutting Down")


# Create FastAPI application
app = FastAPI(
    title="Voice Agent API",
    version="1.0.0",
    description="AI-powered voice calling system for logistics operations",
    lifespan=lifespan,
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle HTTP exceptions with consistent error response format.
    """
    logger.warning(
        f"HTTP {exc.status_code} at {request.method} {request.url.path}: {exc.detail}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle request validation errors with detailed error messages.
    """
    logger.warning(f"Validation error at {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions with safe error response.
    """
    logger.error(
        f"Unhandled exception at {request.method} {request.url.path}: {exc}",
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error occurred. Please try again later."
        },
    )


# Include routers (prefixes are already defined in the router files)
app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(calls.router)


@app.get("/", tags=["Health"])
async def root():
    """
    Root endpoint providing API information.
    """
    return {
        "name": "Voice Agent API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    return {
        "status": "healthy",
        "service": "voice-agent-api",
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
