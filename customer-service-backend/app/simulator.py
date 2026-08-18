"""
Customer service simulation engine for testing approval workflows
"""
import asyncio
import random
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from .governance_client import GovernanceClient

# Low-risk scenario templates
LOW_RISK_TEMPLATES = [
    {
        "name": "refund_request",
        "make_params": lambda: {
            "amount": round(random.uniform(12.50, 79.99), 2),
            "reason": random.choice(["defective_product", "wrong_size", "late_delivery", "item_not_as_described"]),
            "order_id": f"ORD-{random.randint(10000, 99999)}",
        },
        "describe": lambda p: f"Low-risk refund request of ${p['amount']} for order {p['order_id']} due to {p['reason']}",
    },
    {
        "name": "order_replacement",
        "make_params": lambda: {
            "order_id": f"ORD-{random.randint(10000, 99999)}",
            "item": random.choice(["shirt_blue_m", "wireless_headphones_pro", "running_shoes_10", "desk_lamp_led", "usb_c_hub"]),
        },
        "describe": lambda p: f"Replacement shipment request for {p['item']} on order {p['order_id']}",
    },
    {
        "name": "priority_support",
        "make_params": lambda: {
            "customer_tier": random.choice(["silver", "gold", "platinum", "vip"]),
            "issue": random.choice(["urgent_shipping_inquiry", "loyalty_points_sync", "checkout_assistance"]),
        },
        "describe": lambda p: f"Priority tier {p['customer_tier']} support request: {p['issue']}",
    },
    {
        "name": "address_change",
        "make_params": lambda: {
            "order_id": f"ORD-{random.randint(10000, 99999)}",
            "postal_code": f"{random.randint(10001, 99950)}",
            "city": random.choice(["San Francisco", "Austin", "New York", "Seattle", "Chicago"]),
        },
        "describe": lambda p: f"Address change for in-transit order {p['order_id']} to {p['city']}, {p['postal_code']}",
    },
    {
        "name": "discount_inquiry",
        "make_params": lambda: {
            "promo_code": random.choice(["SAVE15", "WELCOME10", "LOYALTY25", "SPRING2026"]),
            "cart_value": round(random.uniform(30.00, 150.00), 2),
        },
        "describe": lambda p: f"Customer applying promotional discount code {p['promo_code']} on cart ${p['cart_value']}",
    },
]

# High-risk scenario templates (blocked by policy)
HIGH_RISK_TEMPLATES = [
    {
        "name": "large_refund",
        "make_params": lambda: {
            "amount": round(random.uniform(1500.00, 7500.00), 2),
            "reason": random.choice(["bulk_order_cancellation", "disputed_transaction", "wholesale_return", "unknown"]),
            "order_id": f"ORD-{random.randint(10000, 99999)}",
        },
        "describe": lambda p: f"High-value refund request of ${p['amount']} on order {p['order_id']} ({p['reason']})",
    },
    {
        "name": "account_suspension",
        "make_params": lambda: {
            "days": random.choice([30, 60, 90, 365]),
            "reason": random.choice(["suspicious_activity", "repeated_chargebacks", "credential_stuffing_alert"]),
        },
        "describe": lambda p: f"Account suspension action requested for {p['days']} days due to {p['reason']}",
    },
    {
        "name": "data_export",
        "make_params": lambda: {
            "format": "json",
            "include_all": True,
            "include_pii": True,
            "destination": "external_download_link",
        },
        "describe": lambda p: f"Full PII customer data export requested in JSON format to external destination",
    },
    {
        "name": "admin_role_grant",
        "make_params": lambda: {
            "target_role": "superadmin",
            "reason": "support_escalation_bypass",
        },
        "describe": lambda p: f"Elevated role permission grant to superadmin for support bypass",
    },
    {
        "name": "security_override",
        "make_params": lambda: {
            "bypass_mfa": True,
            "action": "force_password_reset",
        },
        "describe": lambda p: f"Security override requested: bypass MFA for forced password reset",
    },
]


def generate_random_customer_id() -> str:
    return f"CUST-{random.randint(100, 999)}"


