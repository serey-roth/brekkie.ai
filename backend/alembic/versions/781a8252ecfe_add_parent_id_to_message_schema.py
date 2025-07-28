"""Add parent_id to Message schema

Revision ID: 781a8252ecfe
Revises: 11d1b10382cf
Create Date: 2025-07-04 14:10:00.499935

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "781a8252ecfe"
down_revision: Union[str, None] = "11d1b10382cf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Use batch operations for SQLite compatibility
    with op.batch_alter_table("messages") as batch_op:
        # Add parent_id column to messages table
        batch_op.add_column(sa.Column("parent_id", sa.String(), nullable=True))

        # Add foreign key constraint
        batch_op.create_foreign_key("fk_messages_parent_id", "messages", ["parent_id"], ["id"])

        # Add index for performance
        batch_op.create_index("ix_messages_parent_id", ["parent_id"])

    # Populate parent_id based on message role and logical conversation flow
    # User messages have null parent_id
    # Assistant messages point to the most recent user message that was created before them
    connection = op.get_bind()

    # For each thread, find the parent for each assistant message
    # by looking for the most recent user message created before that assistant message
    result = connection.execute(
        sa.text("""
        SELECT DISTINCT thread_id 
        FROM messages 
        WHERE thread_id IS NOT NULL
    """)
    )

    thread_ids = [row.thread_id for row in result.fetchall()]

    for thread_id in thread_ids:
        # Get all messages in this thread ordered by created_at
        thread_messages = connection.execute(
            sa.text("""
            SELECT id, role, created_at
            FROM messages 
            WHERE thread_id = :thread_id 
            ORDER BY created_at
        """),
            {"thread_id": thread_id},
        ).fetchall()

        # Set all user messages to have null parent_id
        connection.execute(
            sa.text("""
            UPDATE messages 
            SET parent_id = NULL 
            WHERE thread_id = :thread_id AND role = 'user'
        """),
            {"thread_id": thread_id},
        )

        # For each assistant message, find the most recent user message created before it
        for msg in thread_messages:
            if msg.role == "assistant":
                # Find the most recent user message created before this assistant message
                parent_result = connection.execute(
                    sa.text("""
                    SELECT id 
                    FROM messages 
                    WHERE thread_id = :thread_id 
                        AND role = 'user' 
                        AND created_at < :assistant_created_at
                    ORDER BY created_at DESC 
                    LIMIT 1
                """),
                    {"thread_id": thread_id, "assistant_created_at": msg.created_at},
                ).fetchone()

                if parent_result:
                    # Set the parent_id to the found user message
                    connection.execute(
                        sa.text("""
                        UPDATE messages 
                        SET parent_id = :parent_id 
                        WHERE id = :msg_id
                    """),
                        {"parent_id": parent_result.id, "msg_id": msg.id},
                    )
                else:
                    # No user message found before this assistant message
                    connection.execute(
                        sa.text("""
                        UPDATE messages 
                        SET parent_id = NULL 
                        WHERE id = :msg_id
                    """),
                        {"msg_id": msg.id},
                    )


def downgrade() -> None:
    """Downgrade schema."""
    # Use batch operations for SQLite compatibility
    with op.batch_alter_table("messages") as batch_op:
        # Drop the foreign key constraint
        batch_op.drop_constraint("fk_messages_parent_id", type_="foreignkey")

        # Drop the index
        batch_op.drop_index("ix_messages_parent_id")

        # Drop the parent_id column
        batch_op.drop_column("parent_id")
