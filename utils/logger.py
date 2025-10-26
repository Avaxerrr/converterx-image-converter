"""
Application-wide logger with thread-safe operation and multiple log levels.
Can be used from anywhere in the application.
"""

from enum import Enum
from datetime import datetime
from typing import List, Callable, Optional
from threading import Lock
from dataclasses import dataclass


class LogLevel(Enum):
    """Log message levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class LogMessage:
    """Represents a single log message."""
    timestamp: datetime
    level: LogLevel
    message: str
    source: str = ""  # Optional: where the log came from (e.g., "Converter", "FileLoader")

    def __str__(self) -> str:
        time_str = self.timestamp.strftime("%H:%M:%S")
        source_str = f"[{self.source}] " if self.source else ""
        return f"[{time_str}] [{self.level.value}] {source_str}{self.message}"


class AppLogger:
    """
    Singleton application logger.
    Thread-safe, can be used from any part of the application.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._messages: List[LogMessage] = []
        self._callbacks: List[Callable[[LogMessage], None]] = []
        self._max_messages = 1000  # Keep last 1000 messages
        self._enabled = True

    def add_callback(self, callback: Callable[[LogMessage], None]):
        """
        Add a callback to be notified of new log messages.
        Useful for updating UI in real-time.
        """
        with self._lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[LogMessage], None]):
        """Remove a callback."""
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

    def log(self, level: LogLevel, message: str, source: str = ""):
        """Log a message at the specified level."""
        if not self._enabled:
            return

        log_msg = LogMessage(
            timestamp=datetime.now(),
            level=level,
            message=message,
            source=source
        )

        with self._lock:
            self._messages.append(log_msg)

            # Trim old messages if we exceed max
            if len(self._messages) > self._max_messages:
                self._messages = self._messages[-self._max_messages:]

            # Notify all callbacks
            for callback in self._callbacks:
                try:
                    callback(log_msg)
                except Exception as e:
                    print(f"Error in log callback: {e}")

    def debug(self, message: str, source: str = ""):
        """Log a debug message."""
        self.log(LogLevel.DEBUG, message, source)

    def info(self, message: str, source: str = ""):
        """Log an info message."""
        self.log(LogLevel.INFO, message, source)

    def success(self, message: str, source: str = ""):
        """Log a success message."""
        self.log(LogLevel.SUCCESS, message, source)

    def warning(self, message: str, source: str = ""):
        """Log a warning message."""
        self.log(LogLevel.WARNING, message, source)

    def error(self, message: str, source: str = ""):
        """Log an error message."""
        self.log(LogLevel.ERROR, message, source)

    def get_messages(self, level: Optional[LogLevel] = None) -> List[LogMessage]:
        """
        Get all log messages, optionally filtered by level.

        Args:
            level: If specified, only return messages of this level
        """
        with self._lock:
            if level is None:
                return self._messages.copy()
            return [msg for msg in self._messages if msg.level == level]

    def clear(self):
        """Clear all log messages."""
        with self._lock:
            self._messages.clear()

    def set_enabled(self, enabled: bool):
        """Enable or disable logging."""
        self._enabled = enabled

    def is_enabled(self) -> bool:
        """Check if logging is enabled."""
        return self._enabled


# Global logger instance
logger = AppLogger()
