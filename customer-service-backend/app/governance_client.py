"""
Client to communicate with primary backend governance system
"""
import httpx
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from .config import settings

logger = logging.getLogger(__name__)


class GovernanceClient:
    """Client for communicating with the primary backend"""

    def __init__(self):
        self.base_url = settings.primary_backend_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def submit_approval_request(
        self,
        agent_id: str,
        customer_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
        request_context: str,
        trace_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Submit a request to the primary backend for approval
        """
        effective_trace = trace_id or str(uuid.uuid4())
        try:
            payload = {
                "agent_id": agent_id,
                "customer_id": customer_id,
                "tool_name": tool_name,
                "parameters": parameters,
                "request_context": request_context,
                "trace_id": effective_trace,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Submit to primary backend external integration endpoint
            response = await self.client.post(
                f"{self.base_url}/api/external/approvals/request",
                json=payload,
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    **data,
                    "trace_id": data.get("trace_id") or effective_trace,
                }
            else:
                logger.error(f"Approval request failed: {response.text}")
                return {
                    "status": "error",
                    "trace_id": effective_trace,
                    "reason": response.text,
                }

        except httpx.RequestError as e:
            logger.error(f"Error submitting approval request: {str(e)}")
            return {
                "status": "error",
                "trace_id": trace_id,
                "reason": str(e),
            }

    async def get_audit_trail(self, trace_id: str) -> Optional[list]:
        """
        Retrieve audit trail for a specific request
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/external/audit?trace_id={trace_id}",
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get audit trail: {response.text}")
                return []

        except httpx.RequestError as e:
            logger.error(f"Error fetching audit trail: {str(e)}")
            return []

    async def get_findings(self, trace_id: str) -> Optional[list]:
        """
        Retrieve findings/reasons for blocked or pending approvals
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/external/findings?trace_id={trace_id}",
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get findings: {response.text}")
                return []

        except httpx.RequestError as e:
            logger.error(f"Error fetching findings: {str(e)}")
            return []

    async def check_approval_status(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Check the status of an approval request
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/external/approvals/{run_id}",
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to check approval status: {response.text}")
                return None

        except httpx.RequestError as e:
            logger.error(f"Error checking approval status: {str(e)}")
            return None

