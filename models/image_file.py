from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ImageFile:
    """Represents an image file in the conversion queue."""

    path: Path
    size_bytes: int
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None

    @property
    def filename(self) -> str:
        """Get the filename without path."""
        return self.path.name

    @property
    def size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.size_bytes / (1024 * 1024)

    @property
    def size_kb(self) -> float:
        """Get file size in kilobytes."""
        return self.size_bytes / 1024

    @property
    def dimensions_str(self) -> str:
        """Get dimensions as string."""
        if self.width and self.height:
            return f"{self.width} × {self.height}"
        return "Unknown"

    @property
    def size_str(self) -> str:
        """Get formatted file size."""
        if self.size_bytes < 1024:
            return f"{self.size_bytes} B"
        elif self.size_bytes < 1024 * 1024:
            return f"{self.size_kb:.1f} KB"
        else:
            return f"{self.size_mb:.2f} MB"

    def __str__(self) -> str:
        return f"{self.filename} ({self.dimensions_str}, {self.size_str})"
