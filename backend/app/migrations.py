from sqlalchemy import text

from .database import engine


def upgrade_schema() -> None:
    """Apply backwards-compatible upgrades for databases created before v0.1.0."""
    if engine.dialect.name != "postgresql":
        return

    statements = (
        "ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS input_message VARCHAR(2000) NOT NULL DEFAULT ''",
        "ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ",
        "ALTER TABLE findings ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "ALTER TABLE approvals ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "ALTER TABLE audit_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
    )

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
