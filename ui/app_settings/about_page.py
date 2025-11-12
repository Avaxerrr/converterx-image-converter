"""
About Page

Information about the application, creator, and credits.
Separate from doc pages because it uses widgets, not just HTML.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QScrollArea, QFrame, QTextBrowser
)
from PySide6.QtCore import Qt, QSize, QUrl
from PySide6.QtGui import QIcon, QDesktopServices
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.app_settings import AppSettingsController


# ============================================================================
# CENTRALIZED STYLING
# ============================================================================
ABOUT_PAGE_STYLE = """
/* About Page Title */
QLabel#aboutAppName {
    font-size: 28px;
    font-weight: bold;
    color: #CCCCCC;
}

QLabel#aboutVersion {
    font-size: 14px;
    color: #858585;
}

QLabel#aboutTagline {
    font-size: 13px;
    color: #AAAAAA;
    font-style: italic;
}

/* Creator Section */
QLabel#creatorName {
    font-size: 14px;
    color: #CCCCCC;
}

QLabel#creatorDesc {
    color: #CCCCCC;
    font-size: 12px;
}

/* Link Buttons */
QPushButton#linkButton {
    background-color: #0e639c;
    border: 1px solid #007acc;
    border-radius: 3px;
    padding: 6px 14px;
    color: #ffffff;
    font-weight: 600;
    font-size: 9pt;
    min-height: 24px;
}

QPushButton#linkButton:hover {
    background-color: #1177bb;
    border-color: #0098ff;
}

QPushButton#linkButton:pressed {
    background-color: #0d5a8f;
}

/* Group Boxes */
QGroupBox {
    border: 1px solid #3e3e42;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 12px;
    font-weight: 600;
    font-size: 10pt;
    color: #CCCCCC;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
}

/* Tech Stack Text */
QTextBrowser#techText {
    background-color: #1e1e1e;
    border: none;
    color: #CCCCCC;
    font-size: 12px;
}

/* License Text */
QLabel#licenseText {
    color: #999999;
    font-size: 11px;
}
"""


class AboutPage(QWidget):
    """About page showing app info, creator, and credits."""

    def __init__(self, controller: 'AppSettingsController'):
        super().__init__()
        self.controller = controller
        self._setup_ui()
        self.setStyleSheet(ABOUT_PAGE_STYLE)

    def _setup_ui(self):
        """Build about page UI."""
        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        # === App Icon and Title ===
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignCenter)

        # App icon
        icon_label = QLabel()
        icon_pixmap = QIcon(":/icons/app_icon.png").pixmap(QSize(80, 80))
        icon_label.setPixmap(icon_pixmap)
        icon_label.setAlignment(Qt.AlignCenter)

        # App name and version
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)

        app_name = QLabel("ConverterX")
        app_name.setObjectName("aboutAppName")

        version_label = QLabel("Version 1.0.0")
        version_label.setObjectName("aboutVersion")

        tagline = QLabel("Modern Image Format Converter")
        tagline.setObjectName("aboutTagline")

        info_layout.addWidget(app_name)
        info_layout.addWidget(version_label)
        info_layout.addWidget(tagline)

        header_layout.addWidget(icon_label)
        header_layout.addSpacing(15)
        header_layout.addLayout(info_layout)

        layout.addLayout(header_layout)
        layout.addSpacing(10)

        # === Creator Info ===
        creator_group = QGroupBox("Creator")
        creator_layout = QVBoxLayout(creator_group)
        creator_layout.setSpacing(10)

        creator_name = QLabel("Created by <b>Avaxerrr</b>")
        creator_name.setObjectName("creatorName")

        creator_desc = QLabel(
            "A powerful, intuitive image converter supporting modern formats "
            "like WebP and AVIF with advanced compression options."
        )
        creator_desc.setObjectName("creatorDesc")
        creator_desc.setWordWrap(True)

        # Social/contact buttons
        links_layout = QHBoxLayout()

        github_btn = QPushButton("GitHub")
        github_btn.setObjectName("linkButton")
        github_btn.setIcon(QIcon(":/icons/info.svg"))
        github_btn.clicked.connect(lambda: self._open_url("https://github.com/Avaxerrr"))

        """""
        portfolio_btn = QPushButton("Portfolio")
        portfolio_btn.setObjectName("linkButton")
        portfolio_btn.setIcon(QIcon(":/icons/info.svg"))
        portfolio_btn.clicked.connect(lambda: self._open_url("https://your-portfolio.com"))
        """""

        links_layout.addWidget(github_btn)
        #links_layout.addWidget(portfolio_btn)
        links_layout.addStretch()

        creator_layout.addWidget(creator_name)
        creator_layout.addWidget(creator_desc)
        creator_layout.addLayout(links_layout)

        layout.addWidget(creator_group)

        # === Technology Stack ===
        tech_group = QGroupBox("Built With")
        tech_layout = QVBoxLayout(tech_group)
        tech_layout.setSpacing(5)

        tech_text = QTextBrowser()
        tech_text.setObjectName("techText")
        tech_text.setMaximumHeight(120)
        tech_text.setOpenExternalLinks(False)
        tech_text.setHtml("""
            <ul style="color: #CCCCCC; font-size: 12px; line-height: 1.6;">
                <li><b style="color: #4fc3f7;">PySide6 (Qt 6)</b> - Modern GUI framework</li>
                <li><b style="color: #4fc3f7;">Pillow (PIL)</b> - Image processing library</li>
                <li><b style="color: #4fc3f7;">pillow-avif-plugin</b> - AVIF format support</li>
                <li><b style="color: #4fc3f7;">Python 3.10+</b> - Programming language</li>
            </ul>
        """)

        tech_layout.addWidget(tech_text)
        layout.addWidget(tech_group)

        # === License and Copyright ===
        license_group = QGroupBox("License")
        license_layout = QVBoxLayout(license_group)

        license_text = QLabel(
            "© 2025 Avaxerrr. All rights reserved.\n\n"
            "This software is provided \"as is\" without warranty of any kind."
        )
        license_text.setObjectName("licenseText")
        license_text.setWordWrap(True)

        license_layout.addWidget(license_text)
        layout.addWidget(license_group)

        layout.addStretch()

        # Set content and add to main layout
        scroll.setWidget(content)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _open_url(self, url: str):
        """Open URL in default browser."""
        QDesktopServices.openUrl(QUrl(url))

    def load_from_controller(self):
        """No settings to load for about page."""
        pass

    def save_to_controller(self):
        """No settings to save for about page."""
        pass
