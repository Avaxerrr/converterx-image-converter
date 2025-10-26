from PySide6.QtCore import QObject, QRunnable, Signal, Slot
from pathlib import Path
from core.converter import ImageConverter
from core.format_settings import ConversionSettings
from models.image_file import ImageFile


class WorkerSignals(QObject):
    """Signals for conversion worker."""
    finished = Signal()
    error = Signal(str)
    success = Signal(object)  # Passes result dict
    progress = Signal(int)


class ConversionWorker(QRunnable):
    """Worker for converting a single image in a separate thread."""

    def __init__(
            self,
            image_file: ImageFile,
            output_path: Path,
            settings: ConversionSettings
    ):
        super().__init__()
        self.image_file = image_file
        self.output_path = output_path
        self.settings = settings
        self.signals = WorkerSignals()
        self.setAutoDelete(True)

    @Slot()
    def run(self):
        """Execute the conversion."""
        try:
            # Perform conversion
            success, message, output_size = ImageConverter.convert_image(
                self.image_file.path,
                self.output_path,
                self.settings
            )

            if success:
                # Calculate savings
                savings_pct, savings_str = ImageConverter.calculate_savings(
                    self.image_file.size_bytes,
                    output_size
                )

                result = {
                    'input_file': self.image_file,
                    'output_path': self.output_path,
                    'output_size': output_size,
                    'savings_percent': savings_pct,
                    'savings_string': savings_str,
                    'message': message
                }

                self.signals.success.emit(result)
            else:
                self.signals.error.emit(f"{self.image_file.filename}: {message}")

        except Exception as e:
            self.signals.error.emit(f"{self.image_file.filename}: {str(e)}")
        finally:
            self.signals.finished.emit()
