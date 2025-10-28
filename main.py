import sys
from pathlib import Path

# ===================================================================
# CRITICAL: Import AVIF plugin BEFORE any PIL/Pillow imports
# This must be the very first thing after standard library imports
# ===================================================================
try:
    import pillow_avif
    print("✓ AVIF support enabled")
except ImportError:
    print("⚠ Warning: pillow-avif-plugin not installed")
    print("  AVIF files cannot be imported/previewed")
    print("  Install with: pip install pillow-avif-plugin")
# ===================================================================

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase, QFont
from ui.main_window import MainWindow


def load_custom_fonts(app: QApplication) -> str:
    """
    Load custom fonts from the fonts/ folder with anti-aliasing.
    Returns the name of the primary font family.
    """
    fonts_dir = Path(__file__).parent / "fonts"

    if not fonts_dir.exists():
        print(f"Warning: Fonts directory not found at {fonts_dir}")
        return "Segoe UI"

    # Try variable font first (best option)
    variable_font = fonts_dir / "Inter-VariableFont_opsz,wght.ttf"
    if variable_font.exists():
        font_id = QFontDatabase.addApplicationFont(str(variable_font))
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

    # Fallback to static fonts
    font_files = [
        "SFMonoBold.otf",  # Use these instead of _18pt
        "SFMonoMedium.otf",
        "SFMonoRegular.otf",
        "SFMonoSemibold.otf"
    ]

    font_family = None

    for font_file in font_files:
        font_path = fonts_dir / font_file
        if font_path.exists():
            font_id = QFontDatabase.addApplicationFont(str(font_path))
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    font_family = families[0]
                    print(f"✓ Loaded font: {font_file} ({font_family})")
            else:
                print(f"✗ Failed to load: {font_file}")

    if font_family:
        # Configure font with anti-aliasing
        font = QFont(font_family, 9)
        font.setStyleStrategy(
            QFont.StyleStrategy.PreferAntialias |
            QFont.StyleStrategy.PreferQuality
        )
        font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)

        app.setFont(font)
        return font_family
    else:
        print("Warning: No fonts loaded, using system default")
        return "Segoe UI"


def load_theme(app: QApplication, font_family: str) -> None:
    """Load and apply the master theme stylesheet."""
    theme_file = Path(__file__).parent / "theme.qss"

    if theme_file.exists():
        with open(theme_file, 'r', encoding='utf-8') as f:
            stylesheet = f.read()
            # Replace font-family placeholder with loaded font
            stylesheet = stylesheet.replace("{{FONT_FAMILY}}", font_family)
            app.setStyleSheet(stylesheet)
        print(f"✓ Theme loaded with font: {font_family}")
    else:
        print(f"ERROR: Theme file not found at {theme_file}")
        sys.exit(1)


def main():
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("ConverterX")
    app.setOrganizationName("YourCompany")

    # Load custom fonts first
    font_family = load_custom_fonts(app)

    # Apply theme with custom font
    load_theme(app, font_family)

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
