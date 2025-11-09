"""
Application Settings Controller

Manages persistent app settings using QSettings with signal-based notifications.
NOT a singleton - create once in MainWindow and pass to components via dependency injection.

Settings Categories:
- Performance: Worker threads, concurrent conversions
- Preview: Cache sizes, max dimensions, debounce timing
- Defaults: Default quality and format for conversions
"""
from pathlib import Path

from PySide6.QtCore import QObject, Signal, QSettings, QThreadPool
from typing import Optional, cast
from core.format_settings import ImageFormat, OutputLocationMode, FilenameTemplate
from utils.logger import logger


class SettingsKeys:
    """
    Centralized string constants for QSettings keys.

    Prevents typos, enables IDE autocomplete, and makes refactoring safe.
    All keys use category/setting_name format for organization.
    """

    # Performance category
    MAX_CONCURRENT_WORKERS = "performance/max_concurrent_workers"
    THREADPOOL_MAX_THREADS = "performance/threadpool_max_threads"

    # Preview category
    PREVIEW_CACHE_SIZE = "preview/cache_size"
    HD_CACHE_SIZE = "preview/hd_cache_size"
    PREVIEW_MAX_DIMENSION = "preview/max_dimension"
    OUTPUT_PREVIEW_DEBOUNCE = "preview/output_preview_debounce"
    OUTPUT_PREVIEW_CACHE_SIZE = "preview/output_preview_cache_size"

    # Defaults category
    DEFAULT_QUALITY = "defaults/quality"
    DEFAULT_OUTPUT_FORMAT = "defaults/output_format"
    DEFAULT_OUTPUT_LOCATION_MODE = "defaults/output_location_mode"
    DEFAULT_CUSTOM_OUTPUT_FOLDER = "defaults/custom_output_folder"
    DEFAULT_ENABLE_FILENAME_SUFFIX = "defaults/enable_filename_suffix"
    DEFAULT_FILENAME_TEMPLATE = "defaults/filename_template"
    DEFAULT_CUSTOM_SUFFIX = "defaults/custom_suffix"
    DEFAULT_AUTO_INCREMENT = "defaults/auto_increment"


