from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional


class ImageFormat(Enum):
    """Supported output image formats."""
    WEBP = "WebP"
    AVIF = "AVIF"
    JPEG = "JPEG"
    PNG = "PNG"


class ResizeMode(Enum):
    """Image resize modes."""
    NONE = "none"
    PERCENTAGE = "percentage"


@dataclass
class ConversionSettings:
    """Settings for image conversion."""
    output_format: ImageFormat
    quality: int = 85
    lossless: bool = False
    keep_metadata: bool = True
    png_compress_level: int = 6
    target_size_kb: Optional[float] = None
    webp_subsampling: tuple = (2, 2)
    webp_method: int = 6
    avif_speed: int = 4
    avif_range: str = "full"

    # NEW: Resize settings
    resize_mode: ResizeMode = ResizeMode.NONE
    resize_percentage: float = 100.0  # 10-100%

    def to_pillow_kwargs(self, quality_override: Optional[int] = None) -> Dict[str, Any]:
        """
        Convert settings to Pillow save() kwargs.

        Args:
            quality_override: Override quality for target size iterations
        """
        kwargs = {}
        actual_quality = quality_override if quality_override is not None else self.quality

        if self.output_format == ImageFormat.WEBP:
            kwargs['format'] = 'WEBP'
            if self.lossless:
                kwargs['lossless'] = True
            else:
                kwargs['quality'] = actual_quality
            kwargs['method'] = self.webp_method

        elif self.output_format == ImageFormat.AVIF:
            kwargs['format'] = 'AVIF'
            if self.lossless:
                kwargs['quality'] = 100
            else:
                kwargs['quality'] = actual_quality
            kwargs['speed'] = self.avif_speed
            kwargs['range'] = self.avif_range

        elif self.output_format == ImageFormat.JPEG:
            kwargs['format'] = 'JPEG'
            kwargs['quality'] = actual_quality
            kwargs['optimize'] = True

        elif self.output_format == ImageFormat.PNG:
            kwargs['format'] = 'PNG'
            kwargs['optimize'] = True
            kwargs['compress_level'] = self.png_compress_level

        if not self.keep_metadata:
            kwargs['exif'] = b''

        return kwargs

    @property
    def file_extension(self) -> str:
        """Get file extension for the format."""
        extensions = {
            ImageFormat.WEBP: '.webp',
            ImageFormat.AVIF: '.avif',
            ImageFormat.JPEG: '.jpg',
            ImageFormat.PNG: '.png'
        }
        return extensions[self.output_format]
