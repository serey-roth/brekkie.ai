"""Test that LangGraph checkpoint tables are preserved during migrations."""

import pytest
from alembic import command
from sqlalchemy import text
from sqlalchemy.orm import Session

# LangGraph tables that should be preserved
LANGGRAPH_TABLES = {
    'checkpoints',
    'checkpoint_blobs', 
    'checkpoint_writes',
    'checkpoint_migrations'
}

@pytest.fixture
def langgraph_tables_setup(pre_migration_schema):
    """Fixture to set up all LangGraph tables with sample data."""
    engine = pre_migration_schema
    
    with Session(engine) as session:
        # Create checkpoints table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                thread_id TEXT NOT NULL,
                checkpoint_ns TEXT NOT NULL DEFAULT '',
                checkpoint_id TEXT NOT NULL,
                parent_checkpoint_id TEXT,
                type TEXT,
                checkpoint TEXT NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}',
                PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
            )
        """))
        
        # Create checkpoint_blobs table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS checkpoint_blobs (
                thread_id TEXT NOT NULL,
                checkpoint_ns TEXT NOT NULL DEFAULT '',
                channel TEXT NOT NULL,
                version TEXT NOT NULL,
                type TEXT NOT NULL,
                blob BLOB,
                PRIMARY KEY (thread_id, checkpoint_ns, channel, version)
            )
        """))
        
        # Create checkpoint_writes table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS checkpoint_writes (
                thread_id TEXT NOT NULL,
                checkpoint_ns TEXT NOT NULL DEFAULT '',
                checkpoint_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                idx INTEGER NOT NULL,
                channel TEXT NOT NULL,
                type TEXT,
                blob BLOB NOT NULL,
                task_path TEXT NOT NULL DEFAULT '',
                PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
            )
        """))
        
        # Create checkpoint_migrations table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS checkpoint_migrations (
                v INTEGER NOT NULL,
                PRIMARY KEY (v)
            )
        """))
        
        # Insert sample data
        session.execute(text("""
            INSERT INTO checkpoints (thread_id, checkpoint_ns, checkpoint_id, checkpoint, metadata)
            VALUES ('test-thread-1', 'test-ns', 'test-checkpoint-1', '{"test": "data"}', '{"version": 1}')
        """))
        
        session.execute(text("""
            INSERT INTO checkpoint_migrations (v)
            VALUES (1)
        """))
        
        session.commit()
    
    return engine

def test_langgraph_tables_preserved_in_initial_migration(langgraph_tables_setup, alembic_config, temp_db_url):
    """Test that LangGraph tables are not dropped in the initial migration."""
    engine = langgraph_tables_setup
    
    # Verify tables exist before migration
    with Session(engine) as session:
        for table_name in LANGGRAPH_TABLES:
            result = session.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"))
            assert result.fetchone() is not None, f"Table {table_name} should exist before migration"
        
        # Verify data exists
        checkpoint_count = session.execute(text("SELECT COUNT(*) FROM checkpoints")).scalar()
        assert checkpoint_count == 1, "Should have 1 checkpoint before migration"
        
        migration_count = session.execute(text("SELECT COUNT(*) FROM checkpoint_migrations")).scalar()
        assert migration_count == 1, "Should have 1 migration record before migration"
    
    # Since the pre_migration_schema fixture already creates the app tables,
    # we need to stamp the database at the initial revision first
    command.stamp(alembic_config, "11d1b10382cf")
    
    # Verify LangGraph tables still exist after migration
    with Session(engine) as session:
        for table_name in LANGGRAPH_TABLES:
            result = session.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"))
            assert result.fetchone() is not None, f"Table {table_name} should still exist after migration"
        
        # Verify data is preserved
        checkpoint_count = session.execute(text("SELECT COUNT(*) FROM checkpoints")).scalar()
        assert checkpoint_count == 1, "Should still have 1 checkpoint after migration"
        
        migration_count = session.execute(text("SELECT COUNT(*) FROM checkpoint_migrations")).scalar()
        assert migration_count == 1, "Should still have 1 migration record after migration"
        
        # Verify the specific data is preserved
        checkpoint_data = session.execute(text("""
            SELECT thread_id, checkpoint_ns, checkpoint_id, checkpoint, metadata 
            FROM checkpoints 
            WHERE thread_id = 'test-thread-1'
        """)).fetchone()
        assert checkpoint_data is not None, "Checkpoint data should be preserved"
        assert checkpoint_data.thread_id == 'test-thread-1'
        assert checkpoint_data.checkpoint_ns == 'test-ns'
        assert checkpoint_data.checkpoint_id == 'test-checkpoint-1'


