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
from utils.logger import logger


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
    def _apply_resize(img: Image.Image, settings: ConversionSettings) -> Image.Image:
        """
        Apply resize based on settings for output preview.
        """

        if settings.resize_mode == ResizeMode.NONE:
            logger.debug("No resize applied (ResizeMode.NONE)", source="OutputPreviewGenerator")
            return img

        original_width, original_height = img.size

        if settings.resize_mode == ResizeMode.PERCENTAGE:
            scale = settings.resize_percentage / 100.0
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)

            if (new_width, new_height) != (original_width, original_height):
                logger.debug(
                    f"Percentage: {original_width}×{original_height} → {new_width}×{new_height}",
                    source="OutputPreviewGenerator"
                )
                return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            return img

        elif settings.resize_mode == ResizeMode.FIT_TO_WIDTH:
            if not settings.target_width_px:
                logger.debug("Fit to width: No target specified", source="OutputPreviewGenerator")
                return img

            target_w = settings.target_width_px
            aspect_ratio = original_width / original_height
            new_w = target_w
            new_h = int(target_w / aspect_ratio)

            if not settings.allow_upscaling and new_w > original_width:
                logger.debug("Fit to width: Upscaling disabled", source="OutputPreviewGenerator")
                return img

            if (new_w, new_h) != (original_width, original_height):
                logger.debug(
                    f"Fit to width: {original_width}×{original_height} → {new_w}×{new_h}",
                    source="OutputPreviewGenerator"
                )
                return img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            return img

        elif settings.resize_mode == ResizeMode.FIT_TO_HEIGHT:
            if not settings.target_height_px:
                logger.debug("Fit to height: No target specified", source="OutputPreviewGenerator")
                return img

            target_h = settings.target_height_px
            aspect_ratio = original_width / original_height
            new_h = target_h
            new_w = int(target_h * aspect_ratio)

            if not settings.allow_upscaling and new_h > original_height:
                logger.debug("Fit to height: Upscaling disabled", source="OutputPreviewGenerator")
                return img

            if (new_w, new_h) != (original_width, original_height):
                logger.debug(
                    f"Fit to height: {original_width}×{original_height} → {new_w}×{new_h}",
                    source="OutputPreviewGenerator"
                )
                return img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            return img

        elif settings.resize_mode == ResizeMode.FIT_TO_DIMENSIONS:
            max_w = settings.max_width_px
            max_h = settings.max_height_px

            if not max_w and not max_h:
                logger.debug("Fit to dimensions: No dimensions specified", source="OutputPreviewGenerator")
                return img

            # Calculate fit dimensions
            aspect_ratio = original_width / original_height

            if max_w and not max_h:
                new_w = max_w
                new_h = int(max_w / aspect_ratio)
            elif max_h and not max_w:
                new_h = max_h
                new_w = int(max_h * aspect_ratio)
            else:
                if original_width / max_w > original_height / max_h:
                    new_w = max_w
                    new_h = int(max_w / aspect_ratio)
                else:
                    new_h = max_h
                    new_w = int(max_h * aspect_ratio)

            if not settings.allow_upscaling:
                new_w = min(new_w, original_width)
                new_h = min(new_h, original_height)

            if (new_w, new_h) != (original_width, original_height):
                logger.debug(
                    f"Fit to dimensions: {original_width}×{original_height} → {new_w}×{new_h}",
                    source="OutputPreviewGenerator"
                )
                return img.resize((new_w, new_h), Image.Resampling.LANCZOS)
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

        # ==========================================
        # GIF format preparation
        # ==========================================
        elif settings.output_format == ImageFormat.GIF:
            # GIF requires palette mode (256 colors max)
            if img.mode != 'P':
                logger.debug(
                    f"Converting {img.mode} → P (palette) for GIF format",
                    source="OutputPreviewGenerator"
                )

                # Convert to palette mode with adaptive palette
                # Apply dithering based on settings
                if settings.gif_dithering == "floyd":
                    img = img.convert('P', palette=Image.ADAPTIVE, colors=256)
                else:  # "none"
                    img = img.convert('P', palette=Image.ADAPTIVE, colors=256, dither=Image.NONE)

                logger.info(
                    f"Converted to palette mode for GIF (256 colors, dithering={settings.gif_dithering})",
                    source="OutputPreviewGenerator"
                )

                return img

        # ==========================================
        # ICO format preparation
        # ==========================================
        elif settings.output_format == ImageFormat.ICO:
            # ICO must be square - apply force square method
            if img.width != img.height:
                target_size = settings.ico_size

                if settings.ico_force_square == "pad":
                    # Pad with transparency to make square
                    logger.debug(
                        f"Padding {img.width}×{img.height} → {target_size}×{target_size} for ICO",
                        source="OutputPreviewGenerator"
                    )

                    # Ensure RGBA mode for transparency
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')

                    # Calculate padding
                    max_dim = max(img.width, img.height)
                    new_img = Image.new('RGBA', (max_dim, max_dim), (0, 0, 0, 0))

                    # Center paste
                    paste_x = (max_dim - img.width) // 2
                    paste_y = (max_dim - img.height) // 2
                    new_img.paste(img, (paste_x, paste_y))

                    # Resize to target size
                    img = new_img.resize((target_size, target_size), Image.Resampling.LANCZOS)

                    logger.info(
                        f"ICO padded to square: {target_size}×{target_size}",
                        source="OutputPreviewGenerator"
                    )

                elif settings.ico_force_square == "crop":
                    # Crop to center square
                    logger.debug(
                        f"Cropping {img.width}×{img.height} → {target_size}×{target_size} for ICO",
                        source="OutputPreviewGenerator"
                    )

                    # Find the smallest dimension
                    min_dim = min(img.width, img.height)

                    # Calculate center crop
                    left = (img.width - min_dim) // 2
                    top = (img.height - min_dim) // 2
                    right = left + min_dim
                    bottom = top + min_dim

                    img = img.crop((left, top, right, bottom))

                    # Resize to target size
                    img = img.resize((target_size, target_size), Image.Resampling.LANCZOS)

                    logger.info(
                        f"ICO cropped to square: {target_size}×{target_size}",
                        source="OutputPreviewGenerator"
                    )

                return img
            else:
                # Already square, just resize to target size
                if img.width != settings.ico_size:
                    logger.debug(
                        f"Resizing square ICO: {img.width}×{img.height} → {settings.ico_size}×{settings.ico_size}",
                        source="OutputPreviewGenerator"
                    )
                    img = img.resize((settings.ico_size, settings.ico_size), Image.Resampling.LANCZOS)

                # Ensure RGBA mode for ICO
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')

                return img

        # ==========================================
        # TIFF format preparation
        # ==========================================
        elif settings.output_format == ImageFormat.TIFF:
            # Convert palette/indexed images to RGB for JPEG compression
            if settings.tiff_compression == 'jpeg' and img.mode in ('P', 'PA', 'L', 'LA'):
                # JPEG compression in TIFF only supports RGB/RGBA, not palette
                if img.mode in ('PA', 'LA'):
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')
            return img

        # ==========================================
        # BMP format preparation
        # ==========================================
        elif settings.output_format == ImageFormat.BMP:
            # BMP supports RGB/RGBA, but RGBA is better
            # Convert palette mode if present
            if img.mode == 'P':
                logger.debug(
                    f"Converting P (palette) → RGBA for BMP format",
                    source="OutputPreviewGenerator"
                )
                img = img.convert('RGBA')
            # Pass through otherwise

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
        - WebP subsampling (affects visual quality)
        - AVIF range (affects contrast/levels)
        - TIFF compression (affects visual quality for JPEG compression)
        - GIF optimization (affects visual quality)

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

            # Apply subsampling (affects visual quality)
            if settings.webp_subsampling:
                # PIL expects string format "4:2:0" or "4:4:4"
                subsampling_str = f"{settings.webp_subsampling[0]}:{settings.webp_subsampling[1]}:0"
                kwargs['subsampling'] = subsampling_str
                logger.debug(
                    f"WebP subsampling applied: {subsampling_str}",
                    source="OutputPreviewGenerator"
                )

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

        # ==========================================
        # TIFF format kwargs
        # ==========================================
        elif settings.output_format == ImageFormat.TIFF:
            kwargs['format'] = 'TIFF'
            kwargs['compression'] = settings.tiff_compression

            # Only add quality if JPEG compression is used
            if settings.tiff_compression == 'jpeg':
                kwargs['quality'] = settings.tiff_jpeg_quality
                logger.debug(
                    f"TIFF kwargs: compression=jpeg, quality={settings.tiff_jpeg_quality}",
                    source="OutputPreviewGenerator"
                )
            else:
                logger.debug(
                    f"TIFF kwargs: compression={settings.tiff_compression}",
                    source="OutputPreviewGenerator"
                )

        # ==========================================
        # GIF format kwargs
        # ==========================================
        elif settings.output_format == ImageFormat.GIF:
            kwargs['format'] = 'GIF'
            kwargs['optimize'] = settings.gif_optimize

            # Save transparency if present
            kwargs['transparency'] = 0  # Preserve transparent color
            kwargs['disposal'] = 2  # Clear frame after rendering

            logger.debug(
                f"GIF kwargs: optimize={settings.gif_optimize}",
                source="OutputPreviewGenerator"
            )

        # ==========================================
        # ICO format kwargs
        # ==========================================
        elif settings.output_format == ImageFormat.ICO:
            kwargs['format'] = 'ICO'
            # Note: sizes parameter is handled during format preparation (square conversion)
            # PIL automatically uses the image size for single-size ICO
            kwargs['sizes'] = [(settings.ico_size, settings.ico_size)]

            logger.debug(
                f"ICO kwargs: size={settings.ico_size}×{settings.ico_size}",
                source="OutputPreviewGenerator"
            )

        # ==========================================
        # BMP format kwargs
        # ==========================================
        elif settings.output_format == ImageFormat.BMP:
            kwargs['format'] = 'BMP'
            # BMP has no compression options
            logger.debug(
                "BMP kwargs: no options (uncompressed)",
                source="OutputPreviewGenerator"
            )

        return kwargs
