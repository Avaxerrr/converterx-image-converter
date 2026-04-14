from __future__ import annotations

import io
import math
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageOps
from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer


SVG_SUFFIX = ".svg"
SVG_FALLBACK_SIZE = (1024, 1024)


def is_svg_file(file_path: Path) -> bool:
    """Return True when the path points to an SVG file."""
    return file_path.suffix.lower() == SVG_SUFFIX


def get_image_info(file_path: Path) -> Tuple[Optional[int], Optional[int], str]:
    """
    Load image dimensions and format name for raster and SVG files.

    Raises:
        ValueError: If the file cannot be decoded.
    """
    if is_svg_file(file_path):
        width, height = get_svg_size(file_path)
        return width, height, "SVG"

    with Image.open(file_path) as img:
        return img.width, img.height, img.format or file_path.suffix.upper().replace(".", "")


def get_svg_size(file_path: Path) -> Tuple[int, int]:
    """Get the intrinsic SVG size or a sensible fallback."""
    renderer = _create_svg_renderer(file_path)
    return _resolve_svg_size(renderer)


def load_pil_image(
        file_path: Path,
        *,
        target_size: Optional[Tuple[int, int]] = None,
        max_dimension: Optional[int] = None
) -> Image.Image:
    """
    Load an image file into a PIL Image.

    Raster images are opened through Pillow. SVG files are rendered through QtSvg.
    """
    if is_svg_file(file_path):
        return _load_svg_as_pil_image(
            file_path,
            target_size=target_size,
            max_dimension=max_dimension
        )

    with Image.open(file_path) as img:
        img = ImageOps.exif_transpose(img)

        if target_size:
            width, height = _normalize_size(target_size)
            img = img.resize((width, height), Image.Resampling.LANCZOS)
        elif max_dimension and max(img.size) > max_dimension:
            img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

        return img.copy()


def _load_svg_as_pil_image(
        file_path: Path,
        *,
        target_size: Optional[Tuple[int, int]] = None,
        max_dimension: Optional[int] = None
) -> Image.Image:
    """Render an SVG file into a PIL RGBA image."""
    renderer = _create_svg_renderer(file_path)
    render_width, render_height = _determine_render_size(
        renderer,
        target_size=target_size,
        max_dimension=max_dimension
    )

    qimage = QImage(render_width, render_height, QImage.Format.Format_ARGB32)
    qimage.fill(0)

    painter = QPainter(qimage)
    renderer.render(painter)
    painter.end()

    buffer = QBuffer()
    if not buffer.open(QIODevice.OpenModeFlag.ReadWrite):
        raise ValueError(f"Failed to buffer rendered SVG: {file_path.name}")

    if not qimage.save(buffer, "PNG"):
        raise ValueError(f"Failed to encode rendered SVG: {file_path.name}")

    pil_image = Image.open(io.BytesIO(bytes(buffer.data())))
    return pil_image.copy()


def _create_svg_renderer(file_path: Path) -> QSvgRenderer:
    """Create and validate a Qt SVG renderer."""
    renderer = QSvgRenderer(str(file_path))
    if not renderer.isValid():
        raise ValueError(f"Invalid SVG file: {file_path.name}")
    return renderer


def _determine_render_size(
        renderer: QSvgRenderer,
        *,
        target_size: Optional[Tuple[int, int]] = None,
        max_dimension: Optional[int] = None
) -> Tuple[int, int]:
    """Choose the final pixel size to render the SVG at."""
    if target_size:
        return _normalize_size(target_size)

    intrinsic_width, intrinsic_height = _resolve_svg_size(renderer)

    if max_dimension and max(intrinsic_width, intrinsic_height) > max_dimension:
        scale = max_dimension / max(intrinsic_width, intrinsic_height)
        return (
            max(1, int(round(intrinsic_width * scale))),
            max(1, int(round(intrinsic_height * scale))),
        )

    return intrinsic_width, intrinsic_height


def _resolve_svg_size(renderer: QSvgRenderer) -> Tuple[int, int]:
    """Resolve an SVG size from its default size, viewBox, or fallback."""
    default_size = renderer.defaultSize()
    if default_size.isValid() and default_size.width() > 0 and default_size.height() > 0:
        return default_size.width(), default_size.height()

    view_box = renderer.viewBoxF()
    if view_box.isValid() and view_box.width() > 0 and view_box.height() > 0:
        return (
            max(1, int(math.ceil(view_box.width()))),
            max(1, int(math.ceil(view_box.height()))),
        )

    return SVG_FALLBACK_SIZE


def _normalize_size(size: Tuple[int, int]) -> Tuple[int, int]:
    """Normalize a size tuple to positive integers."""
    width = max(1, int(round(size[0])))
    height = max(1, int(round(size[1])))
    return width, height
