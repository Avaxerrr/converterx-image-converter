"""
App Settings UI Components

Provides a settings dialog with sidebar navigation for configuring
app performance, preview, and default conversion settings.

This package uses dependency injection - the AppSettingsController is passed
to all components rather than being a singleton. This makes testing easier
and dependencies explicit.
"""

from .app_settings_dialog import AppSettingsDialog
from .performance_page import PerformanceSettingsPage
from .preview_page import PreviewSettingsPage
from .defaults_page import DefaultSettingsPage

__all__ = [
    'AppSettingsDialog',
    'PerformanceSettingsPage',
    'PreviewSettingsPage',
    'DefaultSettingsPage'
]
