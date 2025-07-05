from dataclasses import dataclass, asdict
from enum import Enum
from string import Template


class ChatSessionErrorType(str, Enum):
    ACCESS_TOKEN_NOT_FOUND = "access_token_not_found"
    OVER_MESSAGE_LIMIT = "over_message_limit"
    THREAD_NOT_FOUND = "thread_not_found"
    INTERNAL_SERVER_ERROR = "internal_server_error"
    INVALID_PAYLOAD = "invalid_payload"
    SESSION_CLOSED = "session_closed"
    CUSTOM = "custom_error"


@dataclass(frozen=True)
class ChatSessionError(Exception):
    code: int
    type: ChatSessionErrorType
    message_template: str

    def format_message(self, **kwargs) -> str:
        """Format the message template with provided variables."""
        template = Template(self.message_template)
        return template.safe_substitute(kwargs)

    def dict(self, **kwargs) -> dict:
        """Return dictionary representation with formatted message."""
        data = asdict(self)
        data['message'] = self.format_message(**kwargs)
        return data


class AccessTokenNotFoundError(ChatSessionError):
    def __init__(self, access_token: str):
        self.access_token = access_token
        super().__init__(
            code=4400,
            type=ChatSessionErrorType.ACCESS_TOKEN_NOT_FOUND,
            message_template="Access token not found: ${access_token}. Please refresh the page and try again."
        )
        
    def dict(self, **kwargs) -> dict:
        data = super().dict(access_token=self.access_token)
        return data

class OverMessageLimitError(ChatSessionError):
    def __init__(self, message_limit: int):
        self.message_limit = message_limit
        super().__init__(
            code=4403,
            type=ChatSessionErrorType.OVER_MESSAGE_LIMIT,
            message_template="You've reached your limit of ${message_limit} messages."
        )
        
    def dict(self, **kwargs) -> dict:
        data = super().dict(message_limit=self.message_limit)
        return data
    
    
class ThreadNotFoundError(ChatSessionError):
    def __init__(self, thread_id: str):
        self.thread_id = thread_id
        super().__init__(
            code=4404,
            type=ChatSessionErrorType.THREAD_NOT_FOUND,
            message_template="We couldn't find thread ${thread_id}. Please start a new session."
        )
        
    def dict(self, **kwargs) -> dict:
        data = super().dict(thread_id=self.thread_id)
        return data
    
    
class InternalServerError(ChatSessionError):
    def __init__(self):
        super().__init__(
            code=4500,
            type=ChatSessionErrorType.INTERNAL_SERVER_ERROR,
            message_template="Something went wrong on our end. We're currently working on it."
        )
        
    def dict(self, **kwargs) -> dict:
        data = super().dict()
        return data
    
    
class InvalidPayloadError(ChatSessionError):
    def __init__(self, payload: str):
        self.payload = payload
        super().__init__(
            code=4405,
            type=ChatSessionErrorType.INVALID_PAYLOAD,
            message_template="Invalid payload: ${payload}. Please try again."
        )
        
    def dict(self, **kwargs) -> dict:
        data = super().dict(payload=self.payload)
        return data
    
    
class SessionClosedError(ChatSessionError):
    def __init__(self, access_token: str, close_reason: str):
        self.access_token = access_token
        self.close_reason = close_reason
        super().__init__(
            code=4408,
            type=ChatSessionErrorType.SESSION_CLOSED,
            message_template="Session ${access_token} closed due to: ${close_reason}."
        )
        
    def dict(self, **kwargs) -> dict:
        data = super().dict(access_token=self.access_token, close_reason=self.close_reason)
        return data
    
    
class CustomError(ChatSessionError):
    def __init__(self, message: str):
        self.message = message
        super().__init__(
            code=4407,
            type=ChatSessionErrorType.CUSTOM,
            message_template="${custom_message}"
        )
        
    def dict(self, **kwargs) -> dict:
        data = super().dict(custom_message=self.message)
        return data
    
