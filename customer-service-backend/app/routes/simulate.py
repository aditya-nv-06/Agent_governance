"""
Simulation routes for testing customer service scenarios with governance
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

from ..schemas import SimulateRequest, SimulateResponse
from ..governance_client import GovernanceClient
from ..simulator import CustomerServiceSimulator

router = APIRouter(prefix="/simulate", tags=["Simulation"])

# Global governance client
_governance_client = None
_simulator = None


def get_governance_client() -> GovernanceClient:
    """Get or create governance client"""
    global _governance_client
    if _governance_client is None:
        _governance_client = GovernanceClient()
    return _governance_client


def get_simulator() -> CustomerServiceSimulator:
    """Get or create simulator"""
    global _simulator
    if _simulator is None:
        _simulator = CustomerServiceSimulator(get_governance_client())
    return _simulator


@router.get("")
@router.post("")
async def simulate(
    request: SimulateRequest = None,
    scenario_type: str = "random",
    customer_id: str = None,
    series_count: int = 5,
    simulator: CustomerServiceSimulator = Depends(get_simulator),
) -> SimulateResponse:
    """
    Simulate a series of customer service requests with governance approval.
    
    Scenarios:
    - random (default): Random selection between low-risk and high-risk operations
    - auto_approval: Low-risk requests that auto-approve
    - blocked_approval: High-risk requests that get blocked
    """
    try:
        effective_scenario = request.scenario_type if request and request.scenario_type else scenario_type or "random"
        effective_customer = request.customer_id if request and request.customer_id else customer_id
        effective_description = request.request_description if request else None
        effective_count = request.series_count if request and request.series_count else series_count or 5

        result = await simulator.simulate_series(
            scenario_type=effective_scenario,
            customer_id=effective_customer,
            request_description=effective_description,
            series_count=effective_count,
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Simulation failed"))

        return SimulateResponse(
            success=True,
            scenario_type=result["scenario_type"],
            customer_id=result["customer_id"],
            total_requests=result["total_requests"],
            approved_count=result["approved_count"],
            blocked_count=result["blocked_count"],
            series=result["series"],
            message=result["message"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/random")
async def test_random_scenario(
    customer_id: str = None,
    series_count: int = 5,
    simulator: CustomerServiceSimulator = Depends(get_simulator),
) -> SimulateResponse:
    """Quick test for random scenario series"""
    result = await simulator.simulate_series(
        scenario_type="random",
        customer_id=customer_id,
        series_count=series_count,
    )

    return SimulateResponse(
        success=True,
        scenario_type=result["scenario_type"],
        customer_id=result["customer_id"],
        total_requests=result["total_requests"],
        approved_count=result["approved_count"],
        blocked_count=result["blocked_count"],
        series=result["series"],
        message=result["message"],
    )


@router.get("/auto-approval")
async def test_auto_approval(
    customer_id: str = None,
    series_count: int = 3,
    simulator: CustomerServiceSimulator = Depends(get_simulator),
) -> SimulateResponse:
    """Quick test for auto-approval scenario series"""
    result = await simulator.simulate_series(
        scenario_type="auto_approval",
        customer_id=customer_id,
        series_count=series_count,
    )

    return SimulateResponse(
        success=True,
        scenario_type=result["scenario_type"],
        customer_id=result["customer_id"],
        total_requests=result["total_requests"],
        approved_count=result["approved_count"],
        blocked_count=result["blocked_count"],
        series=result["series"],
        message=result["message"],
    )


@router.get("/blocked-approval")
async def test_blocked_approval(
    customer_id: str = None,
    series_count: int = 3,
    simulator: CustomerServiceSimulator = Depends(get_simulator),
) -> SimulateResponse:
    """Quick test for blocked-approval scenario series"""
    result = await simulator.simulate_series(
        scenario_type="blocked_approval",
        customer_id=customer_id,
        series_count=series_count,
    )

    return SimulateResponse(
        success=True,
        scenario_type=result["scenario_type"],
        customer_id=result["customer_id"],
        total_requests=result["total_requests"],
        approved_count=result["approved_count"],
        blocked_count=result["blocked_count"],
        series=result["series"],
        message=result["message"],
    )


