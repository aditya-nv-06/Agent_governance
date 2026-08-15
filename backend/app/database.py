import os

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import  load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be set to the Neon PostgreSQL connection URL")

# Neon URLs frequently use the generic PostgreSQL scheme. This application
# installs psycopg v3, so select its SQLAlchemy dialect explicitly.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

is_test_sqlite = (
    DATABASE_URL.startswith("sqlite")
    and os.getenv("ALLOW_SQLITE_FOR_TESTS", "false").lower() == "true"
)

if not is_test_sqlite:
    url = make_url(DATABASE_URL)
    if url.drivername != "postgresql+psycopg" or not (url.host or "").endswith("neon.tech"):
        raise RuntimeError("DATABASE_URL must use the Neon PostgreSQL psycopg connection URL")

engine_options = {"pool_pre_ping": True}
if is_test_sqlite:
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(
        DATABASE_URL,
        **engine_options,
)

SessionLocal = sessionmaker(
    bind = engine,
    autoflush=False,
    autocommit=False
)

class Base(DeclarativeBase):
    pass

def get_db():
    db=SessionLocal()

    try:
        yield db
    finally:
        db.close()
