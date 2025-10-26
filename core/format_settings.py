from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional


class ImageFormat(Enum):
    """Supported output image formats."""
    WEBP = "WebP"
    AVIF = "AVIF"
    JPEG = "JPEG"
    PNG = "PNG"


@dataclass
class ConversionSettings:
    """Settings for image conversion."""
    output_format: ImageFormat
    quality: int = 85
    lossless: bool = False
    keep_metadata: bool = True
    png_compress_level: int = 6
    target_size_kb: Optional[float] = None  # NEW: Target file size
    webp_method: int = 6  # NEW: WebP compression effort
    avif_speed: int = 4  # NEW: AVIF encoding speed

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
