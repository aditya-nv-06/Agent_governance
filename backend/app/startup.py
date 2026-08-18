from .database import Base, engine
from .migrations import upgrade_schema
from .models import EnvAgent
from sqlalchemy.orm import Session
from .database import get_db
import os


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    upgrade_schema()
    # Optional auto-register local langraph demo agent for development
    if os.getenv("AUTO_REGISTER_LANGRAPH", "false").lower() in {"1", "true", "yes"}:
        try:
            with Session(bind=engine) as db:
                exists = db.query(EnvAgent).filter(EnvAgent.url == "http://localhost:9001/respond").first()
                if not exists:
                    a = EnvAgent(name="langraph-demo", url="http://localhost:9001/respond", purpose="langraph demo", allowed_instructions=["read_faq", "lookup_customer", "send_email"])
                    db.add(a)
                    db.commit()
        except Exception:
            pass
