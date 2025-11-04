
"""
Batch Processor

Manages queue of image conversions with concurrent worker limit.
Handles up to 4 simultaneous conversions using existing ConversionWorker.
"""

from PySide6.QtCore import QObject, Signal, QThreadPool
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from models.image_file import ImageFile
from workers.conversion_worker import ConversionWorker
from core.format_settings import ConversionSettings
from utils.logger import logger, LogLevel


@dataclass
class BatchFileResult:
    """Result of a single file conversion in batch."""
    image_file: ImageFile
    success: bool
    output_path: Optional[Path] = None
    bytes_saved: int = 0
    error_message: str = ""


class BatchProcessor(QObject):
    """
    Manages batch conversion queue with concurrent worker limit.
    
    Processes multiple files using ConversionWorker, limiting to
    MAX_CONCURRENT simultaneous conversions.
    """
    
    # Signals
    file_started = Signal(ImageFile, int, int)  # file, current_index, total
    file_progress = Signal(ImageFile, int)  # file, progress (0-100)
    file_completed = Signal(ImageFile, Path, int)  # file, output_path, bytes_saved
    file_failed = Signal(ImageFile, str)  # file, error_message
    batch_finished = Signal(int, int, int)  # total, successful, failed
    
    MAX_CONCURRENT = 4  # Maximum simultaneous conversions
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Batch state
        self.file_queue: List[ImageFile] = []
        self.active_workers: Dict[ImageFile, ConversionWorker] = {}
        self.completed_files: List[BatchFileResult] = []
        self.failed_files: List[BatchFileResult] = []
        
        # Settings snapshot
        self.settings_snapshot: Optional[ConversionSettings] = None
        self.output_folder: Optional[Path] = None
        
        # Control flags
        self.cancel_requested = False
        self.is_batch_running = False
        
        # Thread pool
        self.threadpool = QThreadPool.globalInstance()
        
        # Tracking
        self.total_files = 0
        self.current_index = 0
    
    def start_batch(
        self,
        files: List[ImageFile],
        settings: ConversionSettings,
        output_folder: Path
    ):
        """
        Start batch conversion of multiple files.
        
        Args:
            files: List of ImageFile objects to convert
            settings: ConversionSettings snapshot (captured at batch start)
            output_folder: Output directory for converted files
        """
        if self.is_batch_running:
            logger.warning("Batch already running. Ignoring new batch request.", "BatchProcessor")
            return
        
        # Reset state
        self.file_queue = files.copy()
        self.active_workers.clear()
        self.completed_files.clear()
        self.failed_files.clear()
        
        # Capture snapshot
        self.settings_snapshot = settings
        self.output_folder = output_folder
        
        # Control flags
        self.cancel_requested = False
        self.is_batch_running = True
        
        # Tracking
        self.total_files = len(files)
        self.current_index = 0
        
        logger.info(f"Starting batch conversion of {self.total_files} files", "BatchProcessor")
        logger.debug(f"Settings: {settings.output_format.value}, Quality {settings.quality}", "BatchProcessor")
        
        # Start initial workers (up to MAX_CONCURRENT)
        self._start_initial_workers()
    
    def cancel_all(self):
        """
        Cancel batch conversion.
        
        Sets cancel flag to prevent new files from starting.
        Currently active workers will finish their work.
        """
        if not self.is_batch_running:
            return
        
        self.cancel_requested = True
        pending_count = len(self.file_queue)
        logger.warning(f"Batch cancellation requested. {pending_count} files will be skipped.", "BatchProcessor")
    
    def is_running(self) -> bool:
        """Check if batch is currently active."""
        return self.is_batch_running
    
    def _start_initial_workers(self):
        """Start up to MAX_CONCURRENT workers from the queue."""
        workers_to_start = min(self.MAX_CONCURRENT, len(self.file_queue))
        
        for _ in range(workers_to_start):
            self._start_next_file()
    
    def _start_next_file(self):
        """
        Start conversion of next file in queue.
        
        Internal method called when a worker slot is available.
        Respects MAX_CONCURRENT limit and cancel_requested flag.
        """
        # Check if we should stop
        if self.cancel_requested:
            logger.debug("Batch cancelled. Skipping remaining files.", "BatchProcessor")
            self._check_batch_completion()
            return
        
        # Check if queue is empty
        if not self.file_queue:
            self._check_batch_completion()
            return
        
        # Check concurrent limit
        if len(self.active_workers) >= self.MAX_CONCURRENT:
            return
        
        # Get next file
        image_file = self.file_queue.pop(0)
        self.current_index += 1
        
        # Create output path
        output_filename = f"{image_file.path.stem}.{self.settings_snapshot.output_format.value.lower()}"
        output_path = self.output_folder / output_filename
        
        # Create worker
        worker = ConversionWorker(
            image_file=image_file,
            output_path=output_path,
            settings=self.settings_snapshot
        )
        
        # Connect signals
        worker.signals.success.connect(lambda result: self._on_worker_success(image_file, result))
        worker.signals.error.connect(lambda error: self._on_worker_error(image_file, error))
        worker.signals.progress.connect(lambda prog: self.file_progress.emit(image_file, prog))
        
        # Track active worker
        self.active_workers[image_file] = worker
        
        # Emit started signal
        self.file_started.emit(image_file, self.current_index, self.total_files)
        logger.debug(f"Starting conversion [{self.current_index}/{self.total_files}]: {image_file.filename}", "BatchProcessor")
        
        # Start worker
        self.threadpool.start(worker)
    
    def _on_worker_success(self, image_file: ImageFile, result: dict):
        """
        Handle successful file conversion.
        
        Args:
            image_file: The converted file
            result: Result dict from ConversionWorker (contains output_path, size_saved)
        """
        # Remove from active workers
        if image_file in self.active_workers:
            del self.active_workers[image_file]
        
        # Extract result data
        output_path = result.get('output_path')
        size_saved = result.get('size_saved', 0)
        
        # Record result
        batch_result = BatchFileResult(
            image_file=image_file,
            success=True,
            output_path=output_path,
            bytes_saved=size_saved
        )
        self.completed_files.append(batch_result)
        
        # Emit signal
        self.file_completed.emit(image_file, output_path, size_saved)
        logger.success(f"Completed: {image_file.filename} (saved {size_saved / 1024:.1f} KB)", "BatchProcessor")
        
        # Start next file
        self._start_next_file()
    
    def _on_worker_error(self, image_file: ImageFile, error_message: str):
        """
        Handle failed file conversion.
        
        Args:
            image_file: The file that failed
            error_message: Error description
        """
        # Remove from active workers
        if image_file in self.active_workers:
            del self.active_workers[image_file]
        
        # Record failure
        batch_result = BatchFileResult(
            image_file=image_file,
            success=False,
            error_message=error_message
        )
        self.failed_files.append(batch_result)
        
        # Emit signal
        self.file_failed.emit(image_file, error_message)
        logger.error(f"Failed: {image_file.filename} - {error_message}", "BatchProcessor")
        
        # Continue with next file (don't stop batch)
        self._start_next_file()
    
    def _check_batch_completion(self):
        """
        Check if batch is complete.
        
        Called after each file finishes or when cancellation requested.
        Emits batch_finished signal when all work is done.
        """
        # Check if any workers still active or files in queue
        if len(self.active_workers) > 0 or (len(self.file_queue) > 0 and not self.cancel_requested):
            return
        
        # Batch is complete
        self.is_batch_running = False
        
        successful_count = len(self.completed_files)
        failed_count = len(self.failed_files)
        
        # Emit completion signal
        self.batch_finished.emit(self.total_files, successful_count, failed_count)
        
        # Log summary
        logger.info(
            f"Batch conversion finished: {successful_count} successful, {failed_count} failed",
            "BatchProcessor"
        )