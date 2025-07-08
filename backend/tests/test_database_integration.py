import pytest
from config.settings import Settings
from database.index import create_db_transaction_maker


def test_create_db_transaction_maker():
    """Test that we can create a database transaction maker with settings."""
    # Create test settings with SQLite-compatible configuration
    test_settings = Settings(
        db_url="sqlite+aiosqlite:///:memory:",  # Use in-memory SQLite for testing
        environment="development",
        # SQLite doesn't support these pool options, so we'll use defaults
        db_pool_size=5,
        db_max_overflow=10,
        db_pool_timeout=30,
        db_pool_recycle=3600,
    )
    
    # Create the transaction maker
    db_transaction_maker = create_db_transaction_maker(test_settings)
    
    # Verify it's callable (a context manager)
    assert callable(db_transaction_maker)
    
    # Test that we can create another one with different settings
    test_settings_2 = Settings(
        db_url="sqlite+aiosqlite:///:memory:",
        environment="production",
        db_pool_size=5,
        db_max_overflow=10,
        db_pool_timeout=30,
        db_pool_recycle=3600,
    )
    
    db_transaction_maker_2 = create_db_transaction_maker(test_settings_2)
    assert callable(db_transaction_maker_2)


def test_db_transaction_maker_with_invalid_url():
    """Test that creating a transaction maker with invalid DB URL raises an error."""
    test_settings = Settings(
        db_url=None,  # Invalid/None URL
        environment="development",
    )
    
    with pytest.raises(ValueError, match="DB_URL environment variable is not set"):
        create_db_transaction_maker(test_settings) 