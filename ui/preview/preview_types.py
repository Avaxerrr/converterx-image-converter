"""
Types and enums for preview functionality.
"""

from enum import Enum


class PreviewMode(Enum):
    """Preview display modes."""
    PREVIEW = "preview"  # Scaled down for performance (default)
    HD = "hd"           # Full resolution
