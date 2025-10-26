from pathlib import Path
from typing import List, Optional
from PIL import Image
from models.image_file import ImageFile

# Supported image formats
SUPPORTED_FORMATS = {
    '.jpg', '.jpeg', '.png', '.webp', '.bmp',
    '.tiff', '.tif', '.gif', '.avif'
}


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

    for path in file_paths:
        if not is_supported_image(path):
            print(f"Skipping unsupported file: {path}")
            continue

        image_file = load_image_file(path)
        if image_file:
            image_files.append(image_file)

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
