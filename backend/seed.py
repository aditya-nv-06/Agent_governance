from app.database import SessionLocal, engine, Base
from app.models import (
    Agent,
    AgentRun,
    Approval,
    AuditEvent,
    BehaviorProfile,
    ExecutionEvent,
    Finding,
    ResponseAction,
    AdminUser,
)
from app.auth import create_password_fields


# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Seed only for this admin email
TARGET_ADMIN_EMAIL = "adityanv4@gmail.com"

try:

    # This seed script is intentionally a demo reset.  Delete child records
    # first so every invocation starts the dashboard with only the profile
    # below, rather than preserving old approvals/findings from prior demos.
    for model in (
        AuditEvent,
        Approval,
        ResponseAction,
        ExecutionEvent,
        Finding,
        AgentRun,
        BehaviorProfile,
        Agent,
    ):
        db.query(model).delete(synchronize_session=False)
    db.commit()

    # Ensure the target admin exists (create with a seed password if needed)
    admin = db.query(AdminUser).filter(AdminUser.email == TARGET_ADMIN_EMAIL).first()
    if not admin:
        salt, password_hash = create_password_fields("change-me-please")
        admin = AdminUser(email=TARGET_ADMIN_EMAIL, password_hash=password_hash, password_salt=salt)
        db.add(admin)
        db.flush()

    # --------------------------------------------------
    # Agent (owned by the target admin)
    # --------------------------------------------------

    agent = Agent(
        name="Customer Support Agent",
        description="Handles customer support requests",
        status="active",
        owner_id=admin.id,
    )
    db.add(agent)
    db.flush()


    # --------------------------------------------------
    # Behavior Profile
    # --------------------------------------------------

    profile_data = {
        "allowed_tools": ["faq_search", "send_email"],
        "allowed_data_sources": ["faq_database", "email_service"],
        "allowed_actions": ["read", "send_email"],
        "max_llm_calls": 1000,
        "warning_threshold": 80,
        "critical_threshold": 90,
    }
    profile = BehaviorProfile(
        agent_id=agent.id,
        name="Customer Support Policy",
        **profile_data,
    )
    db.add(profile)

    db.commit()

    print("\n====================================")
    print("Database seeded successfully!")
    print("====================================")

    print(f"\nAgent ID:")
    print(agent.id)

    print(f"\nAgent Name:")
    print(agent.name)

    print("\nAllowed Tools:")
    for tool in profile.allowed_tools:
        print(f"  - {tool}")

    print("\nBlocked Tools:")
    print("  - customer_database")

    print()


except Exception as error:

    db.rollback()

    print("Seeding failed:")
    print(error)

    raise

finally:

    db.close()
