from typing import Literal
from datetime import datetime
from pydantic import BaseModel, Field


class Thread(BaseModel):
    id: str
    user_id: str
    created_at: str
    updated_at: str
    resumed_at: str | None = None
    error_message: str | None = None
    title: str | None = None
    summary: str | None = None
    is_empty: bool
    

class PaginatedThreads(BaseModel):
    threads: list[Thread]
    total_count: int
    has_more: bool
    next_timestamp: str | None = None


class BaseThreadParams(BaseModel):
    """Base parameters for thread operations."""

    resumed_at: datetime | None = Field(default=None, description="When the thread was resumed")
    title: str | None = Field(default=None, description="Thread title")
    summary: str | None = Field(default=None, description="Thread summary")
    error_message: str | None = Field(
        default=None, description="Error message if the thread failed"
    )


class CreateThreadParams(BaseThreadParams):
    """Parameters for creating a new thread."""

    id: str = Field(description="Unique thread identifier")
    user_id: str = Field(description="User who created the thread")
    created_at: datetime = Field(description="When the thread was created")
    updated_at: datetime = Field(description="When the thread was last modified")
    is_empty: bool = Field(description="Whether the thread is empty")


class GetUserThreadsParams(BaseModel):
    """Parameters for getting user threads with pagination and sorting.

    Attributes:
        - user_id: User who created the thread
        - limit: Number of threads to return (min 1, max 100) (default 10)
        - from_timestamp: Timestamp to start from
        - sort_by: Field to sort by (default "updated_at")
        - sort_order: Sort order (default "desc")
        - exclude_empty: Whether to exclude empty threads (default False)
    """

    user_id: str = Field(description="User who created the thread")
    limit: int = Field(ge=1, le=100, default=10, description="Number of threads to return")
    from_timestamp: datetime | None = Field(default=None, description="Timestamp to start from")
    sort_by: Literal["created_at", "updated_at"] = Field(
        default="updated_at", description="Field to sort by"
    )
    sort_order: Literal["asc", "desc"] = Field(default="desc", description="Sort order")
    exclude_empty: bool = Field(default=False, description="Whether to exclude empty threads")


class GetDBUserThreadsParams(BaseModel):
    """Parameters for getting user threads with pagination and sorting.

    Attributes:
        - user_id: User who created the thread
        - limit: Number of threads to return (min 1, max 101) (default 10) (100+1 for paginated limit and has_more flag)
        - from_timestamp: Timestamp to start from
        - sort_by: Field to sort by (default "updated_at")
        - sort_order: Sort order (default "desc")
        - exclude_empty: Whether to exclude empty threads (default False)
    """

    user_id: str = Field(description="User who created the thread")
    limit: int = Field(
        ge=1,
        le=101,
        default=10,
        description="Number of threads to return (100+1 for paginated limit and has_more flag)",
    )
    from_timestamp: datetime | None = Field(default=None, description="Timestamp to start from")
    sort_by: Literal["created_at", "updated_at"] = Field(
        default="updated_at", description="Field to sort by"
    )
    sort_order: Literal["asc", "desc"] = Field(default="desc", description="Sort order")
    exclude_empty: bool = Field(default=False, description="Whether to exclude empty threads")


class UpdateThreadParams(BaseThreadParams):
    """Parameters for updating a thread."""

    id: str = Field(description="Thread ID")
    updated_at: datetime = Field(description="When the thread was last modified")
    is_empty: bool | None = Field(default=None, description="Whether the thread is empty")


class ResumeThreadParams(BaseModel):
    """Parameters for resuming a thread."""

    id: str = Field(description="Thread ID")
    resumed_at: datetime = Field(description="When the thread was resumed")
