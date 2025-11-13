from pathlib import Path
from PIL import Image, ImageOps
from typing import Optional, Tuple
from core.format_settings import ConversionSettings, ResizeMode, ImageFormat
from utils.logger import logger, LogLevel
import time
import io
import math


class ImageConverter:
    """Handles image conversion operations."""

    @staticmethod
    def convert_image(
            input_path: Path,
            output_path: Path,
            settings: ConversionSettings
    ) -> Tuple[bool, str, Optional[int]]:
        """Convert an image file to specified format."""
        start_time = time.time()

        try:
            with Image.open(input_path) as img:
                img = ImageOps.exif_transpose(img)
                original_size = img.size

                logger.log(f"Original image: {original_size[0]}x{original_size[1]}", LogLevel.DEBUG, "Converter")

                # Apply resize if configured (happens first, before format conversion)
                img = ImageConverter.apply_resize(img, settings)

                if img.size != original_size:
                    logger.log(f"Resized to: {img.size[0]}x{img.size[1]}", LogLevel.INFO, "Converter")

                # ==========================================
                # Format-specific preparation
                # ==========================================
                img = ImageConverter._prepare_for_format(img, settings)

                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Target size mode - iterative compression
                if settings.target_size_kb and settings.output_format not in [ImageFormat.PNG, ImageFormat.BMP, ImageFormat.GIF, ImageFormat.ICO]:
                    success, msg, size = ImageConverter._compress_to_target_size(
                        img, output_path, settings
                    )
                    elapsed = time.time() - start_time
                    return (success, f"{msg} ({elapsed:.2f}s)", size)

                # Normal quality-based compression
                save_kwargs = settings.to_pillow_kwargs()
                img.save(output_path, **save_kwargs)

            output_size = output_path.stat().st_size
            elapsed = time.time() - start_time

            return (True, f"Converted successfully in {elapsed:.2f}s", output_size)

        except Exception as e:
            logger.log(f"Conversion error: {str(e)}", LogLevel.ERROR, "Converter")
            return (False, f"Conversion failed: {str(e)}", None)

    @staticmethod
    def apply_resize(img: Image.Image, settings: ConversionSettings) -> Image.Image:
        """Apply resize based on settings."""
        if settings.resize_mode == ResizeMode.NONE:
            return img

        original_width, original_height = img.size

        if settings.resize_mode == ResizeMode.PERCENTAGE:
            scale = settings.resize_percentage / 100.0
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)

            if (new_width, new_height) != (original_width, original_height):
                logger.log(
                    f"Percentage resize: {original_width}×{original_height} → {new_width}×{new_height} ({settings.resize_percentage}%)",
                    LogLevel.INFO,
                    "Converter"
                )
                return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            return img

        elif settings.resize_mode == ResizeMode.FIT_TO_WIDTH:
            # Resize to target width, height follows aspect ratio
            if not settings.target_width_px:
                logger.log("Fit to width: No target width specified", LogLevel.DEBUG, "Converter")
                return img

            target_w = settings.target_width_px
            aspect_ratio = original_width / original_height
            new_w = target_w
            new_h = int(target_w / aspect_ratio)

            # Don't upscale unless allowed
            if not settings.allow_upscaling and new_w > original_width:
                logger.log(
                    f"Fit to width: Target {target_w}px exceeds original {original_width}px, upscaling disabled",
                    LogLevel.DEBUG,
                    "Converter"
                )
                return img

            if (new_w, new_h) != (original_width, original_height):
                logger.log(
                    f"Fit to width: {original_width}×{original_height} → {new_w}×{new_h}",
                    LogLevel.INFO,
                    "Converter"
                )
                return img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            return img

        elif settings.resize_mode == ResizeMode.FIT_TO_HEIGHT:
            # Resize to target height, width follows aspect ratio
            if not settings.target_height_px:
                logger.log("Fit to height: No target height specified", LogLevel.DEBUG, "Converter")
                return img

            target_h = settings.target_height_px
            aspect_ratio = original_width / original_height
            new_h = target_h
            new_w = int(target_h * aspect_ratio)

            # Don't upscale unless allowed
            if not settings.allow_upscaling and new_h > original_height:
                logger.log(
                    f"Fit to height: Target {target_h}px exceeds original {original_height}px, upscaling disabled",
                    LogLevel.DEBUG,
                    "Converter"
                )
                return img

            if (new_w, new_h) != (original_width, original_height):
                logger.log(
                    f"Fit to height: {original_width}×{original_height} → {new_w}×{new_h}",
                    LogLevel.INFO,
                    "Converter"
                )
                return img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            return img

        elif settings.resize_mode == ResizeMode.FIT_TO_DIMENSIONS:
            # Fit within max width × max height box
            max_w = settings.max_width_px
            max_h = settings.max_height_px

            if not max_w and not max_h:
                logger.log("Fit to dimensions: No dimensions specified", LogLevel.DEBUG, "Converter")
                return img

            new_w, new_h = ImageConverter._calculate_fit_dimensions(
                original_width, original_height, max_w, max_h, settings.allow_upscaling
            )

            if (new_w, new_h) != (original_width, original_height):
                logger.log(
                    f"Fit to dimensions: {original_width}×{original_height} → {new_w}×{new_h}",
                    LogLevel.INFO,
                    "Converter"
                )
                return img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            else:
                logger.log(
                    "Fit to dimensions: Image already within constraints",
                    LogLevel.DEBUG,
                    "Converter"
                )
                return img

        return img

    @staticmethod
    def _prepare_for_format(img: Image.Image, settings: ConversionSettings) -> Image.Image:
        """
        Prepare image for target format (convert color modes, handle format-specific requirements).

        This method handles all format-specific transformations that must happen
        BEFORE saving (e.g., JPEG RGB conversion, GIF palette, ICO square enforcement).

        Args:
            img: PIL Image to prepare
            settings: Conversion settings with target format

        Returns:
            Prepared PIL Image (may be modified in-place or new instance)
        """
        # JPEG: Convert RGBA/LA/P to RGB (JPEG doesn't support transparency)
        if settings.output_format == ImageFormat.JPEG and img.mode in ('RGBA', 'LA', 'P'):
            logger.log(f"Converting {img.mode} → RGB for JPEG format", LogLevel.DEBUG, "Converter")
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            logger.log("Converted to RGB for JPEG (white background applied)", LogLevel.INFO, "Converter")
            return rgb_img

        # ==========================================
        # GIF format preparation
        # ==========================================
        elif settings.output_format == ImageFormat.GIF:
            # GIF requires palette mode (256 colors max)
            if img.mode != 'P':
                logger.log(f"Converting {img.mode} → P (palette) for GIF format", LogLevel.DEBUG, "Converter")

                # Convert to palette mode with adaptive palette
                # Apply dithering based on settings
                if settings.gif_dithering == "floyd":
                    img = img.convert('P', palette=Image.ADAPTIVE, colors=256)
                else:  # "none"
                    img = img.convert('P', palette=Image.ADAPTIVE, colors=256, dither=Image.NONE)

                logger.log(
                    f"Converted to palette mode for GIF (256 colors, dithering={settings.gif_dithering})",
                    LogLevel.INFO,
                    "Converter"
                )

            return img

        # ==========================================
        # ICO format preparation
        # ==========================================
        elif settings.output_format == ImageFormat.ICO:
            target_size = settings.ico_size

            logger.log(
                f"ICO preparation: Original size {img.width}×{img.height}, target {target_size}×{target_size}",
                LogLevel.DEBUG,
                "Converter"
            )

            if img.width != img.height:
                # Image is not square - apply force square method

                if settings.ico_force_square == "pad":
                    # Pad with transparency to make square
                    logger.log("ICO: Using PAD method", LogLevel.INFO, "Converter")

                    # Ensure RGBA mode for transparency
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')

                    # Find the largest dimension
                    max_dim = max(img.width, img.height)

                    # Create new square image with transparent background
                    new_img = Image.new('RGBA', (max_dim, max_dim), (0, 0, 0, 0))

                    # Calculate position to center-paste original image
                    paste_x = (max_dim - img.width) // 2
                    paste_y = (max_dim - img.height) // 2
                    new_img.paste(img, (paste_x, paste_y))

                    # Resize to target ICO size
                    img = new_img.resize((target_size, target_size), Image.Resampling.LANCZOS)

                    logger.log(
                        f"ICO: Padded and resized to {target_size}×{target_size}",
                        LogLevel.INFO,
                        "Converter"
                    )

                elif settings.ico_force_square == "crop":
                    # Crop to center square
                    logger.log("ICO: Using CROP method", LogLevel.INFO, "Converter")

                    # Find the smallest dimension
                    min_dim = min(img.width, img.height)

                    # Calculate center crop coordinates
                    left = (img.width - min_dim) // 2
                    top = (img.height - min_dim) // 2
                    right = left + min_dim
                    bottom = top + min_dim

                    # Crop to square
                    img = img.crop((left, top, right, bottom))

                    # Resize to target ICO size
                    img = img.resize((target_size, target_size), Image.Resampling.LANCZOS)

                    logger.log(
                        f"ICO: Cropped and resized to {target_size}×{target_size}",
                        LogLevel.INFO,
                        "Converter"
                    )

            else:
                # Already square - just resize to target size
                logger.log("ICO: Image already square", LogLevel.INFO, "Converter")
                if img.width != target_size:
                    img = img.resize((target_size, target_size), Image.Resampling.LANCZOS)
                    logger.log(f"ICO: Resized to {target_size}×{target_size}", LogLevel.INFO, "Converter")

            # Ensure RGBA mode (32-bit ICO)
            if img.mode != 'RGBA':
                logger.log(f"ICO: Converting {img.mode} → RGBA", LogLevel.DEBUG, "Converter")
                img = img.convert('RGBA')

            return img

        # ==========================================
        # TIFF format preparation
        # ==========================================
        elif settings.output_format == ImageFormat.TIFF:
            # TIFF supports RGBA natively, no conversion needed
            logger.log(f"TIFF format: No conversion needed (mode={img.mode})", LogLevel.DEBUG, "Converter")
            # Pass through as-is
            return img

        # ==========================================
        # BMP format preparation
        # ==========================================
        elif settings.output_format == ImageFormat.BMP:
            # BMP supports RGB/RGBA
            # Convert palette mode if present for better compatibility
            if img.mode == 'P':
                logger.log(f"Converting P (palette) → RGBA for BMP format", LogLevel.DEBUG, "Converter")
                img = img.convert('RGBA')

            return img

        # WebP, AVIF, PNG - pass through (handled by PIL automatically)
        return img

    @staticmethod
    def _calculate_fit_dimensions(
            orig_w: int,
            orig_h: int,
            max_w: Optional[int],
            max_h: Optional[int],
            allow_upscale: bool
    ) -> tuple[int, int]:
        """
        Calculate dimensions that fit within max_w × max_h while preserving aspect ratio.

        Args:
            orig_w: Original width
            orig_h: Original height
            max_w: Maximum width (None = unlimited)
            max_h: Maximum height (None = unlimited)
            allow_upscale: Whether to allow upscaling

        Returns:
            (new_width, new_height) tuple
        """
        aspect_ratio = orig_w / orig_h

        # If only one dimension specified
        if max_w and not max_h:
            new_w = max_w
            new_h = int(max_w / aspect_ratio)
        elif max_h and not max_w:
            new_h = max_h
            new_w = int(max_h * aspect_ratio)
        else:
            # Both dimensions specified - fit within box
            # Determine which dimension is the limiting factor
            if orig_w / max_w > orig_h / max_h:
                # Width is the limiting factor
                new_w = max_w
                new_h = int(max_w / aspect_ratio)
            else:
                # Height is the limiting factor
                new_h = max_h
                new_w = int(max_h * aspect_ratio)

        # Don't upscale unless explicitly allowed
        if not allow_upscale:
            new_w = min(new_w, orig_w)
            new_h = min(new_h, orig_h)

        return new_w, new_h

    @staticmethod
    def _compress_to_target_size(
            img: Image.Image,
            output_path: Path,
            settings: ConversionSettings,
            max_iterations: int = 20
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Compress image to target file size using improved binary search.

        Strategy:
        1. Test at minimum acceptable quality (15) to see if target is possible
        2. If not possible, suggest resize
        3. Otherwise, binary search for optimal quality
        """
        target_bytes = int(settings.target_size_kb * 1024)
        tolerance = max(0.02, 5120 / target_bytes)  # 2% or 5KB, whichever is larger

        min_quality = 15  # Don't go below this - quality becomes trash
        max_quality = 95  # Start at 95, quality 95-100 has minimal visual difference

        logger.log(f"Target size: {settings.target_size_kb}KB (tolerance: {tolerance * 100:.1f}%)",
                   LogLevel.INFO, "Converter")

        # Step 1: Check if target is achievable at minimum quality
        buffer = io.BytesIO()
        kwargs = settings.to_pillow_kwargs(quality_override=min_quality)
        img.save(buffer, **kwargs)
        min_size = len(buffer.getvalue())

        logger.log(f"Size at quality {min_quality}: {min_size / 1024:.1f}KB", LogLevel.DEBUG, "Converter")

        if min_size > target_bytes * (1 + tolerance):
            # Target not achievable even at minimum quality
            suggested_scale = math.sqrt(target_bytes / min_size)
            logger.log(
                f"Target size not achievable. Minimum possible: {min_size / 1024:.1f}KB. "
                f"Try resizing to {suggested_scale * 100:.0f}% or lower.",
                LogLevel.WARNING,
                "Converter"
            )
            # Save at minimum quality anyway
            with open(output_path, 'wb') as f:
                f.write(buffer.getvalue())
            return (
                True,
                f"⚠ Target not achievable. Saved at quality {min_quality} ({min_size / 1024:.1f}KB). Try resizing.",
                min_size
            )

        # Step 2: Binary search for optimal quality
        best_quality = (min_quality + max_quality) // 2
        best_buffer = None
        best_size = min_size

        for iteration in range(max_iterations):
            buffer = io.BytesIO()
            kwargs = settings.to_pillow_kwargs(quality_override=best_quality)
            img.save(buffer, **kwargs)
            current_size = len(buffer.getvalue())

            logger.log(
                f"Iteration {iteration + 1}: quality={best_quality}, size={current_size / 1024:.1f}KB",
                LogLevel.DEBUG,
                "Converter"
            )

            # Check if within tolerance
            size_ratio = current_size / target_bytes
            if (1 - tolerance) <= size_ratio <= (1 + tolerance):
                # Perfect! Within tolerance
                with open(output_path, 'wb') as f:
                    f.write(buffer.getvalue())
                logger.log(
                    f"✓ Target achieved at quality {best_quality}",
                    LogLevel.SUCCESS,
                    "Converter"
                )
                return (
                    True,
                    f"✓ Target size achieved (quality {best_quality}, {current_size / 1024:.1f}KB)",
                    current_size
                )

            # Track best attempt (closest to target without exceeding much)
            if best_buffer is None or abs(current_size - target_bytes) < abs(best_size - target_bytes):
                best_buffer = buffer.getvalue()
                best_size = current_size

            # Binary search adjustment
            if current_size > target_bytes:
                # Too large, reduce quality
                max_quality = best_quality
            else:
                # Too small, increase quality
                min_quality = best_quality

            new_quality = (min_quality + max_quality) // 2

            # Check for convergence
            if new_quality == best_quality or max_quality - min_quality <= 1:
                break

            best_quality = new_quality

        # Save best attempt
        if best_buffer:
            with open(output_path, 'wb') as f:
                f.write(best_buffer)

        logger.log(
            f"Closest match: quality {best_quality}, size {best_size / 1024:.1f}KB",
            LogLevel.INFO,
            "Converter"
        )

        return (
            True,
            f"Closest match at quality {best_quality} ({best_size / 1024:.1f}KB)",
            best_size
        )

    @staticmethod
    def calculate_savings(original_size: int, converted_size: int) -> Tuple[float, str]:
        """Calculate size reduction percentage."""
        if original_size == 0:
            return (0.0, "N/A")

        savings_percent = ((original_size - converted_size) / original_size) * 100

        if savings_percent > 0:
            return (savings_percent, f"{savings_percent:.1f}% smaller")
        else:
            return (savings_percent, f"{abs(savings_percent):.1f}% larger")
