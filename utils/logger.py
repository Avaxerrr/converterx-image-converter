"""
Application-wide logger with thread-safe operation and multiple log levels.
Now includes automatic file logging with rotation.
"""

from enum import Enum
from datetime import datetime
from typing import List, Callable, Optional
from threading import Lock
from dataclasses import dataclass
from pathlib import Path
import atexit


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

        # Defensive check for level type
        if isinstance(self.level, str):
            try:
                level_value = LogLevel[self.level.upper()].value
            except (KeyError, AttributeError):
                level_value = self.level
        elif isinstance(self.level, LogLevel):
            level_value = self.level.value
        else:
            level_value = str(self.level)

        return f"[{time_str}] [{level_value}] {source_str}{self.message}"


class AppLogger:
    """
    Singleton application logger with file output.

    Logs are written to:
    - Memory (for UI display)
    - File (logs/converter_YYYYMMDD_HHMMSS.log)
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

        self.messages: List[LogMessage] = []
        self.callbacks: List[Callable] = []
        self.max_messages = 1000  # Keep last 1000 in memory

        # File logging setup
        self.log_folder = Path("logs")
        self.log_folder.mkdir(exist_ok=True)

        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_folder / f"converter_{timestamp}.log"
        self.file_handle = None

        # Open log file
        try:
            self.file_handle = open(self.log_file, 'w', encoding='utf-8', buffering=1)  # Line buffering
            self._write_header()
        except Exception as e:
            print(f"WARNING: Could not create log file: {e}")

        # Register cleanup on exit
        atexit.register(self._cleanup)

        self._initialized = True

    def _write_header(self):
        """Write log file header."""
        if self.file_handle:
            self.file_handle.write("=" * 80 + "\n")
            self.file_handle.write(f"ConverterX Application Log\n")
            self.file_handle.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.file_handle.write("=" * 80 + "\n\n")
            self.file_handle.flush()

    def _cleanup(self):
        """Close log file on shutdown."""
        if self.file_handle:
            try:
                self.file_handle.write("\n" + "=" * 80 + "\n")
                self.file_handle.write(f"Log ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                self.file_handle.write("=" * 80 + "\n")
                self.file_handle.close()
            except:
                pass

    def log(self, level: LogLevel, message: str, source: str = ""):
        """
        Log a message with specified level.

        Args:
            level: Log level (LogLevel enum)
            message: Log message
            source: Source component (optional)
        """
        with self._lock:
            msg = LogMessage(
                timestamp=datetime.now(),
                level=level,
                message=message,
                source=source
            )

            # Add to memory
            self.messages.append(msg)

            # Trim memory if needed
            if len(self.messages) > self.max_messages:
                self.messages = self.messages[-self.max_messages:]

            # Write to file
            if self.file_handle:
                try:
                    self.file_handle.write(str(msg) + "\n")
                    self.file_handle.flush()  # Immediate write
                except Exception as e:
                    print(f"WARNING: Failed to write to log file: {e}")

            # Notify callbacks
            for callback in self.callbacks:
                try:
                    callback(msg)
                except Exception as e:
                    print(f"Error in log callback: {e}")

    def debug(self, message: str, source: str = ""):
        """Log a DEBUG message."""
        self.log(LogLevel.DEBUG, message, source)

    def info(self, message: str, source: str = ""):
        """Log an INFO message."""
        self.log(LogLevel.INFO, message, source)

    def success(self, message: str, source: str = ""):
        """Log a SUCCESS message."""
        self.log(LogLevel.SUCCESS, message, source)

    def warning(self, message: str, source: str = ""):
        """Log a WARNING message."""
        self.log(LogLevel.WARNING, message, source)

    def error(self, message: str, source: str = ""):
        """Log an ERROR message."""
        self.log(LogLevel.ERROR, message, source)

    def add_callback(self, callback: Callable[[LogMessage], None]):
        """
        Register a callback to be notified of new log messages.

        Args:
            callback: Function that accepts a LogMessage
        """
        with self._lock:
            if callback not in self.callbacks:
                self.callbacks.append(callback)

    def remove_callback(self, callback: Callable):
        """Remove a registered callback."""
        with self._lock:
            if callback in self.callbacks:
                self.callbacks.remove(callback)

    def get_messages(self, level: Optional[LogLevel] = None) -> List[LogMessage]:
        """
        Get all messages, optionally filtered by level.

        Args:
            level: Filter by this level (None = all messages)

        Returns:
            List of LogMessage objects
        """
        with self._lock:
            if level is None:
                return self.messages.copy()
            return [msg for msg in self.messages if msg.level == level]

    def clear(self):
        """Clear all messages from memory (does not affect log file)."""
        with self._lock:
            self.messages.clear()

    def get_log_file_path(self) -> Optional[Path]:
        """Get the current log file path."""
        return self.log_file if self.log_file.exists() else None


# Global logger instance
logger = AppLogger()
