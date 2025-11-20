from pathlib import Path
from typing import List, Optional
from PIL import Image
from models.image_file import ImageFile

from utils.logger import logger


def _get_pillow_supported_extensions() -> List[str]:
    """
    Dynamically get list of image extensions supported by current Pillow installation.

    Returns:
        List of lowercase file extensions (e.g., ['.jpg', '.png', '.heic'])
    """
    supported = set()

    # Get all registered extensions from Pillow
    for ext, format_name in Image.registered_extensions().items():
        # Only include formats that Pillow can READ (has a decoder)
        if format_name in Image.OPEN:
            supported.add(ext.lower())

    # Manually add common extension aliases that might not be in Pillow's registry
    extension_aliases = {
        '.jpeg': '.jpg',
        '.tif': '.tiff',
        '.heif': '.heic',  # HEIF is the container, HEIC is Apple's variant
    }

    # Add aliases if their base format is supported
    for alias, base in extension_aliases.items():
        if base in supported:
            supported.add(alias)

    return sorted(list(supported))


# Dynamically populate supported formats based on what Pillow can actually handle
SUPPORTED_FORMATS = _get_pillow_supported_extensions()


def is_supported_image(file_path: Path) -> bool:
    """Check if file is a supported image format."""
    return file_path.suffix.lower() in SUPPORTED_FORMATS


def load_image_file(file_path: Path) -> Optional[ImageFile]:
    """
    Load an image file and extract metadata.

    Args:
        file_path: Path to the image file

    Returns:
        ImageFile object or None if loading fails
    """
    try:
        # Get file size
        size_bytes = file_path.stat().st_size

        # Try to open with PIL to get dimensions
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                format_name = img.format
        except Exception as e:
            # LOG: Failed to read image metadata (corrupt file, unsupported format, etc.)
            logger.warning(f"Could not read metadata for {file_path.name}: {str(e)}", source="FileLoader")
            print(f"Warning: Could not read image metadata for {file_path}: {e}")
            width, height = None, None
            format_name = file_path.suffix.upper().replace('.', '')

        return ImageFile(
            path=file_path,
            size_bytes=size_bytes,
            width=width,
            height=height,
            format=format_name
        )

    except Exception as e:

        # LOG: Complete failure to load image file (file not found, permissions, etc.)
        logger.error(f"Failed to load {file_path.name}: {str(e)}", source="FileLoader")
        print(f"Error loading file {file_path}: {e}")

        return None


def load_image_files(file_paths: List[Path]) -> List[ImageFile]:
    """
    Load multiple image files.

    Args:
        file_paths: List of file paths

    Returns:
        List of successfully loaded ImageFile objects
    """
    image_files = []

    # LOG: Track how many files user is attempting to load
    logger.info(f"Loading {len(file_paths)} file(s)...", source="FileLoader")

    for path in file_paths:
        if not is_supported_image(path):
            print(f"Skipping unsupported file: {path}")
            continue

        image_file = load_image_file(path)
        if image_file:
            image_files.append(image_file)

    # LOG: Summary of successful loads (helps identify if some files failed silently)
    if image_files:
        total_size_mb = sum(f.size_mb for f in image_files)
        logger.info(
            f"Successfully loaded {len(image_files)}/{len(file_paths)} images ({total_size_mb:.1f} MB total)",
            source="FileLoader"
        )
    else:
        logger.warning("No images were successfully loaded", source="FileLoader")

    return image_files


def validate_image_path(path_str: str) -> Optional[Path]:
    """
    Validate and convert string path to Path object.

    Args:
        path_str: String path to validate

    Returns:
        Path object if valid, None otherwise
    """
    try:
        path = Path(path_str)
        if path.exists() and path.is_file():
            return path
    except Exception:
        pass

    return None
