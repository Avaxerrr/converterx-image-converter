from pathlib import Path
from PIL import Image, ImageOps
from typing import Optional, Tuple
from core.format_settings import ConversionSettings
import time
import io


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
            return (False, f"Conversion failed: {str(e)}", None)

    @staticmethod
    def _compress_to_target_size(
            img: Image.Image,
            output_path: Path,
            settings: ConversionSettings,
            max_iterations: int = 10
    ) -> Tuple[bool, str, Optional[int]]:
        """Compress image to target file size using binary search."""
        target_bytes = int(settings.target_size_kb * 1024)
        tolerance = 0.05  # 5% tolerance

        min_quality = 1
        max_quality = 100
        best_quality = 85

        for iteration in range(max_iterations):
            # Try current quality
            buffer = io.BytesIO()
            kwargs = settings.to_pillow_kwargs(quality_override=best_quality)
            img.save(buffer, **kwargs)
            current_size = len(buffer.getvalue())

            # Check if within tolerance
            size_ratio = current_size / target_bytes
            if 0.95 <= size_ratio <= 1.05:
                # Good enough - save to file
                with open(output_path, 'wb') as f:
                    f.write(buffer.getvalue())
                return (
                    True,
                    f"Compressed to target size (quality {best_quality})",
                    current_size
                )

            # Binary search adjustment
            if current_size > target_bytes:
                # Too large, reduce quality
                max_quality = best_quality
                best_quality = (min_quality + best_quality) // 2
            else:
                # Too small, increase quality
                min_quality = best_quality
                best_quality = (best_quality + max_quality) // 2

            # Avoid infinite loop
            if max_quality - min_quality <= 1:
                break

        # Save best attempt
        buffer = io.BytesIO()
        kwargs = settings.to_pillow_kwargs(quality_override=best_quality)
        img.save(buffer, **kwargs)

        with open(output_path, 'wb') as f:
            f.write(buffer.getvalue())

        final_size = len(buffer.getvalue())

        return (
            True,
            f"Closest match at quality {best_quality} ({final_size / 1024:.1f}KB)",
            final_size
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
