import sys
from pathlib import Path

import pillow_avif
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QFile, QTextStream
from PySide6.QtGui import QFontDatabase, QFont, QIcon
from ui.main_window import MainWindow
import resources_rc  # Import compiled resources


def load_custom_fonts(app: QApplication) -> str:
    """
    Load custom fonts from QRC resources with anti-aliasing.
    Returns the name of the primary font family.
    """
    # Load from QRC
    font_id = QFontDatabase.addApplicationFont(":/fonts/Inter-VariableFont_opsz,wght.ttf")

    if font_id != -1:
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            font_family = families[0]
            print(f"✓ Loaded variable font: {font_family}")

            # Configure font with anti-aliasing
            font = QFont(font_family, 9)
            font.setStyleStrategy(
                QFont.StyleStrategy.PreferAntialias |
                QFont.StyleStrategy.PreferQuality
            )
            font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)

            app.setFont(font)
            return font_family

    print("Warning: No fonts loaded, using system default")
    return "Segoe UI"


def load_theme(app: QApplication, font_family: str) -> None:
    """Load and apply theme stylesheet from QRC resources."""
    # Load theme.qss from QRC
    file = QFile(":/theme/theme.qss")

    if file.open(QFile.ReadOnly | QFile.Text):
        stream = QTextStream(file)
        stylesheet = stream.readAll()
        file.close()

        # Replace font-family placeholder with loaded font
        stylesheet = stylesheet.replace("{{FONT_FAMILY}}", font_family)
        app.setStyleSheet(stylesheet)
        print(f"✓ Theme loaded with font: {font_family}")
    else:
        print(f"ERROR: Could not load theme from QRC resources")
        sys.exit(1)


def main():
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("ConverterX")
    app.setOrganizationName("YourCompany")

    # Set application icon (Windows taskbar, macOS dock, window title bar)
    app.setWindowIcon(QIcon(":/icons/app_icon.png"))

    # Load custom fonts first
    font_family = load_custom_fonts(app)

    # Load and apply theme with custom font
    load_theme(app, font_family)

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
