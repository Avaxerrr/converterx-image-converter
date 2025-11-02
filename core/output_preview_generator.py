"""
Output Preview Generator

Generates in-memory preview images with conversion settings applied.
This is a pure PIL-based module with NO file I/O operations.

Settings Applied:
- Quality slider
- Lossless toggle
- Scale by % (resize)
- PNG compression level

Settings Skipped (for preview purposes):
- Target file size (iterative compression)
- WebP/AVIF advanced options (subsampling, method, speed, range)
"""

from pathlib import Path
from PIL import Image, ImageOps
from typing import Optional
from core.format_settings import ConversionSettings, ResizeMode, ImageFormat
from utils.logger import logger, LogLevel


class OutputPreviewGenerator:
    """
    Generate an in-memory preview image based on conversion settings.

    This is a PURE computation layer - no file I/O, no side effects.
    Returns a PIL Image object, NOT a file.
    """

    @staticmethod
    def generate_preview(
            image_path: Path,
            settings: ConversionSettings
    ) -> Optional[Image.Image]:
        """
        Generate a preview of what the output will look like.

        Args:
            image_path: Path to the original image file
            settings: Conversion settings to apply

        Returns:
            PIL Image with settings applied, or None if generation fails

        Note:
            - Does NOT save to disk
            - Does NOT apply target file size iterative compression
            - Does NOT apply max dimensions (uses scale % only)
            - Does NOT apply advanced WebP/AVIF options
        """
        logger.debug(
            f"Starting output preview generation for {image_path.name}",
            source="OutputPreviewGenerator"
        )

        try:
            # Load image with EXIF orientation fix
            with Image.open(image_path) as img:
                original_size = img.size
                logger.debug(
                    f"Loaded image: {original_size[0]}×{original_size[1]} mode={img.mode}",
                    source="OutputPreviewGenerator"
                )

                # Fix EXIF orientation (rotate/flip based on EXIF data)
                img = ImageOps.exif_transpose(img)
                if img.size != original_size:
                    logger.debug(
                        f"EXIF orientation applied: {img.size[0]}×{img.size[1]}",
                        source="OutputPreviewGenerator"
                    )

                # Apply resize if needed (ONLY scale %, skip max dimensions)
                img = OutputPreviewGenerator._apply_resize(img, settings)

                # Apply format-specific operations (RGBA → RGB conversion, etc.)
                img = OutputPreviewGenerator._prepare_for_format(img, settings)

                logger.info(
                    f"Output preview generated: {img.size[0]}×{img.size[1]} "
                    f"format={settings.output_format.value} quality={settings.quality}",
                    source="OutputPreviewGenerator"
                )

                # Return a copy (PIL Image object in memory)
                return img.copy()

        except FileNotFoundError:
            logger.error(
                f"Image file not found: {image_path}",
                source="OutputPreviewGenerator"
            )
            return None
        except Exception as e:
            logger.error(
                f"Preview generation failed for {image_path.name}: {str(e)}",
                source="OutputPreviewGenerator"
            )
            return None

    @staticmethod
    def _apply_resize(
            img: Image.Image,
            settings: ConversionSettings
    ) -> Image.Image:
        """
        Apply resize based on settings (ONLY scale percentage).

        Note: Max dimensions are skipped for output preview.
        """
        if settings.resize_mode == ResizeMode.NONE:
            logger.debug("No resize applied (ResizeMode.NONE)", source="OutputPreviewGenerator")
            return img

        original_width, original_height = img.size

        # ONLY handle percentage scaling (skip max dimensions for preview)
        if settings.resize_mode == ResizeMode.PERCENTAGE:
            scale = settings.resize_percentage / 100.0
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)

            logger.debug(
                f"Applying scale {settings.resize_percentage}%: "
                f"{original_width}×{original_height} → {new_width}×{new_height}",
                source="OutputPreviewGenerator"
            )

            # Use high-quality Lanczos resampling
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            logger.info(
                f"Resized to {new_width}×{new_height} ({scale * 100:.1f}%)",
                source="OutputPreviewGenerator"
            )

            return resized

        elif settings.resize_mode == ResizeMode.MAXDIMENSIONS:
            # Skip max dimensions for output preview (different from scale %)
            logger.debug(
                "Skipping max dimensions for output preview (not applied)",
                source="OutputPreviewGenerator"
            )
            return img

        return img

    @staticmethod
    def _prepare_for_format(
            img: Image.Image,
            settings: ConversionSettings
    ) -> Image.Image:
        """
        Prepare image for target format (convert color modes).

        This doesn't actually apply quality/compression (that happens during save),
        but it handles necessary color space conversions.
        """
        original_mode = img.mode

        # JPEG: Convert RGBA/LA/P to RGB (JPEG doesn't support transparency)
        if settings.output_format == ImageFormat.JPEG:
            if img.mode in ('RGBA', 'LA', 'P'):
                logger.debug(
                    f"Converting {img.mode} → RGB for JPEG format",
                    source="OutputPreviewGenerator"
                )

                # Create white background
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))

                # Convert palette to RGBA first if needed
                if img.mode == 'P':
                    img = img.convert('RGBA')

                # Paste with alpha mask
                if img.mode in ('RGBA', 'LA'):
                    rgb_img.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                else:
                    rgb_img.paste(img)

                logger.info(
                    f"Converted to RGB for JPEG (white background applied)",
                    source="OutputPreviewGenerator"
                )

                return rgb_img

        # WebP/AVIF: Convert RGBA to RGB if no transparency
        # (This optimization is optional but matches converter.py behavior)
        elif settings.output_format in (ImageFormat.WEBP, ImageFormat.AVIF):
            if img.mode == 'RGBA':
                # Check if image has actual transparency
                if img.getextrema()[3][0] == 255:  # Alpha channel is all 255 (opaque)
                    logger.debug(
                        "Converting RGBA → RGB (no transparency detected)",
                        source="OutputPreviewGenerator"
                    )
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    rgb_img.paste(img)
                    return rgb_img

        if img.mode != original_mode:
            logger.debug(
                f"Format preparation: {original_mode} → {img.mode}",
                source="OutputPreviewGenerator"
            )
        else:
            logger.debug(
                f"No format conversion needed (mode={img.mode})",
                source="OutputPreviewGenerator"
            )

        return img

    @staticmethod
    def get_preview_kwargs(settings: ConversionSettings) -> dict:
        """
        Get preview-relevant PIL save kwargs including advanced options.

        Applied Settings:
        - Quality, lossless, PNG compression (already applied)
        - WebP subsampling (NEW - affects visual quality)
        - AVIF range (NEW - affects contrast/levels)

        Excluded Settings:
        - WebP method (no visual difference, only compression efficiency)
        - AVIF speed (no visual difference, only encoding speed)
        - Target file size (iterative, too slow for preview)
        - Max dimensions (different from scale %)

        Returns:
            Dictionary of kwargs for PIL Image.save()
        """
        kwargs = {}

        if settings.output_format == ImageFormat.JPEG:
            kwargs['format'] = 'JPEG'
            kwargs['quality'] = settings.quality
            kwargs['optimize'] = True
            logger.debug(
                f"JPEG kwargs: quality={settings.quality}",
                source="OutputPreviewGenerator"
            )

        elif settings.output_format == ImageFormat.PNG:
            kwargs['format'] = 'PNG'
            kwargs['compress_level'] = settings.png_compress_level
            kwargs['optimize'] = True
            logger.debug(
                f"PNG kwargs: compress_level={settings.png_compress_level}",
                source="OutputPreviewGenerator"
            )

        elif settings.output_format == ImageFormat.WEBP:
            kwargs['format'] = 'WEBP'
            if settings.lossless:
                kwargs['lossless'] = True
                logger.debug("WebP kwargs: lossless=True", source="OutputPreviewGenerator")
            else:
                kwargs['quality'] = settings.quality
                logger.debug(
                    f"WebP kwargs: quality={settings.quality}",
                    source="OutputPreviewGenerator"
                )

            # pply subsampling (affects visual quality)
            if settings.webp_subsampling:
                # PIL expects string format "4:2:0" or "4:4:4"
                subsampling_str = f"{settings.webp_subsampling[0]}:{settings.webp_subsampling[1]}:0"
                kwargs['subsampling'] = subsampling_str
                logger.debug(
                    f"WebP subsampling applied: {subsampling_str}",
                    source="OutputPreviewGenerator"
                )

            # Skip method (no visual impact, only compression speed)

        elif settings.output_format == ImageFormat.AVIF:
            kwargs['format'] = 'AVIF'
            if settings.lossless:
                kwargs['quality'] = 100
                logger.debug("AVIF kwargs: lossless (quality=100)", source="OutputPreviewGenerator")
            else:
                kwargs['quality'] = settings.quality
                logger.debug(
                    f"AVIF kwargs: quality={settings.quality}",
                    source="OutputPreviewGenerator"
                )

            # Apply range (affects contrast/black levels)
            if settings.avif_range:
                kwargs['range'] = settings.avif_range  # "full" or "limited"
                logger.debug(
                    f"AVIF range applied: {settings.avif_range}",
                    source="OutputPreviewGenerator"
                )

        return kwargs
