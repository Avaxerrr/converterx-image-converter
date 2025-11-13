from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional


class ImageFormat(Enum):
    """Supported output image formats."""
    WEBP = "WebP"
    AVIF = "AVIF"
    JPEG = "JPEG"
    PNG = "PNG"
    TIFF = "TIFF"
    GIF = "GIF"
    BMP = "BMP"
    ICO = "ICO"


class ResizeMode(Enum):
    """Image resize modes."""
    NONE = "none"
    PERCENTAGE = "percentage"
    FIT_TO_WIDTH = "fit_to_width"
    FIT_TO_HEIGHT = "fit_to_height"
    FIT_TO_DIMENSIONS = "fit_to_dimensions"


class OutputLocationMode(Enum):
    """Output location modes for converted files."""
    CUSTOM_FOLDER = "custom"
    SAME_AS_SOURCE = "same"
    ASK_EVERY_TIME = "ask"


class FilenameTemplate(Enum):
    """Filename suffix templates for output files."""
    CONVERTED = "_converted"
    FORMAT = "_{format}"
    QUALITY = "_Q{quality}"
    CUSTOM = "custom"  # Indicates user will provide custom suffix

    def apply(self, original_stem: str, format_name: str, quality: int, custom_suffix: str = "",
              enable_suffix: bool = True) -> str:
        """
        Apply template to generate new filename stem.

        Args:
            original_stem: Original filename without extension
            format_name: Output format name (e.g., "WebP", "AVIF")
            quality: Quality setting (0-100)
            custom_suffix: Custom suffix string (only used when CUSTOM template)

        Returns:
            New filename stem with suffix applied
        """

        if not enable_suffix:
            return original_stem

        if self == FilenameTemplate.CONVERTED:
            return f"{original_stem}_converted"
        elif self == FilenameTemplate.FORMAT:
            return f"{original_stem}_{format_name}"
        elif self == FilenameTemplate.QUALITY:
            return f"{original_stem}_Q{quality}"
        elif self == FilenameTemplate.CUSTOM:
            # Apply custom suffix if provided, otherwise no suffix
            if custom_suffix:
                # Ensure suffix starts with underscore if not empty
                if not custom_suffix.startswith("_"):
                    custom_suffix = f"_{custom_suffix}"
                return f"{original_stem}{custom_suffix}"
            return original_stem
        return original_stem


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
    enable_filename_suffix: bool = True

    # Resize settings
    resize_mode: ResizeMode = ResizeMode.NONE
    resize_percentage: float = 100.0  # 10-100%

    # Pixel-based resize settings
    target_width_px: Optional[int] = None
    target_height_px: Optional[int] = None
    max_width_px: Optional[int] = None
    max_height_px: Optional[int] = None
    allow_upscaling: bool = False

    # Output field
    output_location_mode: OutputLocationMode = OutputLocationMode.CUSTOM_FOLDER
    custom_output_folder: Path = Path.home() / "Downloads" / "Converted"
    filename_template: FilenameTemplate = FilenameTemplate.CONVERTED
    custom_suffix: str = ""
    custom_base_name: str = ""
    auto_increment: bool = True

    # ==========================================
    # Format-specific settings
    # ==========================================

    # TIFF settings
    tiff_compression: str = "lzw"  # "none", "lzw", "jpeg", "packbits"
    tiff_jpeg_quality: int = 85  # Only used if compression="jpeg"

    # GIF settings
    gif_optimize: bool = True
    gif_dithering: str = "floyd"  # "floyd", "none"

    # ICO settings
    ico_size: int = 256  # Square dimension (16-512)
    ico_force_square: str = "pad"  # "pad", "crop"

    # BMP settings (none needed - uncompressed format)

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

        elif self.output_format == ImageFormat.TIFF:
            kwargs['format'] = 'TIFF'
            # Map compression names to PIL-expected values
            compression_map = {
                'none': None,
                'lzw': 'tiff_lzw',
                'jpeg': 'jpeg',
                'packbits': 'packbits'
            }
            if self.tiff_compression in compression_map:
                compression_value = compression_map[self.tiff_compression]
                if compression_value is not None:  # Only add if not 'none'
                    kwargs['compression'] = compression_value
            # Only add quality if JPEG compression is used
            if self.tiff_compression == 'jpeg':
                kwargs['quality'] = self.tiff_jpeg_quality

        elif self.output_format == ImageFormat.GIF:
            kwargs['format'] = 'GIF'
            kwargs['optimize'] = self.gif_optimize
            # Dithering handled during palette conversion in converter

        elif self.output_format == ImageFormat.ICO:
            kwargs['format'] = 'ICO'
            # Size specification handled in converter (image needs to be square first)
            kwargs['sizes'] = [(self.ico_size, self.ico_size)]

        elif self.output_format == ImageFormat.BMP:
            kwargs['format'] = 'BMP'
            # No options for BMP (uncompressed)

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
            ImageFormat.PNG: '.png',
            ImageFormat.TIFF: '.tiff',
            ImageFormat.GIF: '.gif',
            ImageFormat.BMP: '.bmp',
            ImageFormat.ICO: '.ico'
        }
        return extensions[self.output_format]