class CustomerServiceSimulator:
    """Simulate customer service scenarios with governance"""

    def __init__(self, governance_client: GovernanceClient):
        self.governance_client = governance_client

    async def simulate_single_step(
        self,
        step_number: int,
        scenario_type: str,
        customer_id: str,
        request_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a single step in the customer service simulation"""
        effective_type = scenario_type.lower() if scenario_type else "random"

        if effective_type == "auto_approval":
            template = random.choice(LOW_RISK_TEMPLATES)
            actual_scenario = "auto_approval"
        elif effective_type == "blocked_approval":
            template = random.choice(HIGH_RISK_TEMPLATES)
            actual_scenario = "blocked_approval"
        else:
            if random.random() < 0.6:
                template = random.choice(LOW_RISK_TEMPLATES)
                actual_scenario = "auto_approval"
            else:
                template = random.choice(HIGH_RISK_TEMPLATES)
                actual_scenario = "blocked_approval"

        tool_params = template["make_params"]()
        tool_name = template["name"]
        step_desc = request_description.strip() if (request_description and request_description.strip() and step_number == 1) else template["describe"](tool_params)

        trace_id = str(uuid.uuid4())
        start_time = datetime.utcnow()

        # Submit to primary backend governance
        approval_response = await self.governance_client.submit_approval_request(
            agent_id="customer-service-agent-1",
            customer_id=customer_id,
            tool_name=tool_name,
            parameters=tool_params,
            request_context=step_desc,
            trace_id=trace_id,
        )

        # Audit trail and findings are returned directly from governance
        audit_events = (approval_response.get("audit_events") if approval_response else None)
        if audit_events is None:
            audit_events = await self.governance_client.get_audit_trail(trace_id)

        findings = (approval_response.get("findings") if approval_response else None)
        if findings is None and approval_response and approval_response.get("status") == "blocked":
            findings = await self.governance_client.get_findings(trace_id)

        end_time = datetime.utcnow()
        execution_time_ms = (end_time - start_time).total_seconds() * 1000

        return {
            "step": step_number,
            "scenario_type": actual_scenario,
            "customer_id": customer_id,
            "tool_executed": tool_name,
            "tool_parameters": tool_params,
            "request_description": step_desc,
            "approval_status": approval_response.get("status") if approval_response else "error",
            "approval_reason": approval_response.get("reason") if approval_response else None,
            "approval_id": approval_response.get("approval_id") if approval_response else None,
            "run_id": approval_response.get("run_id") if approval_response else None,
            "trace_id": trace_id,
            "audit_events": audit_events or [],
            "findings": findings or [],
            "execution_time_ms": execution_time_ms,
        }

    async def simulate_series(
        self,
        scenario_type: Optional[str] = "random",
        customer_id: Optional[str] = None,
        request_description: Optional[str] = None,
        series_count: int = 5,
    ) -> Dict[str, Any]:
        """
        Execute a series of simulated customer requests in a single customer session.
        Every request is governed, audited, and any blocked actions produce findings/approvals.
        """
        effective_customer_id = customer_id.strip() if (customer_id and customer_id.strip()) else generate_random_customer_id()
        effective_type = (scenario_type or "random").lower()
        count = max(1, min(series_count or 5, 20))

        step_tasks = [
            self.simulate_single_step(
                step_number=i + 1,
                scenario_type=effective_type,
                customer_id=effective_customer_id,
                request_description=request_description if i == 0 else None,
            )
            for i in range(count)
        ]
        series_steps = await asyncio.gather(*step_tasks)

        approved_count = sum(1 for s in series_steps if s["approval_status"] == "approved")
        blocked_count = sum(1 for s in series_steps if s["approval_status"] == "blocked")

        return {
            "success": True,
            "scenario_type": effective_type,
            "customer_id": effective_customer_id,
            "total_requests": count,
            "approved_count": approved_count,
            "blocked_count": blocked_count,
            "series": list(series_steps),
            "message": f"Simulated series of {count} customer requests for {effective_customer_id}: {approved_count} approved, {blocked_count} blocked",
        }


