"""
Filename Utilities

Handles output path generation, template application, and collision detection.
"""

from pathlib import Path
from typing import Tuple, Optional
from models.image_file import ImageFile
from core.format_settings import ConversionSettings, FilenameTemplate, OutputLocationMode


def generate_output_path(
    source_file: ImageFile,
    settings: ConversionSettings,
    batch_index: Optional[int] = None  # NEW: Sequential index for batch conversions
) -> Path:
    """
    Generate complete output path for a converted file.

    Handles:
    - Output location mode (custom folder, same as source, ask)
    - Base filename renaming (custom base name or original)
    - Sequential batch numbering (when batch_index is provided)
    - Filename template application
    - Collision detection with auto-increment

    Args:
        source_file: Source ImageFile object
        settings: Conversion settings with output configuration
        batch_index: Optional sequential number for batch conversions (1-based)

    Returns:
        Complete Path object for output file

    Note:
        For ASK_EVERY_TIME mode, settings.custom_output_folder should
        be pre-set by the caller (MainWindow) before calling this function.

        When batch_index is provided with custom_base_name, the file will be
        numbered sequentially (e.g., base_1, base_2, base_3...).
    """
    # Determine output folder based on mode
    if settings.output_location_mode == OutputLocationMode.CUSTOM_FOLDER:
        output_folder = settings.custom_output_folder
    elif settings.output_location_mode == OutputLocationMode.SAME_AS_SOURCE:
        output_folder = source_file.path.parent
    else:  # ASK_EVERY_TIME - caller must pre-set custom_output_folder
        output_folder = settings.custom_output_folder

    # Ensure output folder exists
    output_folder.mkdir(parents=True, exist_ok=True)

    # Determine base filename
    if batch_index is not None and settings.custom_base_name.strip():
        # BATCH MODE with custom base name: Always use sequential numbering
        base_stem = f"{settings.custom_base_name.strip()}_{batch_index}"
    elif settings.custom_base_name.strip():
        # SINGLE FILE with custom base name
        base_stem = settings.custom_base_name.strip()
    else:
        # Use original filename (no custom base name)
        base_stem = source_file.path.stem

    # Apply suffix template to filename
    new_stem = apply_suffix(
        base_stem,
        settings.filename_template,
        settings
    )

    # Get output extension
    new_extension = settings.file_extension

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
        original_stem: Original filename without extension (or custom base name)
        template: Template to apply
        settings: Conversion settings (for format and quality)

    Returns:
        New filename stem with suffix applied
    """
    format_name = settings.output_format.name  # "WEBP", "AVIF", etc.
    quality = settings.quality

    # Pass custom_suffix and enable_filename_suffix flag to apply method
    return template.apply(
        original_stem,
        format_name,
        quality,
        settings.custom_suffix,
        settings.enable_filename_suffix
    )


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
