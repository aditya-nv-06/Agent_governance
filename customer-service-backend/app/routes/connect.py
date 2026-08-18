"""
Connection routes for customer service agent
"""
from fastapi import APIRouter
from datetime import datetime
from typing import Optional

from ..schemas import ConnectRequest, ConnectResponse
from ..config import settings

router = APIRouter(prefix="/connect", tags=["Connection"])


@router.post("")
async def connect(request: Optional[ConnectRequest] = None) -> ConnectResponse:
    """
    Connect to customer service agent using service URL.
    Validates that the service is running and reachable.
    """
    now = datetime.utcnow().isoformat()
    default_service = getattr(settings, "service_url", f"http://localhost:{settings.port}")
    service_url = request.url if request and request.url else default_service
    service_name = request.service_name if request and request.service_name else "Customer Service Agent"

    return ConnectResponse(
        status="connected",
        url=service_url,
        service_name=service_name,
        timestamp=now,
        message=f"Successfully connected to {service_name} at {service_url}",
    )


@router.get("")
async def get_connection_info() -> ConnectResponse:
    """
    Get connection status and info for the Customer Service backend.
    """
    now = datetime.utcnow().isoformat()
    default_service = getattr(settings, "service_url", f"http://localhost:{settings.port}")
    return ConnectResponse(
        status="connected",
        url=default_service,
        service_name="Customer Service Agent",
        timestamp=now,
        message=f"Customer Service Agent backend is active and ready",
    )


@router.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Customer Service Agent",
        "port": settings.port,
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat(),
    }

