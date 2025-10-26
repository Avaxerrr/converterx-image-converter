from pathlib import Path
from PIL import Image, ImageOps
from typing import Optional, Tuple
from core.format_settings import ConversionSettings, ResizeMode
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

                # Apply resize if configured
                img = ImageConverter._apply_resize(img, settings)

                if img.size != original_size:
                    logger.log(f"Resized to: {img.size[0]}x{img.size[1]}", LogLevel.INFO, "Converter")

                # Convert RGBA to RGB for JPEG
                if settings.output_format.name == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = rgb_img

                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Target size mode - iterative compression
                if settings.target_size_kb and settings.output_format.name != 'PNG':
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
    def _apply_resize(img: Image.Image, settings: ConversionSettings) -> Image.Image:
        """Apply resize based on settings."""
        if settings.resize_mode == ResizeMode.NONE:
            return img

        original_width, original_height = img.size
        new_width, new_height = original_width, original_height

        if settings.resize_mode == ResizeMode.PERCENTAGE:
            scale = settings.resize_percentage / 100.0
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)

        elif settings.resize_mode == ResizeMode.MAX_DIMENSIONS:
            if settings.max_width and settings.max_height:
                if settings.maintain_aspect_ratio:
                    # Calculate scale to fit within max dimensions
                    width_scale = settings.max_width / original_width
                    height_scale = settings.max_height / original_height
                    scale = min(width_scale, height_scale, 1.0)  # Don't upscale

                    new_width = int(original_width * scale)
                    new_height = int(original_height * scale)
                else:
                    # Exact dimensions (may distort)
                    new_width = settings.max_width
                    new_height = settings.max_height
            elif settings.max_width:
                scale = settings.max_width / original_width
                new_width = settings.max_width
                new_height = int(original_height * scale) if settings.maintain_aspect_ratio else original_height
            elif settings.max_height:
                scale = settings.max_height / original_height
                new_height = settings.max_height
                new_width = int(original_width * scale) if settings.maintain_aspect_ratio else original_width

        # Only resize if dimensions actually changed
        if (new_width, new_height) != (original_width, original_height):
            # Use high-quality Lanczos resampling
            return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return img

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
