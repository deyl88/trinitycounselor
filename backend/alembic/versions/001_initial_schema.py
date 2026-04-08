"""001 — Initial Trinity schema

Creates:
  - pgvector extension
  - conversation_memory       (private per-user per-agent encrypted memory)
  - therapeutic_summaries     (running session arc compression)
  - sap_signals_staging       (pre-RKG abstracted signal queue)
  - users                     (stub — for auth integration)
  - relationships             (maps two users to a relationship_id)

Revision ID: 001_initial
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── pgvector extension ────────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # ── users (stub — full implementation in future auth migration) ───────────
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.Text(), nullable=False, unique=True),
        sa.Column("hashed_password", sa.Text(), nullable=False),
        sa.Column("partner_tag", sa.Text(), nullable=False),  # "partner_a" | "partner_b"
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    # ── relationships ─────────────────────────────────────────────────────────
    op.create_table(
        "relationships",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("partner_a_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("partner_b_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    # ── conversation_memory ───────────────────────────────────────────────────
    # The embedding column uses pgvector's vector type.
    # We use raw SQL for this because SQLAlchemy doesn't natively know the
    # pgvector type — pgvector-python adds it, but Alembic needs the raw DDL.
    op.execute("""
        CREATE TABLE conversation_memory (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            namespace       TEXT NOT NULL,
            content         TEXT NOT NULL,
            content_enc     BYTEA,
            embedding       vector(1536) NOT NULL,
            metadata        JSONB NOT NULL DEFAULT '{}',
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # HNSW index for fast approximate nearest-neighbour search within namespace
    op.execute("""
        CREATE INDEX ix_conv_memory_hnsw
        ON conversation_memory
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    # Composite filter index — every query filters by (user_id, namespace) first
    op.execute("""
        CREATE INDEX ix_conv_memory_user_ns
        ON conversation_memory (user_id, namespace)
    """)

    # ── therapeutic_summaries ─────────────────────────────────────────────────
    op.create_table(
        "therapeutic_summaries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("namespace", sa.Text(), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("summary_enc", sa.LargeBinary(), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.UniqueConstraint("user_id", "namespace", name="uq_summaries_user_ns"),
    )

    # ── sap_signals_staging ───────────────────────────────────────────────────
    op.create_table(
        "sap_signals_staging",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("relationship_id", UUID(as_uuid=True), sa.ForeignKey("relationships.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_agent", sa.Text(), nullable=False),  # "agent_a" | "agent_b"
        sa.Column("signals", JSONB(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index(
        "ix_sap_staging_unprocessed",
        "sap_signals_staging",
        ["relationship_id", "processed"],
        postgresql_where=sa.text("processed = false"),
    )


def downgrade() -> None:
    op.drop_table("sap_signals_staging")
    op.drop_table("therapeutic_summaries")
    op.execute("DROP TABLE IF EXISTS conversation_memory CASCADE")
    op.drop_table("relationships")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS vector")
