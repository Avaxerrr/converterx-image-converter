"""Dialog for displaying image metadata and EXIF information."""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit
from PySide6.QtCore import Qt
from models.image_file import ImageFile

try:
    from PIL import Image
    from PIL.ExifTags import TAGS

    EXIF_AVAILABLE = True
except ImportError:
    EXIF_AVAILABLE = False


class MetadataDialog(QDialog):
    """Dialog to display image metadata/EXIF information."""

    def __init__(self, image_file: ImageFile, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Metadata - {image_file.filename}")
        self.setMinimumSize(500, 400)
        self._setup_ui(image_file)

    def _setup_ui(self, image_file: ImageFile):
        """Setup the metadata dialog UI."""
        layout = QVBoxLayout(self)

        # Text display for metadata
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Courier New', monospace;
                font-size: 10pt;
                border: 1px solid #3e3e42;
                padding: 8px;
            }
        """)

        # Load and display metadata
        metadata_text = self._load_metadata(image_file)
        self.text_edit.setHtml(metadata_text)

        layout.addWidget(self.text_edit)

    def _load_metadata(self, image_file: ImageFile) -> str:
        """Load metadata from image file."""
        html = "<h3 style='color: #4ec9b0;'>Basic Information</h3>"
        html += f"<table style='color: #d4d4d4;'>"
        html += f"<tr><td><b>Filename:</b></td><td>{image_file.filename}</td></tr>"
        html += f"<tr><td><b>Path:</b></td><td>{image_file.path}</td></tr>"
        html += f"<tr><td><b>Format:</b></td><td>{image_file.format}</td></tr>"
        html += f"<tr><td><b>Dimensions:</b></td><td>{image_file.dimensions_str} px</td></tr>"
        html += f"<tr><td><b>File Size:</b></td><td>{image_file.size_str}</td></tr>"
        html += "</table>"

        if EXIF_AVAILABLE:
            try:
                with Image.open(image_file.path) as img:
                    exif_data = img._getexif()
                    if exif_data:
                        html += "<br><h3 style='color: #4ec9b0;'>EXIF Data</h3>"
                        html += "<table style='color: #d4d4d4;'>"
                        for tag_id, value in exif_data.items():
                            tag = TAGS.get(tag_id, tag_id)
                            html += f"<tr><td><b>{tag}:</b></td><td>{value}</td></tr>"
                        html += "</table>"
                    else:
                        html += "<br><p style='color: #808080;'>No EXIF data available</p>"
            except Exception as e:
                html += f"<br><p style='color: #f48771;'>Error reading EXIF: {e}</p>"
        else:
            html += "<br><p style='color: #808080;'>PIL not available for EXIF reading</p>"

        return html
