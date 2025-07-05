import os
import pytest
from alembic.config import Config
from sqlalchemy import create_engine

PREV_REVISION = "11d1b10382cf"
ALEMBIC_INI_PATH = "alembic.ini"
ALEMBIC_SCRIPT_LOCATION = "alembic"

@pytest.fixture
def temp_db_url(tmp_path):
    db_path = tmp_path / "parent_id_test.db"
    db_url = f"sqlite:///{db_path}"
    return db_url

@pytest.fixture
def alembic_config(temp_db_url):
    # Set the DB_URL env var for Alembic env.py
    os.environ["DB_URL"] = temp_db_url
    alembic_cfg = Config(ALEMBIC_INI_PATH)
    alembic_cfg.set_main_option("sqlalchemy.url", temp_db_url)
    alembic_cfg.set_main_option("script_location", ALEMBIC_SCRIPT_LOCATION)
    return alembic_cfg

@pytest.fixture
def pre_migration_schema(temp_db_url):
    engine = create_engine(temp_db_url, echo=False, future=True)
    with engine.begin() as conn:
        conn.exec_driver_sql("""
            CREATE TABLE users (
                id VARCHAR PRIMARY KEY,
                email VARCHAR UNIQUE,
                name VARCHAR,
                password_hash VARCHAR,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            );
        """)
        conn.exec_driver_sql("""
            CREATE TABLE threads (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                resumed_at TIMESTAMP,
                error_message TEXT,
                title TEXT,
                summary TEXT,
                is_empty BOOLEAN NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
        """)
        conn.exec_driver_sql("""
            CREATE TABLE recipes (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL,
                thread_id VARCHAR NOT NULL,
                name VARCHAR,
                description TEXT,
                ingredients TEXT,
                instructions TEXT,
                categories TEXT,
                prep_time_minutes INTEGER,
                cook_time_minutes INTEGER,
                servings VARCHAR,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                chef_notes TEXT,
                substitutions TEXT,
                equipment_alternatives TEXT,
                scaling_guidance TEXT,
                storage_notes TEXT,
                serving_suggestions TEXT,
                make_ahead_tips TEXT,
                coordination_timeline TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(thread_id) REFERENCES threads(id)
            );
        """)
        conn.exec_driver_sql("""
            CREATE TABLE messages (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR,
                thread_id VARCHAR,
                role TEXT,
                content_type TEXT,
                text_content TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                model_name VARCHAR,
                input_tokens INTEGER,
                output_tokens INTEGER,
                tool_name VARCHAR,
                tool_input TEXT,
                tool_output TEXT,
                recipe_id VARCHAR,
                is_recipe_generation_started BOOLEAN,
                is_recipe_generation_completed BOOLEAN,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(thread_id) REFERENCES threads(id),
                FOREIGN KEY(recipe_id) REFERENCES recipes(id)
            );
        """)
    return engine