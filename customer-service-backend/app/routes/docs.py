"""
Documentation routes (only available in development)
"""
from fastapi import APIRouter, HTTPException
from ..config import settings

router = APIRouter(prefix="/docs", tags=["Documentation"])


@router.get("/api")
async def api_documentation():
    """
    API documentation endpoint
    Only available in development mode
    """
    if settings.environment == "production":
        raise HTTPException(status_code=403, detail="Documentation not available in production")

    return {
        "service": "Customer Service Agent Backend",
        "version": "1.0.0",
        "environment": settings.environment,
        "endpoints": {
            "connect": {
                "method": "POST",
                "path": "/api/connect",
                "description": "Connect to the customer service agent using service URL",
                "body": {"url": "optional string", "service_name": "optional string"},
            },
            "simulate": {
                "method": "POST",
                "path": "/api/simulate",
                "description": "Simulate a customer service scenario (defaults to random)",
                "body": {
                    "scenario_type": "random|auto_approval|blocked_approval",
                    "customer_id": "optional string (auto-generated if omitted)",
                    "request_description": "optional string (auto-generated if omitted)",
                },
            },
            "health": {
                "method": "GET",
                "path": "/api/connect/health",
                "description": "Health check endpoint",
            },
        },
        "primary_backend": settings.primary_backend_url,
        "frontend": settings.frontend_url,
    }


@router.get("/flows")
async def workflow_documentation():
    """
    Workflow documentation - explaining the approval flow
    Only available in development mode
    """
    if settings.environment == "production":
        raise HTTPException(status_code=403, detail="Documentation not available in production")

    return {
        "workflow": "Customer Service Request Governance Flow",
        "steps": [
            {
                "number": 1,
                "name": "Customer Request",
                "description": "Frontend sends request to customer service agent",
                "endpoint": "/api/simulate",
            },
            {
                "number": 2,
                "name": "Governance Check",
                "description": "Customer service agent forwards request to primary backend",
                "endpoint": "Primary Backend /api/approvals/request",
            },
            {
                "number": 3,
                "name": "Decision Making",
                "description": "Primary backend evaluates request against governance rules",
                "result": "approved|blocked|pending",
            },
            {
                "number": 4,
                "name": "Audit & Trace",
                "description": "All requests, decisions, and reasons are logged",
                "data": ["trace_id", "audit_events", "findings"],
            },
            {
                "number": 5,
                "name": "Response",
                "description": "Result with audit trail sent back to frontend",
                "response": "SimulateResponse with approval_status and audit_events",
            },
        ],
        "scenario_types": {
            "auto_approval": {
                "description": "Low-risk customer service requests that are automatically approved",
                "examples": ["refund_request ($50)", "order_replacement", "priority_support"],
            },
            "blocked_approval": {
                "description": "High-risk requests that are blocked with reasons",
                "examples": ["large_refund ($5000)", "account_suspension", "data_export"],
            },
            "random": {
                "description": "Randomly selected scenario for comprehensive testing",
            },
        },
    }
