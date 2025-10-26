import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from ui.main_window import MainWindow


def load_stylesheet(app: QApplication) -> None:
    """Load and apply the custom dark stylesheet."""
    style_file = Path(__file__).parent / "styles.qss"

    if style_file.exists():
        with open(style_file, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    else:
        print(f"Warning: Stylesheet not found at {style_file}")


def main():
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("ConverterX")
    app.setOrganizationName("YourName")

    # Apply custom dark theme
    load_stylesheet(app)

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
