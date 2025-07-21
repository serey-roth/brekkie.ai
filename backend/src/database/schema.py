import uuid

from sqlalchemy import JSON, Column, String, Integer, Text, ForeignKey, Enum, DateTime, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

from schemas.message_content_type import MessageContentType
from schemas.message_role import MessageRole

from utils.date_utils import strip_timezone

Base = declarative_base()


class DBThread(Base):
    __tablename__ = "threads"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)

    created_at = Column(DateTime, default=strip_timezone(datetime.now(timezone.utc)))
    updated_at = Column(DateTime, default=strip_timezone(datetime.now(timezone.utc)))
    resumed_at = Column(DateTime, nullable=True)

    error_message = Column(Text, nullable=True)  # TODO: Do we need thread-level error messages?
    title = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)

    is_empty = Column(Boolean, default=True)

    user = relationship("DBUser", back_populates="threads")
    messages = relationship("DBMessage", back_populates="thread", cascade="all, delete-orphan")
    recipes = relationship("DBRecipe", back_populates="thread", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DBThread(id='{self.id}', user_id='{self.user_id}', is_empty={self.is_empty})>"


class DBMessage(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), index=True)
    thread_id = Column(String, ForeignKey("threads.id"), index=True)

    parent_id = Column(String, ForeignKey("messages.id"), nullable=True)

    role = Column(Enum(MessageRole))
    content_type = Column(Enum(MessageContentType))
    text_content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=strip_timezone(datetime.now(timezone.utc)))
    updated_at = Column(DateTime, default=strip_timezone(datetime.now(timezone.utc)))

    model_name = Column(String, nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)

    tool_name = Column(String, nullable=True)
    tool_input = Column(JSON, nullable=True)
    tool_output = Column(JSON, nullable=True)

    recipe_id = Column(String, ForeignKey("recipes.id"), nullable=True)
    is_recipe_generation_started = Column(Boolean, nullable=True)
    is_recipe_generation_completed = Column(Boolean, nullable=True)

    ip_address = Column(String, nullable=True)

    safety_guard_result = Column(JSON, nullable=True)

    parent = relationship(
        "DBMessage",
        back_populates="children",
        uselist=False,
        remote_side=[id],  # This resolves the self-referencing relationship
    )
    children = relationship("DBMessage", back_populates="parent", cascade="all, delete-orphan")

    user = relationship("DBUser", back_populates="messages")
    thread = relationship("DBThread", back_populates="messages")
    recipe = relationship("DBRecipe", back_populates="message", uselist=False)

    def __repr__(self):
        return f"<DBMessage(id='{self.id}', role={self.role}, content_type={self.content_type})>"


class DBUser(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    external_id = Column(String, nullable=True, unique=True)
    created_at = Column(DateTime, default=strip_timezone(datetime.now(timezone.utc)))
    updated_at = Column(DateTime, default=strip_timezone(datetime.now(timezone.utc)))

    messages = relationship("DBMessage", back_populates="user", cascade="all, delete-orphan")
    threads = relationship("DBThread", back_populates="user", cascade="all, delete-orphan")
    recipes = relationship("DBRecipe", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DBUser(id='{self.id}', external_id='{self.external_id}')>"
    

class DBRecipe(Base):
    __tablename__ = "recipes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    thread_id = Column(String, ForeignKey("threads.id"), nullable=False)

    name = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    ingredients = Column(JSON, nullable=True)
    instructions = Column(JSON, nullable=True)
    categories = Column(JSON, nullable=True)
    prep_time_minutes = Column(Integer, nullable=True)
    cook_time_minutes = Column(Integer, nullable=True)
    servings = Column(String, nullable=True)
    created_at = Column(DateTime, default=strip_timezone(datetime.now(timezone.utc)))
    updated_at = Column(DateTime, default=strip_timezone(datetime.now(timezone.utc)))

    chef_notes = Column(Text, nullable=True)
    substitutions = Column(Text, nullable=True)
    equipment_alternatives = Column(Text, nullable=True)
    scaling_guidance = Column(Text, nullable=True)
    storage_notes = Column(Text, nullable=True)
    serving_suggestions = Column(Text, nullable=True)
    make_ahead_tips = Column(Text, nullable=True)
    coordination_timeline = Column(Text, nullable=True)

    user = relationship("DBUser", back_populates="recipes")
    message = relationship("DBMessage", back_populates="recipe")
    thread = relationship("DBThread", back_populates="recipes")

    def __repr__(self):
        return f"<DBRecipe(id='{self.id}', name='{self.name}', user_id='{self.user_id}')>"
