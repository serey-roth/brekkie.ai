import logging
import os
from typing import Any


class Logger:
    def __init__(self, name: str, level: str | None = None):
        if level is None:
            level = "DEBUG" if os.getenv("ENVIRONMENT", "production") == "development" else "INFO"

        if not logging.getLogger().handlers:
            logging.basicConfig(
                level=level,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )

        self.logger = logging.getLogger(name)

    def info(self, message: str, *args: Any, **kwargs: Any):
        self.logger.info(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any):
        self.logger.error(message, exc_info=True, *args, **kwargs)

    def debug(self, message: str, *args: Any, **kwargs: Any):
        self.logger.debug(message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any):
        self.logger.warning(message, *args, **kwargs)
