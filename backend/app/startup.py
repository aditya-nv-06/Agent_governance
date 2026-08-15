from .database import Base, engine
from .migrations import upgrade_schema


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    upgrade_schema()
