from app.database import SessionLocal, engine, Base
from app.models import Agent, BehaviorProfile


# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:

    # --------------------------------------------------
    # Agent
    # --------------------------------------------------

    agent = Agent(
        name="Customer Support Agent",
        description="Handles customer support requests",
        status="active",
    )

    db.add(agent)
    db.flush()


    # --------------------------------------------------
    # Behavior Profile
    # --------------------------------------------------

    profile = BehaviorProfile(
        agent_id=agent.id,

        name="Customer Support Policy",

        allowed_tools=[
            "faq_search",
            "send_email",
        ],

        allowed_data_sources=[
            "faq_database",
            "email_service",
        ],

        allowed_actions=[
            "search",
            "reply",
            "send_email",
            "read",
        ],

        max_llm_calls=1000,

        warning_threshold=80,

        critical_threshold=90,
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
