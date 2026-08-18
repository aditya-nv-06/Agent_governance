"""
Customer Service Agent Backend - Second Backend for Governance Testing
This backend connects to the primary AI Agent Governance Platform
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from .config import settings
from .governance_client import GovernanceClient
from .routes import connect, simulate, docs

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global governance client
governance_client: GovernanceClient = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    global governance_client
    
    # Startup
    governance_client = GovernanceClient()
    logger.info(f"Customer Service Agent Backend started")
    logger.info(f"Primary backend: {settings.primary_backend_url}")
    logger.info(f"Environment: {settings.environment}")
    
    yield
    
    # Shutdown
    if governance_client:
        await governance_client.close()
        logger.info("Governance client closed")


# Create FastAPI app
app = FastAPI(
    title="Customer Service Agent Backend",
    description="Second backend for customer service scenarios with governance approval",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS origins: allow only the frontend in production, allow localhost in development
if settings.environment == "production":
    allow_origins = [settings.frontend_url]
else:
    allow_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        settings.frontend_url,
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Root endpoint
@app.get("/")
def root():
    return {
        "service": "Customer Service Agent Backend",
        "status": "running",
        "version": "1.0.0",
        "environment": settings.environment,
        "primary_backend": settings.primary_backend_url,
    }


# Health endpoint
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "Customer Service Agent",
        "environment": settings.environment,
    }


# Include routers
app.include_router(connect.router, prefix="/api")
app.include_router(simulate.router, prefix="/api")
app.include_router(docs.router, prefix="/api", include_in_schema=False)

# Docs endpoint (only in development)
if settings.environment != "production":
    @app.get("/api/docs")
    def get_docs():
        return {
            "message": "Visit /api/docs/api or /api/docs/flows for full documentation",
            "mode": "development",
        }
else:
    # Disable docs endpoints in production
    app.openapi = lambda: None
    app.docs_url = None
    app.redoc_url = None
    app.openapi_url = None


# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.environment != "production",
    )
