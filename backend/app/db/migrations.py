from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


async def migrate_legacy_schema(connection: AsyncConnection) -> None:
    """Add RBAC/versioning columns to databases created by the pre-auth MVP.

    New installations receive the full schema through metadata.create_all. These
    idempotent statements keep an existing hackathon database usable without a
    destructive reset. A production deployment can later move the same changes
    into Alembic revisions.
    """
    if connection.dialect.name != "postgresql":
        return
    statements = (
        "ALTER TABLE startups ADD COLUMN IF NOT EXISTS owner_id UUID NULL",
        "ALTER TABLE startups ADD COLUMN IF NOT EXISTS status VARCHAR(30) NOT NULL DEFAULT 'draft'",
        "ALTER TABLE startups ADD COLUMN IF NOT EXISTS current_version INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE startups ADD COLUMN IF NOT EXISTS discoverable BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE startups ADD COLUMN IF NOT EXISTS public_summary JSONB NOT NULL DEFAULT '{}'::jsonb",
        "ALTER TABLE startup_access ALTER COLUMN granted_by_id DROP NOT NULL",
        "ALTER TABLE startup_access ALTER COLUMN granted_at DROP NOT NULL",
        "ALTER TABLE startup_access ADD COLUMN IF NOT EXISTS request_reason VARCHAR(1000) NULL",
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS visibility VARCHAR(30) NOT NULL DEFAULT 'shared'",
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS uploaded_by_id UUID NULL",
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS category VARCHAR(40) NOT NULL DEFAULT 'unclassified'",
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS categorized_by VARCHAR(20) NOT NULL DEFAULT 'pending'",
        "ALTER TABLE analyses ADD COLUMN IF NOT EXISTS startup_version_id UUID NULL",
        "ALTER TABLE analyses ADD COLUMN IF NOT EXISTS created_by_id UUID NULL",
        "ALTER TABLE analyses ADD COLUMN IF NOT EXISTS rubric_version VARCHAR(30) NOT NULL DEFAULT 'default-v1'",
        "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS user_id UUID NULL",
        "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS startup_version_id UUID NULL",
        "CREATE INDEX IF NOT EXISTS ix_startups_owner_id ON startups (owner_id)",
        "CREATE INDEX IF NOT EXISTS ix_documents_uploaded_by_id ON documents (uploaded_by_id)",
        "CREATE INDEX IF NOT EXISTS ix_analyses_created_by_id ON analyses (created_by_id)",
        "CREATE INDEX IF NOT EXISTS ix_analyses_startup_version_id ON analyses (startup_version_id)",
        "CREATE INDEX IF NOT EXISTS ix_chat_messages_user_id ON chat_messages (user_id)",
    )
    for statement in statements:
        await connection.execute(text(statement))
