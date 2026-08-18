from pydantic import BaseModel
from typing import Any, Optional, Dict, List
from datetime import datetime


class SimulationStep(BaseModel):
    """A single simulated request/response step in a series"""
    step: int
    scenario_type: str
    customer_id: str
    tool_executed: str
    tool_parameters: Optional[Dict[str, Any]] = None
    request_description: Optional[str] = None
    approval_status: str  # 'approved', 'blocked', 'pending'
    approval_reason: Optional[str] = None
    approval_id: Optional[str] = None
    trace_id: str
    run_id: Optional[str] = None
    audit_events: List[Dict[str, Any]] = []
    findings: List[Dict[str, Any]] = []
    execution_time_ms: float


class SimulateRequest(BaseModel):
    """Request to simulate customer service scenarios"""
    scenario_type: str = "random"  # 'auto_approval', 'blocked_approval', 'random'
    customer_id: Optional[str] = None
    request_description: Optional[str] = None
    tool_name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    series_count: int = 5


class ConnectRequest(BaseModel):
    """Request to connect to the customer service agent using URL"""
    url: Optional[str] = None
    service_name: Optional[str] = "Customer Service Agent"


class ApprovalRequest(BaseModel):
    """Request sent to primary backend for approval"""
    agent_id: str
    run_id: str
    tool_name: str
    parameters: Dict[str, Any]
    customer_id: str
    request_context: str


class ApprovalResponse(BaseModel):
    """Response from primary backend"""
    run_id: str
    status: str  # 'approved', 'blocked', 'pending'
    reason: Optional[str] = None
    audit_trail: List[Dict[str, Any]]
    trace_id: str


class SimulateResponse(BaseModel):
    """Response to multi-request series simulation"""
    success: bool
    scenario_type: str
    customer_id: str
    total_requests: int
    approved_count: int
    blocked_count: int
    series: List[SimulationStep]
    message: Optional[str] = None



class ConnectResponse(BaseModel):
    """Response to connect request"""
    status: str
    url: Optional[str] = None
    service_name: Optional[str] = None
    timestamp: Optional[str] = None
    message: str
