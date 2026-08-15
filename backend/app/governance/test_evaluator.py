import uuid

from app.database import SessionLocal
from app.governance.evaluator import PolicyEvaluator
from app.models import Agent


db = SessionLocal()

try:
    agent = db.get(Agent, uuid.UUID("0380e7e6-4ac4-4a42-8e37-31797c042996"))
    if not agent:
        print("No agent found. Create an agent first.")
        raise SystemExit

    print("Testing agent:")
    print(agent.id)
    print(agent.name)

    evaluator = PolicyEvaluator(db)

    tests = [
        "faq_search",
        "send_email",
        "customer_database",
        "file_delete",
    ]

    for tool in tests:
        result = evaluator.check_tool(agent.id, tool)

        print("\nTool:", tool)
        print("Allowed:", result.allowed)
        print("Severity:", result.severity)
        print("Reason:", result.reason)

finally:
    db.close()