class AppSettingsController(QObject):
    """
    Controller for application settings with signal-based change notifications.

    This is NOT a singleton - create once in MainWindow and inject into
    components that need access to settings.

    Inherits from QObject to emit signals when settings change, allowing
    components to reactively update without tight coupling.

    Usage:
        # In MainWindow.__init__
        self.app_settings = AppSettingsController()

        # Pass to components
        self.preview = PreviewWidget(controller=self.app_settings)

        # Listen to changes
        self.app_settings.preview_changed.connect(self._on_preview_changed)
    """

    # Signals emitted when settings in each category change
    performance_changed = Signal()
    preview_changed = Signal()
    defaults_changed = Signal()
    clear_caches_requested = Signal()
    def __init__(self, settings: Optional[QSettings] = None):
        """
        Initialize settings controller.

        Args:
            settings: Optional QSettings instance. If None, creates default
                     QSettings for "ConverterX". Pass custom instance for testing.
        """
        super().__init__()
        self.settings = settings or QSettings("ConverterX", "AppSettings")

    # ============================================================
    # PERFORMANCE SETTINGS - Getters
    # ============================================================

    def get_max_concurrent_workers(self) -> int:
        """
        Get maximum concurrent workers for batch processing.

        Returns:
            Number of images converted simultaneously (1-16, default 4)
        """
        value = self.settings.value(
            SettingsKeys.MAX_CONCURRENT_WORKERS,
            4,  # Default
            type=int
        )
        return cast(int, value)  # Type assertion for type checker

    def get_threadpool_max_threads(self) -> int:
        """
        Get maximum thread pool size for background tasks.

        Returns:
            Max threads for thumbnails/previews (1-32, default is system max)
        """
        default = QThreadPool.globalInstance().maxThreadCount()
        value = self.settings.value(
            SettingsKeys.THREADPOOL_MAX_THREADS,
            default,
            type=int
        )
        return cast(int, value)  # Type assertion for type checker

    # ============================================================
    # PREVIEW SETTINGS - Getters
    # ============================================================

    def get_preview_cache_size(self) -> int:
        """
        Get preview cache size.

        Returns:
            Number of preview images kept in memory (1-50, default 10)
        """
        value = self.settings.value(
            SettingsKeys.PREVIEW_CACHE_SIZE,
            10,  # Default
            type=int
        )
        return cast(int, value)  # Type assertion for type checker

    def get_hd_cache_size(self) -> int:
        """
        Get HD cache size.

        Returns:
            Number of full-resolution images kept in memory (1-20, default 2)
        """
        value = self.settings.value(
            SettingsKeys.HD_CACHE_SIZE,
            2,  # Default
            type=int
        )
        return cast(int, value)  # Type assertion for type checker

    def get_preview_max_dimension(self) -> int:
        """
        Get preview maximum dimension.

        Returns:
            Max width/height for preview mode in pixels (720-4096, default 1500)
        """
        value = self.settings.value(
            SettingsKeys.PREVIEW_MAX_DIMENSION,
            1500,  # Default
            type=int
        )
        return cast(int, value)  # Type assertion for type checker

    def get_out_preview_debounce(self) -> int:
        """
        Get output preview debounce delay.

        Returns:
            Delay before regenerating output preview in milliseconds (100-2000, default 250)
        """
        value = self.settings.value(
            SettingsKeys.OUTPUT_PREVIEW_DEBOUNCE,
            250,  # Default
            type=int
        )
        return cast(int, value)  # Type assertion for type checker

    def get_output_preview_cache_size(self) -> int:
        """
        Get output preview cache size.

        Returns:
            Number of output previews kept in memory (1-20, default 2)
        """
        value = self.settings.value(
            SettingsKeys.OUTPUT_PREVIEW_CACHE_SIZE,
            2,  # Default
            type=int
        )
        return cast(int, value)

    # ============================================================
    # DEFAULTS SETTINGS - Getters
    # ============================================================

    def get_default_quality(self) -> int:
        """
        Get default conversion quality.

        Returns:
            Default quality setting (1-100, default 85)
        """
        value = self.settings.value(
            SettingsKeys.DEFAULT_QUALITY,
            85,  # Default
            type=int
        )
        return cast(int, value)  # Type assertion for type checker

    def get_default_output_format(self) -> ImageFormat:
        """
        Get default output format.

        Returns:
            Default output format enum (default ImageFormat.WEBP)
        """
        format_str = self.settings.value(
            SettingsKeys.DEFAULT_OUTPUT_FORMAT,
            "WEBP",  # Default
            type=str
        )

        # Cast to str for type checker
        format_str = cast(str, format_str)

        # Convert string to ImageFormat enum
        format_map = {
            "WEBP": ImageFormat.WEBP,
            "AVIF": ImageFormat.AVIF,
            "JPEG": ImageFormat.JPEG,
            "PNG": ImageFormat.PNG
        }

        return format_map.get(format_str, ImageFormat.WEBP)

    def get_default_output_location_mode(self) -> OutputLocationMode:
        raw = self.settings.value(SettingsKeys.DEFAULT_OUTPUT_LOCATION_MODE, "custom")
        mode_str: str = raw if isinstance(raw, str) else str(raw)
        mapping: dict[str, OutputLocationMode] = {
            "custom": OutputLocationMode.CUSTOM_FOLDER,
            "same": OutputLocationMode.SAME_AS_SOURCE,
            "ask": OutputLocationMode.ASK_EVERY_TIME,
        }
        return mapping.get(mode_str, OutputLocationMode.CUSTOM_FOLDER)

    def get_default_custom_output_folder(self) -> Path:
        # Default to ~/Pictures/Converted
        default_path = Path.home() / "Pictures" / "Converted"
        raw = self.settings.value(
            SettingsKeys.DEFAULT_CUSTOM_OUTPUT_FOLDER,
            str(default_path)
        )
        path_str: str = raw if isinstance(raw, str) else str(raw)
        return Path(path_str)

    def get_default_enable_filename_suffix(self) -> bool:
        return bool(self.settings.value(SettingsKeys.DEFAULT_ENABLE_FILENAME_SUFFIX, True, type=bool))

    from typing import cast  # already present in this file

    def get_default_filename_template(self) -> FilenameTemplate:
        # Coerce to str for type checkers, then map to enum
        raw = self.settings.value(SettingsKeys.DEFAULT_FILENAME_TEMPLATE, "CONVERTED")
        name: str = raw if isinstance(raw, str) else str(raw)
        mapping: dict[str, FilenameTemplate] = {
            "CONVERTED": FilenameTemplate.CONVERTED,
            "FORMAT": FilenameTemplate.FORMAT,
            "QUALITY": FilenameTemplate.QUALITY,
            "CUSTOM": FilenameTemplate.CUSTOM,
        }
        return mapping.get(name, FilenameTemplate.CONVERTED)

    def get_default_custom_suffix(self) -> str:
        return self.settings.value(SettingsKeys.DEFAULT_CUSTOM_SUFFIX, "", type=str) or ""

    def get_default_auto_increment(self) -> bool:
        return bool(self.settings.value(SettingsKeys.DEFAULT_AUTO_INCREMENT, True, type=bool))

    # ============================================================
    # PERFORMANCE SETTINGS - Setters
    # ============================================================

    def set_max_concurrent_workers(self, value: int) -> None:
        """
        Set maximum concurrent workers for batch processing.

        Args:
            value: Number of simultaneous conversions (1-16)

        Raises:
            ValueError: If value is outside valid range
        """
        if not isinstance(value, int):
            raise ValueError("max_concurrent_workers must be an integer")

        if not 1 <= value <= 16:
            raise ValueError("max_concurrent_workers must be between 1 and 16")

        self.settings.setValue(SettingsKeys.MAX_CONCURRENT_WORKERS, value)
        self.performance_changed.emit()

    def set_threadpool_max_threads(self, value: int) -> None:
        """
        Set maximum thread pool size.

        Args:
            value: Max threads for background tasks (1-32)

        Raises:
            ValueError: If value is outside valid range
        """
        if not isinstance(value, int):
            raise ValueError("threadpool_max_threads must be an integer")

        if not 1 <= value <= 32:
            raise ValueError("threadpool_max_threads must be between 1 and 32")

        self.settings.setValue(SettingsKeys.THREADPOOL_MAX_THREADS, value)
        self.performance_changed.emit()

    # ============================================================
    # PREVIEW SETTINGS - Setters
    # ============================================================

    def set_preview_cache_size(self, value: int) -> None:
        """
        Set preview cache size.

        Args:
            value: Number of preview images to cache (1-50)

        Raises:
            ValueError: If value is outside valid range
        """
        if not isinstance(value, int):
            raise ValueError("preview_cache_size must be an integer")

        if not 1 <= value <= 50:
            raise ValueError("preview_cache_size must be between 1 and 50")

        self.settings.setValue(SettingsKeys.PREVIEW_CACHE_SIZE, value)
        self.preview_changed.emit()

    def set_hd_cache_size(self, value: int) -> None:
        """
        Set HD cache size.

        Args:
            value: Number of HD images to cache (1-20)

        Raises:
            ValueError: If value is outside valid range
        """
        if not isinstance(value, int):
            raise ValueError("hd_cache_size must be an integer")

        if not 1 <= value <= 20:
            raise ValueError("hd_cache_size must be between 1 and 20")

        self.settings.setValue(SettingsKeys.HD_CACHE_SIZE, value)
        self.preview_changed.emit()

    def set_preview_max_dimension(self, value: int) -> None:
        """
        Set preview maximum dimension.

        Args:
            value: Max width/height for preview in pixels (720-4096)

        Raises:
            ValueError: If value is outside valid range
        """
        if not isinstance(value, int):
            raise ValueError("preview_max_dimension must be an integer")

        if not 720 <= value <= 4096:
            raise ValueError("preview_max_dimension must be between 720 and 4096")

        self.settings.setValue(SettingsKeys.PREVIEW_MAX_DIMENSION, value)
        self.preview_changed.emit()

    def set_out_preview_debounce(self, value: int) -> None:
        """
        Set output preview debounce delay.

        Args:
            value: Delay in milliseconds (100-2000)

        Raises:
            ValueError: If value is outside valid range
        """
        if not isinstance(value, int):
            raise ValueError("out_preview_debounce must be an integer")

        if not 50 <= value <= 2000:
            raise ValueError("out_preview_debounce must be between 50 and 2000")

        self.settings.setValue(SettingsKeys.OUTPUT_PREVIEW_DEBOUNCE, value)
        self.preview_changed.emit()

    def set_output_preview_cache_size(self, value: int) -> None:
        """
        Set output preview cache size.

        Args:
            value: Number of output previews to cache (1-20)

        Raises:
            ValueError: If value is outside valid range
        """
        if not isinstance(value, int):
            raise ValueError("output_preview_cache_size must be an integer")

        if not 1 <= value <= 20:
            raise ValueError("output_preview_cache_size must be between 1 and 20")

        self.settings.setValue(SettingsKeys.OUTPUT_PREVIEW_CACHE_SIZE, value)
        self.preview_changed.emit()

    def request_clear_caches(self) -> None:
        """
        Request all caches to be cleared.

        Emits signal that MainWindow and PreviewWidget can listen to.
        This doesn't store state - it's just a trigger.
        """
        logger.info("Cache clear requested via app settings", source="AppSettings")
        self.clear_caches_requested.emit()

    # ============================================================
    # DEFAULTS SETTINGS - Setters
    # ============================================================

    def set_default_quality(self, value: int) -> None:
        """
        Set default conversion quality.

        Args:
            value: Quality setting (1-100)

        Raises:
            ValueError: If value is outside valid range
        """
        if not isinstance(value, int):
            raise ValueError("default_quality must be an integer")

        if not 1 <= value <= 100:
            raise ValueError("default_quality must be between 1 and 100")

        self.settings.setValue(SettingsKeys.DEFAULT_QUALITY, value)
        self.defaults_changed.emit()

    def set_default_output_format(self, value: ImageFormat) -> None:
        """
        Set default output format.

        Args:
            value: ImageFormat enum value

        Raises:
            ValueError: If value is not an ImageFormat
        """
        if not isinstance(value, ImageFormat):
            raise ValueError("default_output_format must be an ImageFormat enum")

        # Store as string for QSettings compatibility
        self.settings.setValue(SettingsKeys.DEFAULT_OUTPUT_FORMAT, value.name)
        self.defaults_changed.emit()

    def set_default_output_location_mode(self, value: OutputLocationMode) -> None:
        if not isinstance(value, OutputLocationMode):
            raise ValueError("default_output_location_mode must be an OutputLocationMode enum")
        self.settings.setValue(SettingsKeys.DEFAULT_OUTPUT_LOCATION_MODE, value.value)  # "custom"|"same"|"ask"
        self.defaults_changed.emit()

    def set_default_custom_output_folder(self, path: Path) -> None:
        if not isinstance(path, Path):
            raise ValueError("default_custom_output_folder must be a Path")
        self.settings.setValue(SettingsKeys.DEFAULT_CUSTOM_OUTPUT_FOLDER, str(path))
        self.defaults_changed.emit()

    def set_default_enable_filename_suffix(self, enabled: bool) -> None:
        if not isinstance(enabled, bool):
            raise ValueError("enable_filename_suffix must be a bool")
        self.settings.setValue(SettingsKeys.DEFAULT_ENABLE_FILENAME_SUFFIX, enabled)
        self.defaults_changed.emit()

    def set_default_filename_template(self, value: FilenameTemplate) -> None:
        if not isinstance(value, FilenameTemplate):
            raise ValueError("filename_template must be a FilenameTemplate enum")
        self.settings.setValue(SettingsKeys.DEFAULT_FILENAME_TEMPLATE, value.name)
        self.defaults_changed.emit()

    def set_default_custom_suffix(self, text: str) -> None:
        if not isinstance(text, str):
            raise ValueError("custom_suffix must be a string")
        self.settings.setValue(SettingsKeys.DEFAULT_CUSTOM_SUFFIX, text)
        self.defaults_changed.emit()

    def set_default_auto_increment(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise ValueError("auto_increment must be a bool")
        self.settings.setValue(SettingsKeys.DEFAULT_AUTO_INCREMENT, value)
        self.defaults_changed.emit()

    # ============================================================
    # UTILITY METHODS
    # ============================================================

    def reset_to_defaults(self) -> None:
        """
        Clear all settings and revert to defaults.

        Emits all change signals to notify components.
        """
        self.settings.clear()

        # Emit all signals to notify components of reset
        self.performance_changed.emit()
        self.preview_changed.emit()
        self.defaults_changed.emit()

    def get_all_settings(self) -> dict:
        """
        Get all current settings as a dictionary.

        Useful for debugging or displaying current configuration.

        Returns:
            Dictionary with all setting names and values
        """
        return {
            'max_concurrent_workers': self.get_max_concurrent_workers(),
            'threadpool_max_threads': self.get_threadpool_max_threads(),
            'preview_cache_size': self.get_preview_cache_size(),
            'hd_cache_size': self.get_hd_cache_size(),
            'preview_max_dimension': self.get_preview_max_dimension(),
            'out_preview_debounce': self.get_out_preview_debounce(),
            'default_quality': self.get_default_quality(),
            'default_output_format': self.get_default_output_format().name
        }

    def __repr__(self) -> str:
        """String representation showing all current settings."""
        settings = self.get_all_settings()
        settings_str = "\n  ".join(f"{k}: {v}" for k, v in settings.items())
        return f"AppSettingsController(\n  {settings_str}\n)"
