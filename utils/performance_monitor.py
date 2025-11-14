"""
Performance Monitor

Self-contained module for monitoring CPU and RAM usage.
Uses psutil if available, gracefully degrades if not.

CPU measurement shows % of total system capacity (normalized by core count).
Instant values - no smoothing, shows real-time response.
"""

from typing import Tuple, Optional
import os

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class PerformanceMonitor:
    """
    Monitors CPU and RAM usage of the current process.

    CPU % represents usage of total system capacity (0-100%).
    Instant values with no smoothing for real-time responsiveness.
    """

    def __init__(self):
        """Initialize performance monitor."""
        self.process = None
        self._cpu_count = os.cpu_count() or 1  # Auto-detect logical core count

        if PSUTIL_AVAILABLE:
            try:
                self.process = psutil.Process()
                # Prime the CPU counter with a small interval
                self.process.cpu_percent(interval=0.1)
            except Exception:
                self.process = None

    def is_available(self) -> bool:
        """Check if performance monitoring is available."""
        return PSUTIL_AVAILABLE and self.process is not None

    def get_cpu_percent(self) -> Optional[float]:
        """
        Get current CPU usage as % of total system capacity.

        Returns normalized CPU usage (0-100%) representing how much of the
        system's total CPU resources this process is consuming.

        Formula: (raw_cpu_percent / cpu_core_count)
        Example: 120% raw on 12-core system = 10% of system capacity

        Instant value - no smoothing applied.

        Returns:
            CPU percentage (0-100) of system capacity, or None if unavailable
        """
        if not self.is_available():
            return None

        try:
            # Get raw CPU percent (can exceed 100% on multi-core)
            raw_cpu = self.process.cpu_percent(interval=None)

            # Normalize to system capacity (0-100%)
            normalized_cpu = raw_cpu / self._cpu_count

            # Clamp to 0-100% range
            normalized_cpu = min(100.0, max(0.0, normalized_cpu))

            return normalized_cpu

        except Exception:
            return None

    def get_cpu_percent_raw(self) -> Optional[float]:
        """
        Get raw CPU usage (can exceed 100% on multi-core systems).

        Useful for detailed tooltips showing core utilization.

        Returns:
            Raw CPU percentage (0-N*100 where N=cores) or None if unavailable
        """
        if not self.is_available():
            return None

        try:
            return self.process.cpu_percent(interval=None)
        except Exception:
            return None

    def get_memory_mb(self) -> Optional[float]:
        """
        Get current memory usage in MB.

        Uses RSS (Resident Set Size) - actual physical RAM used by process.
        May differ slightly (~50-100 MB) from Task Manager's "Memory" column.

        Returns:
            Memory usage in MB or None if unavailable
        """
        if not self.is_available():
            return None

        try:
            mem_bytes = self.process.memory_info().rss
            return mem_bytes / (1024 * 1024)  # Convert to MB
        except Exception:
            return None

    def get_stats(self) -> Tuple[Optional[float], Optional[float]]:
        """
        Get both CPU and RAM stats in one call.

        Returns:
            Tuple of (cpu_percent_normalized, memory_mb) or (None, None)
        """
        return (self.get_cpu_percent(), self.get_memory_mb())

    def get_cpu_count(self) -> int:
        """
        Get number of logical CPU cores (includes hyperthreading).

        Detected automatically at initialization.

        Returns:
            Number of logical processors on the system
        """
        return self._cpu_count

    def get_cpu_cores_utilized(self) -> Optional[float]:
        """
        Calculate approximate number of cores being utilized.

        Example: 33% system capacity on 12-core = ~4 cores utilized

        Returns:
            Approximate cores in use, or None if unavailable
        """
        cpu_percent = self.get_cpu_percent()
        if cpu_percent is None:
            return None

        # Convert % back to approximate core count
        return (cpu_percent / 100.0) * self._cpu_count

    @staticmethod
    def format_memory(mb: float) -> str:
        """
        Format memory value for human-readable display.

        Args:
            mb: Memory in megabytes

        Returns:
            Formatted string like "234 MB" or "1.2 GB"
        """
        if mb >= 1024:
            return f"{mb / 1024:.1f} GB"
        return f"{int(mb)} MB"
