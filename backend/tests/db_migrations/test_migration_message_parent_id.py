"""Test that the parent_id is correctly assigned to existing assistant messages based on relatively most recent user message."""

import uuid
from datetime import datetime, timedelta, timezone
import pytest
from alembic import command
from sqlalchemy import text
from sqlalchemy.orm import Session

PREV_REVISION = "11d1b10382cf"
TARGET_REVISION = "781a8252ecfe"

def make_msg(id, role, created_at, user_id, thread_id, content_type="text", text_content=None):
    return {
        "id": id,
        "role": role,
        "created_at": created_at,
        "user_id": user_id,
        "thread_id": thread_id,
        "content_type": content_type,
        "text_content": text_content,
    }


SCENARIOS = [
    (
        "normal conversation flow",
        lambda now, user_id, thread_id: [
            make_msg("user1", "user", now, user_id, thread_id, text_content="hi"),
            make_msg("assistant1", "assistant", now + timedelta(seconds=1), user_id, thread_id, text_content="hello!"),
            make_msg("user2", "user", now + timedelta(seconds=2), user_id, thread_id, text_content="hi again"),
            make_msg("assistant2", "assistant", now + timedelta(seconds=3), user_id, thread_id, text_content="more help"),
        ],
        {"assistant1": "user1", "assistant2": "user2"}
    ),
    (
        "consecutive user messages",
        lambda now, user_id, thread_id: [
            make_msg("user1", "user", now, user_id, thread_id),
            make_msg("user2", "user", now + timedelta(seconds=1), user_id, thread_id),
            make_msg("assistant1", "assistant", now + timedelta(seconds=2), user_id, thread_id),
        ],
        {"assistant1": "user2"}
    ),
    (
        "messages with non-chronological timestamps",
        lambda now, user_id, thread_id: [
            make_msg("user1", "user", now, user_id, thread_id),
            make_msg("user2", "user", now + timedelta(seconds=2), user_id, thread_id),
            make_msg("assistant1", "assistant", now + timedelta(seconds=1), user_id, thread_id),
            make_msg("assistant2", "assistant", now + timedelta(seconds=3), user_id, thread_id),
        ],
        {"assistant1": "user1", "assistant2": "user2"}
    ),
    (
        "only user messages",
        lambda now, user_id, thread_id: [
            make_msg("user1", "user", now, user_id, thread_id),
            make_msg("user2", "user", now + timedelta(seconds=1), user_id, thread_id),
        ],
        {}
    ),
    (
        "only assistant messages",
        lambda now, user_id, thread_id: [
            make_msg("assistant1", "assistant", now, user_id, thread_id),
            make_msg("assistant2", "assistant", now + timedelta(seconds=1), user_id, thread_id),
        ],
        {"assistant1": None, "assistant2": None}
    ),
    (
        "assistant messages with identical timestamps as user messages",
        lambda now, user_id, thread_id: [
            make_msg("user1", "user", now, user_id, thread_id),
            make_msg("assistant1", "assistant", now, user_id, thread_id),
            make_msg("user2", "user", now, user_id, thread_id),
            make_msg("assistant2", "assistant", now, user_id, thread_id),
        ],
        {"assistant1": None, "assistant2": None}
    ),
    (
        "multiple rapid user messages",
        lambda now, user_id, thread_id: [
            make_msg("user1", "user", now, user_id, thread_id),
            make_msg("user2", "user", now + timedelta(milliseconds=100), user_id, thread_id),
            make_msg("user3", "user", now + timedelta(milliseconds=200), user_id, thread_id),
            make_msg("user4", "user", now + timedelta(milliseconds=300), user_id, thread_id),
            make_msg("assistant1", "assistant", now + timedelta(seconds=1), user_id, thread_id),
        ],
        {"assistant1": "user4"}
    ),
    (
        "assistant messages with the same parent",
        lambda now, user_id, thread_id: [
            make_msg("user1", "user", now, user_id, thread_id),
            make_msg("assistant1", "assistant", now + timedelta(seconds=1), user_id, thread_id),
            make_msg("assistant2", "assistant", now + timedelta(seconds=2), user_id, thread_id),
            make_msg("user3", "user", now + timedelta(seconds=3), user_id, thread_id),
            make_msg("assistant3", "assistant", now + timedelta(seconds=4), user_id, thread_id),
        ],
        {"assistant1": "user1", "assistant2": "user1", "assistant3": "user3"}
    ),
    (
        "various content types for assistant messages with the same parent",
        lambda now, user_id, thread_id: [
            make_msg("user1", "user", now, user_id, thread_id),
            make_msg("assistant1", "assistant", now + timedelta(seconds=1), user_id, thread_id, content_type="text", text_content="hello!"),
            make_msg("assistant2", "assistant", now + timedelta(seconds=2), user_id, thread_id, content_type="recipe", text_content="recipe 1"),
            make_msg("assistant3", "assistant", now + timedelta(seconds=3), user_id, thread_id, content_type="tool", text_content="tool 1"),
            make_msg("assistant4", "assistant", now + timedelta(seconds=4), user_id, thread_id, content_type="text", text_content="hello again!"),
            make_msg("assistant5", "assistant", now + timedelta(seconds=5), user_id, thread_id, content_type="recipe", text_content="recipe 2"),
            make_msg("assistant6", "assistant", now + timedelta(seconds=6), user_id, thread_id, content_type="tool", text_content="tool 2"),
        ],
        {"assistant1": "user1", "assistant2": "user1", "assistant3": "user1", "assistant4": "user1", "assistant5": "user1", "assistant6": "user1"}
    )
]

