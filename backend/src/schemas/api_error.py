from dataclasses import dataclass
from enum import Enum
from string import Template


class ApiErrorType(str, Enum):
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"


@dataclass(frozen=True)
class ApiError(Exception):
    type: ApiErrorType
    message_template: str
    
    def format_message(self, **kwargs) -> str:
        template = Template(self.message_template)
        return template.safe_substitute(kwargs)
    
    
class RateLimitError(ApiError):
    def __init__(self, ip_address: str):
        super().__init__(
            type=ApiErrorType.RATE_LIMIT_EXCEEDED,
            message_template="Rate limit exceeded for IP address: {ip_address}",
        )
