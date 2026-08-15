from sqlalchemy import text

from .database import engine


def upgrade_schema() -> None:
    """Apply backwards-compatible upgrades for databases created before v0.1.0."""
    if engine.dialect.name != "postgresql":
        return

    statements = (
        "CREATE TABLE IF NOT EXISTS admin_users (id UUID PRIMARY KEY, email VARCHAR(320) UNIQUE NOT NULL, password_hash VARCHAR(256) NOT NULL, password_salt VARCHAR(128) NOT NULL, role VARCHAR(20) NOT NULL DEFAULT 'admin', created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)",
        "CREATE INDEX IF NOT EXISTS ix_admin_users_email ON admin_users (email)",
        "ALTER TABLE agents ADD COLUMN IF NOT EXISTS owner_id UUID REFERENCES admin_users(id)",
        "CREATE INDEX IF NOT EXISTS ix_agents_owner_id ON agents (owner_id)",
        "ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS input_message VARCHAR(2000) NOT NULL DEFAULT ''",
        "ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ",
        "ALTER TABLE findings ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "ALTER TABLE approvals ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "ALTER TABLE audit_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "ALTER TABLE execution_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
    )

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