@pytest.mark.parametrize("desc, msg_builder, expected_map", SCENARIOS)
def test_parent_id_migration_scenarios(desc, msg_builder, expected_map, pre_migration_schema, alembic_config, temp_db_url):
    engine = pre_migration_schema
    now = datetime.now(timezone.utc)
    user_id = str(uuid.uuid4())
    thread_id = str(uuid.uuid4())

    # Insert user and thread
    with Session(engine) as session:
        session.execute(text("""
            INSERT INTO users (id, email, name, password_hash, created_at, updated_at)
            VALUES (:id, :email, :name, 'pw', :ts, :ts)
        """), {"id": user_id, "email": f"{user_id}@example.com", "name": "T. User", "ts": now})
        session.execute(text("""
            INSERT INTO threads (id, user_id, created_at, updated_at, is_empty)
            VALUES (:id, :uid, :ts, :ts, 0)
        """), {"id": thread_id, "uid": user_id, "ts": now})
        session.commit()

    # Insert messages
    messages = msg_builder(now, user_id, thread_id)
    with Session(engine) as session:
        for msg in messages:
            session.execute(text("""
                INSERT INTO messages (id, user_id, thread_id, role, content_type, text_content, created_at, updated_at)
                VALUES (:id, :user_id, :thread_id, :role, :content_type, :text_content, :created_at, :updated_at)
            """), {
                "id": msg["id"],
                "user_id": msg["user_id"],
                "thread_id": msg["thread_id"],
                "role": msg["role"],
                "content_type": msg["content_type"],
                "text_content": msg["text_content"],
                "created_at": msg["created_at"],
                "updated_at": msg["created_at"],
            })
        session.commit()

    # Stamp DB at PREV_REVISION
    command.stamp(alembic_config, PREV_REVISION)
    # Run the migration under test
    command.upgrade(alembic_config, TARGET_REVISION)

    # Assertions
    with Session(engine) as session:
        for assistant_id, expected_parent in expected_map.items():
            parent = session.execute(text(
                "SELECT parent_id FROM messages WHERE id=:id"
            ), {"id": assistant_id}).scalar_one_or_none()
            assert parent == expected_parent, f"{desc}: assistant {assistant_id} expected parent {expected_parent}, got {parent}"

        # All user messages should have parent_id NULL
        user_parents = session.execute(text(
            "SELECT id, parent_id FROM messages WHERE role='user'"
        )).fetchall()
        for row in user_parents:
            assert row.parent_id is None, f"{desc}: user {row.id} should have parent_id NULL, got {row.parent_id}"

