
"""
Settings components package for ConverterX.

This package contains modular settings widgets that compose the main SettingsPanel.
Each component is responsible for a specific category of conversion settings.
"""

from .settings_panel import SettingsPanel
from .collapsible_section import CollapsibleSection
from .output_settings import OutputSettingsWidget
from .resize_settings import ResizeSettingsWidget
from .advanced_settings import AdvancedSettingsWidget

__all__ = [
    'SettingsPanel',
    'CollapsibleSection',
    'OutputSettingsWidget',
    'ResizeSettingsWidget',
    'AdvancedSettingsWidget'
]