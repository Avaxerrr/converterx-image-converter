"""
Filename Utilities

Handles output path generation, template application, and collision detection.
"""

from pathlib import Path
from typing import Tuple
from models.image_file import ImageFile
from core.format_settings import ConversionSettings, FilenameTemplate, OutputLocationMode


def generate_output_path(
    source_file: ImageFile,
    settings: ConversionSettings
) -> Path:
    """
    Generate complete output path for a converted file.

    Handles:
    - Output location mode (custom folder, same as source, ask)
    - Filename template application
    - Collision detection with auto-increment

    Args:
        source_file: Source ImageFile object
        settings: Conversion settings with output configuration

    Returns:
        Complete Path object for output file

    Note:
        For ASK_EVERY_TIME mode, settings.custom_output_folder should
        be pre-set by the caller (MainWindow) before calling this function.
    """
    # Determine output folder based on mode
    if settings.output_location_mode == OutputLocationMode.CUSTOM_FOLDER:
        output_folder = settings.custom_output_folder
    elif settings.output_location_mode == OutputLocationMode.SAME_AS_SOURCE:
        # FIXED: Use source_file.path instead of source_file.filepath
        output_folder = source_file.path.parent
    else:  # ASK_EVERY_TIME - caller must pre-set custom_output_folder
        output_folder = settings.custom_output_folder

    # Ensure output folder exists
    output_folder.mkdir(parents=True, exist_ok=True)

    # Apply template to filename
    # FIXED: Use source_file.path.stem instead of source_file.filepath.stem
    new_stem = apply_suffix(
        source_file.path.stem,
        settings.filename_template,
        settings
    )

    # Get output extension
    new_extension = settings.file_extension  # Uses existing property from ConversionSettings

    # Build initial output path
    output_path = output_folder / f"{new_stem}{new_extension}"

    # Handle collision if auto-increment enabled
    if settings.auto_increment and output_path.exists():
        output_path = get_next_available_path(output_path)

    return output_path


def apply_suffix(
    original_stem: str,
    template: FilenameTemplate,
    settings: ConversionSettings
) -> str:
    """
    Apply filename template to generate new filename stem.

    Args:
        original_stem: Original filename without extension
        template: Template to apply
        settings: Conversion settings (for format and quality)

    Returns:
        New filename stem with suffix applied
    """
    format_name = settings.output_format.name  # "WEBP", "AVIF", etc.
    quality = settings.quality

    return template.apply(original_stem, format_name, quality)


def get_next_available_path(base_path: Path) -> Path:
    """
    Find next available filename by appending _1, _2, _3, etc.

    Args:
        base_path: Original desired path that already exists

    Returns:
        Available path with incremented number

    Example:
        photo_converted.webp exists
        → photo_converted_1.webp exists
        → photo_converted_2.webp (returned)
    """
    stem = base_path.stem
    extension = base_path.suffix
    folder = base_path.parent

    counter = 1
    while True:
        new_path = folder / f"{stem}_{counter}{extension}"
        if not new_path.exists():
            return new_path
        counter += 1

        # Safety: prevent infinite loop (unlikely but possible)
        if counter > 9999:
            # Fallback to timestamp-based naming
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return folder / f"{stem}_{timestamp}{extension}"
