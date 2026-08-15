import os
import tempfile
import unittest
import uuid

_DB_FILE = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_DB_FILE.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_FILE.name}"
os.environ["USE_LLM_DECISIONS"] = "false"
os.environ["ALLOW_SQLITE_FOR_TESTS"] = "true"

from fastapi import HTTPException

from app.agent.service import AgentService
from app.database import Base, SessionLocal, engine
from app.models import Agent, AgentRun, Approval, BehaviorProfile, ExecutionEvent, Finding
from app.routes.approvals import decide_approval, execute_approved_action
from app.schemas import ApprovalDecisionRequest


class ApprovalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(engine)

    def setUp(self):
        self.db = SessionLocal()
        self.agent = Agent(name=f"Approval agent {uuid.uuid4()}", status="active")
        self.db.add(self.agent)
        self.db.flush()
        self.db.add(BehaviorProfile(
            agent_id=self.agent.id,
            name="Support policy",
            allowed_tools=["faq_search", "send_email"],
            allowed_data_sources=["faq_database", "email_service"],
            allowed_actions=["read", "send_email"],
        ))
        self.run = AgentRun(agent_id=self.agent.id, input_message="Get customer information", status="blocked")
        self.db.add(self.run)
        self.db.flush()
        self.finding = Finding(
            agent_id=self.agent.id,
            run_id=self.run.id,
            finding_type="UNAUTHORIZED_TOOL",
            severity="HIGH",
            expected="faq_search, send_email",
            actual="customer_database",
            reason="Unauthorized tool",
        )
        self.db.add(self.finding)
        self.db.flush()
        self.approval = Approval(finding_id=self.finding.id, requested_by="agent")
        self.db.add(self.approval)
        self.db.add(ExecutionEvent(
            run_id=self.run.id,
            agent_id=self.agent.id,
            event_type="LLM_TOOL_REQUEST",
            tool_name="customer_database",
            status="REQUESTED",
            details={"arguments": {"customer_id": "CUST-001"}},
        ))
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_pending_approval_cannot_execute(self):
        with self.assertRaises(HTTPException) as error:
            execute_approved_action(self.approval.id, self.db)
        self.assertEqual(error.exception.status_code, 403)

    def test_approved_action_executes_once(self):
        decide_approval(
            self.approval.id,
            ApprovalDecisionRequest(approved=True, decided_by="reviewer", reason="Verified request"),
            self.db,
        )
        result = execute_approved_action(self.approval.id, self.db)
        self.assertEqual(result["status"], "completed")
        self.db.refresh(self.approval)
        self.assertEqual(self.approval.status, "EXECUTED")
        event = self.db.query(ExecutionEvent).filter_by(
            run_id=self.run.id,
            event_type="APPROVED_TOOL_EXECUTION",
        ).one()
        self.assertEqual(event.tool_name, "customer_database")

        with self.assertRaises(HTTPException) as error:
            execute_approved_action(self.approval.id, self.db)
        self.assertEqual(error.exception.status_code, 409)

    def test_rejected_approval_cannot_execute(self):
        decide_approval(
            self.approval.id,
            ApprovalDecisionRequest(approved=False, decided_by="reviewer", reason="Too sensitive"),
            self.db,
        )
        with self.assertRaises(HTTPException) as error:
            execute_approved_action(self.approval.id, self.db)
        self.assertEqual(error.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