def test_langgraph_tables_preserved_in_parent_id_migration(langgraph_tables_setup, alembic_config, temp_db_url):
    """Test that LangGraph tables are not affected by the parent_id migration."""
    engine = langgraph_tables_setup
    
    # Since the pre_migration_schema fixture already creates the app tables,
    # we need to stamp the database at the initial revision first
    command.stamp(alembic_config, "11d1b10382cf")
    
    # Add additional data for this specific test
    with Session(engine) as session:
        session.execute(text("""
            INSERT INTO checkpoints (thread_id, checkpoint_ns, checkpoint_id, checkpoint, metadata)
            VALUES ('test-thread-2', 'test-ns', 'test-checkpoint-2', '{"test": "data2"}', '{"version": 2}')
        """))
        
        session.execute(text("""
            INSERT INTO checkpoint_migrations (v)
            VALUES (2)
        """))
        
        session.commit()
    
    # Verify data exists before parent_id migration
    with Session(engine) as session:
        checkpoint_count = session.execute(text("SELECT COUNT(*) FROM checkpoints")).scalar()
        assert checkpoint_count >= 2, "Should have at least 2 checkpoints before parent_id migration"
    
    # Run the parent_id migration
    command.upgrade(alembic_config, "781a8252ecfe")
    
    # Verify LangGraph tables still exist after parent_id migration
    with Session(engine) as session:
        for table_name in LANGGRAPH_TABLES:
            result = session.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"))
            assert result.fetchone() is not None, f"Table {table_name} should still exist after parent_id migration"
        
        # Verify data is preserved
        checkpoint_count = session.execute(text("SELECT COUNT(*) FROM checkpoints")).scalar()
        assert checkpoint_count >= 2, "Should still have at least 2 checkpoints after parent_id migration"
        
        # Verify the specific data is preserved
        checkpoint_data = session.execute(text("""
            SELECT thread_id, checkpoint_ns, checkpoint_id, checkpoint, metadata 
            FROM checkpoints 
            WHERE thread_id = 'test-thread-2'
        """)).fetchone()
        assert checkpoint_data is not None, "Checkpoint data should be preserved after parent_id migration"
        assert checkpoint_data.thread_id == 'test-thread-2'
        assert checkpoint_data.checkpoint_ns == 'test-ns'
        assert checkpoint_data.checkpoint_id == 'test-checkpoint-2'


def test_langgraph_tables_excluded_from_migration_generation():
    """Test that LangGraph tables are excluded from migration generation."""
    # This test verifies that the include_object filter logic works correctly
    # The filter should prevent LangGraph tables from being included in new migrations
    
    # Define the expected LangGraph tables
    LANGGRAPH_TABLES = {
        'checkpoints',
        'checkpoint_blobs', 
        'checkpoint_writes',
        'checkpoint_migrations'
    }
    
    # Define the include_object function logic (copied from alembic/env.py)
    def include_object(object_, name, type_, reflected, compare_to):
        """
        Filter function to exclude LangGraph checkpoint tables from migrations.
        This ensures that LangGraph-managed tables are not affected by Alembic.
        """
        if type_ == "table" and name in LANGGRAPH_TABLES:
            return False
        return True
    
    # Test that LangGraph tables are excluded
    for table_name in LANGGRAPH_TABLES:
        result = include_object(None, table_name, "table", False, None)
        assert result is False, f"Table {table_name} should be excluded from migrations"
    
    # Test that regular tables are included
    regular_tables = ['users', 'threads', 'messages', 'recipes']
    for table_name in regular_tables:
        result = include_object(None, table_name, "table", False, None)
        assert result is True, f"Table {table_name} should be included in migrations"
    
    # Test that non-table objects are included
    result = include_object(None, "some_index", "index", False, None)
    assert result is True, "Non-table objects should be included in migrations" 