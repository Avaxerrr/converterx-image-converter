from dataclasses import dataclass
from pathlib import Path

from core.format_settings import ConversionSettings, ResizeMode
from utils.image_loader import get_svg_size
from utils.logger import logger, LogLevel


@dataclass(frozen=True)
class SvgRenderPlan:
    """Resolved render plan for an SVG input."""
    intrinsic_width: int
    intrinsic_height: int
    render_width: int
    render_height: int
    resize_applied: bool
    reason: str

    @property
    def render_size(self) -> tuple[int, int]:
        return self.render_width, self.render_height


def build_svg_render_plan(
        input_path: Path,
        settings: ConversionSettings,
        *,
        log_source: str
) -> SvgRenderPlan:
    """
    Compute the final pixel dimensions an SVG should be rendered at.

    This lets the app preserve SVG vector quality by rendering directly at the
    target output size instead of rasterizing first and resizing afterward.
    """
    intrinsic_width, intrinsic_height = get_svg_size(input_path)
    render_width = intrinsic_width
    render_height = intrinsic_height
    reason = "intrinsic size"

    if settings.resize_mode == ResizeMode.NONE:
        pass

    elif settings.resize_mode == ResizeMode.PERCENTAGE:
        scale = settings.resize_percentage / 100.0
        render_width = max(1, int(round(intrinsic_width * scale)))
        render_height = max(1, int(round(intrinsic_height * scale)))
        reason = f"percentage resize ({settings.resize_percentage}%)"

    elif settings.resize_mode == ResizeMode.FIT_TO_WIDTH:
        if settings.target_width_px:
            aspect_ratio = intrinsic_width / intrinsic_height
            render_width = settings.target_width_px
            render_height = max(1, int(round(settings.target_width_px / aspect_ratio)))
            reason = f"fit to width ({settings.target_width_px}px)"

            if not settings.allow_upscaling and render_width > intrinsic_width:
                render_width = intrinsic_width
                render_height = intrinsic_height
                reason += " - upscaling blocked"

    elif settings.resize_mode == ResizeMode.FIT_TO_HEIGHT:
        if settings.target_height_px:
            aspect_ratio = intrinsic_width / intrinsic_height
            render_height = settings.target_height_px
            render_width = max(1, int(round(settings.target_height_px * aspect_ratio)))
            reason = f"fit to height ({settings.target_height_px}px)"

            if not settings.allow_upscaling and render_height > intrinsic_height:
                render_width = intrinsic_width
                render_height = intrinsic_height
                reason += " - upscaling blocked"

    elif settings.resize_mode == ResizeMode.FIT_TO_DIMENSIONS:
        max_w = settings.max_width_px
        max_h = settings.max_height_px

        if max_w or max_h:
            render_width, render_height = _calculate_fit_dimensions(
                intrinsic_width,
                intrinsic_height,
                max_w,
                max_h,
                settings.allow_upscaling
            )
            reason = f"fit to dimensions ({max_w}x{max_h})"

    resize_applied = (render_width, render_height) != (intrinsic_width, intrinsic_height)

    logger.log(
        LogLevel.DEBUG,
        (
            f"SVG render plan for {input_path.name}: "
            f"intrinsic={intrinsic_width}x{intrinsic_height}, "
            f"render={render_width}x{render_height}, "
            f"resize_mode={settings.resize_mode.value}, "
            f"allow_upscaling={settings.allow_upscaling}, "
            f"reason={reason}"
        ),
        log_source
    )

    if resize_applied:
        logger.log(
            LogLevel.INFO,
            (
                f"SVG will be rendered directly at final size "
                f"{render_width}x{render_height} ({reason})"
            ),
            log_source
        )
    else:
        logger.log(
            LogLevel.DEBUG,
            "SVG render size matches intrinsic size; no post-raster resize needed",
            log_source
        )

    return SvgRenderPlan(
        intrinsic_width=intrinsic_width,
        intrinsic_height=intrinsic_height,
        render_width=render_width,
        render_height=render_height,
        resize_applied=resize_applied,
        reason=reason
    )


def _calculate_fit_dimensions(
        orig_w: int,
        orig_h: int,
        max_w: int | None,
        max_h: int | None,
        allow_upscale: bool
) -> tuple[int, int]:
    """Calculate a fit-within box size while preserving aspect ratio."""
    aspect_ratio = orig_w / orig_h

    if max_w and not max_h:
        new_w = max_w
        new_h = max(1, int(round(max_w / aspect_ratio)))
    elif max_h and not max_w:
        new_h = max_h
        new_w = max(1, int(round(max_h * aspect_ratio)))
    else:
        if orig_w / max_w > orig_h / max_h:
            new_w = max_w
            new_h = max(1, int(round(max_w / aspect_ratio)))
        else:
            new_h = max_h
            new_w = max(1, int(round(max_h * aspect_ratio)))

    if not allow_upscale:
        new_w = min(new_w, orig_w)
        new_h = min(new_h, orig_h)

    return new_w, new_h
