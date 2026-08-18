from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .api import api_router
from .database import engine
from .startup import initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="AI Agent Governance Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS: in production allow only the configured frontend origin,
# otherwise allow common localhost dev origins.
env = os.getenv("ENVIRONMENT", "development")
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
if env == "production":
    allow_origins = [frontend_url]
else:
    allow_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        frontend_url,
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


app.include_router(api_router)
app.include_router(api_router, prefix="/api", include_in_schema=False)


@app.get("/")
def root():

    return {
        "name": "AI Agent Governance Platform",
        "status": "running",
    }


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as error:
        raise HTTPException(status_code=503, detail="Neon database is unavailable") from error

    return {"status": "healthy", "database": "neon"}
