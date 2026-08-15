"""Focused, dependency-free checks for the governance boundary."""

import os
import tempfile
import unittest
import uuid


_DB_FILE = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_DB_FILE.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_FILE.name}"
os.environ["USE_LLM_DECISIONS"] = "false"
os.environ["ALLOW_SQLITE_FOR_TESTS"] = "true"

from app.agent.service import AgentService
from app.database import Base, SessionLocal, engine
from app.governance.evaluator import PolicyEvaluator
from app.models import Agent, AgentRun, BehaviorProfile, ExecutionEvent, Finding, ResponseAction


class GovernanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(engine)

    def setUp(self):
        self.db = SessionLocal()
        agent = Agent(name=f"Agent {uuid.uuid4()}", status="active")
        self.db.add(agent)
        self.db.flush()
        self.agent = agent
        self.profile = BehaviorProfile(
            agent_id=agent.id,
            name="Support policy",
            allowed_tools=["faq_search", "send_email"],
            allowed_data_sources=["faq_database", "email_service"],
            allowed_actions=["read", "send_email"],
            max_llm_calls=1000,
            warning_threshold=80,
            critical_threshold=90,
        )
        self.db.add(self.profile)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_allowed_tool_passes_all_policy_checks(self):
        decision = PolicyEvaluator(self.db).check_tool(self.agent.id, "faq_search")
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.severity, "NONE")

    def test_unauthorized_tool_is_blocked(self):
        decision = PolicyEvaluator(self.db).check_tool(self.agent.id, "customer_database")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.severity, "HIGH")

    def test_unknown_tool_is_critical_block(self):
        decision = PolicyEvaluator(self.db).check_tool(self.agent.id, "delete_production_database")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.severity, "CRITICAL")
        self.assertEqual(decision.finding_type, "UNKNOWN_TOOL")

    def test_blocked_run_persists_finding_and_never_executes_tool(self):
        run = AgentRun(agent_id=self.agent.id, input_message="Get customer information")
        self.db.add(run)
        self.db.commit()

        result = AgentService(self.db).run(self.agent.id, run.id, run.input_message)
        self.assertEqual(result["status"], "blocked")
        finding = self.db.get(Finding, uuid.UUID(result["finding_id"]))
        self.assertIsNotNone(finding)
        self.assertIsNotNone(self.db.query(ResponseAction).filter_by(finding_id=finding.id).first())
        executed = self.db.query(ExecutionEvent).filter_by(run_id=run.id, event_type="TOOL_EXECUTED").first()
        self.assertIsNone(executed)

    def test_blocked_request_does_not_disable_future_valid_requests(self):
        blocked_run = AgentRun(agent_id=self.agent.id, input_message="Get customer information")
        self.db.add(blocked_run)
        self.db.commit()
        AgentService(self.db).run(self.agent.id, blocked_run.id, blocked_run.input_message)

        self.db.refresh(self.agent)
        self.assertEqual(self.agent.status, "active")

        allowed_run = AgentRun(agent_id=self.agent.id, input_message="What is the refund policy?")
        self.db.add(allowed_run)
        self.db.commit()
        result = AgentService(self.db).run(self.agent.id, allowed_run.id, allowed_run.input_message)
        self.assertEqual(result["status"], "completed")

    def test_warning_and_critical_thresholds(self):
        self.profile.max_llm_calls = 10
        self.db.commit()
        for _ in range(8):
            self.db.add(AgentRun(agent_id=self.agent.id, input_message="prior"))
        self.db.commit()
        warning = PolicyEvaluator(self.db).check_tool(self.agent.id, "faq_search")
        self.assertEqual(warning.warning, "WARNING")

        for _ in range(1):
            self.db.add(AgentRun(agent_id=self.agent.id, input_message="prior"))
        self.db.commit()
        critical = PolicyEvaluator(self.db).check_tool(self.agent.id, "faq_search")
        self.assertEqual(critical.warning, "CRITICAL")

        self.db.add(AgentRun(agent_id=self.agent.id, input_message="prior"))
        self.db.commit()
        limited = PolicyEvaluator(self.db).check_tool(self.agent.id, "faq_search")
        self.assertFalse(limited.allowed)

    def test_requires_approval_decision_has_status_metadata(self):
        decision = PolicyEvaluator(self.db).check_tool(self.agent.id, "send_email", requires_approval=True)
        self.assertTrue(decision.allowed)
        self.assertTrue(decision.requires_approval)
        self.assertEqual(decision.status, "REQUIRE_APPROVAL")


if __name__ == "__main__":
    unittest.main()
