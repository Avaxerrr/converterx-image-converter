"""
Base Documentation Page

Abstract base class for read-only documentation pages.
All documentation pages inherit from this to maintain consistency.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame, QTextBrowser
from PySide6.QtCore import Qt
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.app_settings import AppSettingsController


# ============================================================================
# CENTRALIZED STYLING - Single source of truth for all doc pages
# ============================================================================
DOC_PAGE_STYLE = """
/* Documentation Content Browser */
QTextBrowser#docContent {
    background-color: #1e1e1e;
    border: none;
    color: #CCCCCC;
    font-size: 12px;
    selection-background-color: #264f78;
    selection-color: #ffffff;
}

/* Scroll Area */
QScrollArea {
    border: none;
    background-color: #1e1e1e;
}
"""


# ============================================================================
# Metaclass Fix for QWidget + ABC
# ============================================================================
class QWidgetABCMeta(type(QWidget), ABCMeta):
    """
    Combined metaclass for QWidget and ABC.
    Resolves metaclass conflict when inheriting from both QWidget and ABC.
    """
    pass


class BaseDocPage(QWidget, metaclass=QWidgetABCMeta):
    """
    Abstract base class for read-only documentation pages.

    Provides consistent structure for all documentation pages:
    - Scroll area setup
    - QTextBrowser for HTML content
    - Unified styling
    - No-op load/save methods (doc pages don't have settings)

    Subclasses only need to implement get_content() to return HTML string.

    Example:
        class MyDocPage(BaseDocPage):
            def get_content(self) -> str:
                return "<h1>My Documentation</h1><p>Content here...</p>"
    """

    def __init__(self, controller: 'AppSettingsController'):
        """
        Initialize base documentation page.

        Args:
            controller: AppSettingsController instance (injected dependency)
        """
        super().__init__()
        self.controller = controller
        self._setup_ui()
        self.setStyleSheet(DOC_PAGE_STYLE)

    def _setup_ui(self):
        """
        Setup UI structure - same for all doc pages.
        Creates scroll area with QTextBrowser displaying HTML content.
        """
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Create text browser for HTML content
        content = QTextBrowser()
        content.setObjectName("docContent")
        content.setOpenExternalLinks(False)  # Handle links manually if needed
        content.setHtml(self.get_content())  # Get HTML from subclass

        # Add margins to create spacing from edges
        content.document().setDocumentMargin(20)

        # Assemble layout
        scroll.setWidget(content)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    @abstractmethod
    def get_content(self) -> str:
        """
        Return HTML content for this documentation page.

        Must be implemented by subclass.

        Returns:
            HTML string with complete document structure (including <style> if needed)
        """
        pass

    def load_from_controller(self):
        """
        No-op for documentation pages.
        Documentation pages are read-only and don't load settings.
        """
        pass

    def save_to_controller(self):
        """
        No-op for documentation pages.
        Documentation pages are read-only and don't save settings.
        """
        pass


# ============================================================================
# Concrete Documentation Page Classes
# ============================================================================

class QuickGuidePage(BaseDocPage):
    """Quick start guide for new users."""

    def get_content(self) -> str:
        """Return HTML content for quick guide."""
        return """
        <style>
            body {
                color: #CCCCCC;
                font-size: 12px;
                line-height: 1.6;
            }
            h1 {
                color: #4fc3f7;
                font-size: 24px;
                font-weight: bold;
                margin-top: 0;
                margin-bottom: 20px;
                border-bottom: 2px solid #3e3e42;
                padding-bottom: 10px;
            }
            h2 {
                color: #4fc3f7;
                font-size: 18px;
                font-weight: 600;
                margin-top: 24px;
                margin-bottom: 12px;
            }
            p {
                margin: 8px 0;
                color: #CCCCCC;
            }
            ul, ol {
                margin: 8px 0;
                padding-left: 24px;
            }
            li {
                margin: 6px 0;
                color: #CCCCCC;
            }
            code {
                background-color: #2d2d30;
                color: #4fc3f7;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
            }
            .tip {
                background-color: #1e3a1e;
                border-left: 3px solid #4caf50;
                padding: 10px;
                margin: 10px 0;
                border-radius: 3px;
            }
        </style>
        
        <h1>Quick Guide</h1>
        
        <p>ConverterX converts images to modern formats like WebP and AVIF with advanced compression options.</p>
        
        <h2>1. Add Images</h2>
        <ul>
            <li>Click <b>"Add Images"</b> button</li>
            <li>Drag and drop files into the file list</li>
            <li>Right-click files for options (Open folder, Remove)</li>
        </ul>
        
        <p><b>Input formats:</b> JPEG, PNG, WebP, AVIF, BMP, TIFF, GIF, ICO</p>
        
        <h2>2. Preview</h2>
        <p>Click any image in the file list to view it. Three preview modes available:</p>
        <ul>
            <li><b>Preview</b> - Optimized thumbnail (fast)</li>
            <li><b>HD</b> - Full resolution</li>
            <li><b>Output Preview</b> - Shows final result with current settings</li>
        </ul>
        
        <h2>3. Choose Format & Quality</h2>
        
        <p><b>Output Formats:</b></p>
        <ul>
            <li><b>WebP</b> - Excellent compression, wide browser support</li>
            <li><b>AVIF</b> - Best compression, smaller files</li>
            <li><b>JPEG</b> - Universal compatibility</li>
            <li><b>PNG</b> - Lossless compression, supports transparency</li>
            <li><b>TIFF</b> - Archival format with multiple compression options</li>
            <li><b>GIF</b> - 256-color palette, supports animation</li>
            <li><b>ICO</b> - Windows icon format (16-256px)</li>
            <li><b>BMP</b> - Uncompressed bitmap (legacy compatibility)</li>
        </ul>
        
        <p><b>Quality Control:</b></p>
        <ul>
            <li><b>Quality Slider</b> - Simple quality control (0-100)</li>
            <li><b>Target File Size</b> - Automatically finds quality for specific file size</li>
            <li><b>Lossless</b> - Zero quality loss (WebP/AVIF/PNG only)</li>
        </ul>
        
        <h2>4. Resize (Optional)</h2>
        <p>Five resize modes available:</p>
        <ul>
            <li><b>None</b> - Keep original dimensions</li>
            <li><b>Scale by %</b> - Resize by percentage (e.g., 50% = half size)</li>
            <li><b>Fit to Width</b> - Resize to specific width, maintain aspect ratio</li>
            <li><b>Fit to Height</b> - Resize to specific height, maintain aspect ratio</li>
            <li><b>Fit to Dimensions</b> - Fit within max width × height box</li>
        </ul>
        
        <div class="tip">
            <b>Technical Note:</b> All resizing uses Lanczos resampling for high-quality results in both upscaling and downscaling.
        </div>
        
        <h2>5. Convert</h2>
        <ul>
            <li><b>Single file:</b> Select image → Click "Convert"</li>
            <li><b>Batch:</b> Add multiple files → Click "Convert All"</li>
            <li>Monitor batch progress with <code>Ctrl+B</code> (Batch Window)</li>
        </ul>
        
        <h2>Keyboard Shortcuts</h2>
        <ul>
            <li><code>F12</code> - Toggle Log window</li>
            <li><code>Ctrl+B</code> - Toggle Batch window</li>
        </ul>
        
        <p style="margin-top: 40px; color: #858585; font-size: 11px;">
            See the <b>Features</b> page for detailed information on advanced options.
        </p>
        """


class FeaturesPage(BaseDocPage):
    """Complete feature reference with format comparison."""

    def get_content(self) -> str:
        """Return HTML content for features documentation."""
        return """
        <style>
            body {
                color: #CCCCCC;
                font-size: 12px;
                line-height: 1.6;
            }
            h1 {
                color: #4fc3f7;
                font-size: 24px;
                font-weight: bold;
                margin-top: 0;
                margin-bottom: 20px;
                border-bottom: 2px solid #3e3e42;
                padding-bottom: 10px;
            }
            h2 {
                color: #4fc3f7;
                font-size: 18px;
                font-weight: 600;
                margin-top: 24px;
                margin-bottom: 12px;
            }
            h3 {
                color: #AAAAAA;
                font-size: 14px;
                font-weight: 600;
                margin-top: 16px;
                margin-bottom: 8px;
            }
            p {
                margin: 8px 0;
                color: #CCCCCC;
            }
            ul {
                margin: 8px 0;
                padding-left: 24px;
            }
            li {
                margin: 6px 0;
                color: #CCCCCC;
            }
            code {
                background-color: #2d2d30;
                color: #4fc3f7;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 12px 0;
            }
            th {
                background-color: #2d2d30;
                color: #4fc3f7;
                padding: 8px;
                text-align: left;
                border: 1px solid #3e3e42;
                font-size: 11px;
            }
            td {
                padding: 8px;
                border: 1px solid #3e3e42;
                color: #CCCCCC;
                font-size: 11px;
            }
            .feature-box {
                background-color: #252526;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 14px;
                margin: 12px 0;
            }
            .warning-box {
                background-color: #3a2a1e;
                border-left: 3px solid #ff9800;
                padding: 10px;
                margin: 10px 0;
                border-radius: 3px;
            }
        </style>
        
        <h1>Features</h1>
        
        <h2>Output Formats</h2>
        
        <table>
            <tr>
                <th>Format</th>
                <th>Compression</th>
                <th>Best For</th>
            </tr>
            <tr>
                <td><b>WebP</b></td>
                <td>30-50% smaller than JPEG</td>
                <td>General web use, modern browsers</td>
            </tr>
            <tr>
                <td><b>AVIF</b></td>
                <td>50-60% smaller than JPEG</td>
                <td>Maximum compression, bandwidth-critical</td>
            </tr>
            <tr>
                <td><b>JPEG</b></td>
                <td>Standard lossy</td>
                <td>Universal compatibility, photos</td>
            </tr>
            <tr>
                <td><b>PNG</b></td>
                <td>Lossless</td>
                <td>Graphics, logos, transparency</td>
            </tr>
            <tr>
                <td><b>TIFF</b></td>
                <td>LZW, JPEG, PackBits, or None</td>
                <td>Archival, printing, professional photography</td>
            </tr>
            <tr>
                <td><b>GIF</b></td>
                <td>LZW (256 colors max)</td>
                <td>Simple animations, legacy web graphics</td>
            </tr>
            <tr>
                <td><b>ICO</b></td>
                <td>Uncompressed (BMP-based)</td>
                <td>Windows application icons (max 256×256)</td>
            </tr>
            <tr>
                <td><b>BMP</b></td>
                <td>Uncompressed</td>
                <td>Legacy compatibility, Windows wallpapers</td>
            </tr>
        </table>
        
        <h2>Quality Control</h2>
        
        <div class="feature-box">
            <h3>Quality Slider Mode</h3>
            <ul>
                <li>Range: 0-100</li>
                <li>Higher = better quality, larger file</li>
                <li>Recommended: 80-90 for photos</li>
            </ul>
            
            <h3>Target File Size Mode</h3>
            <ul>
                <li>Set specific target size (e.g., 500 KB)</li>
                <li>Algorithm automatically finds optimal quality</li>
                <li>Tolerance: 5-20% (adjustable)</li>
            </ul>
            
            <h3>Lossless Mode</h3>
            <ul>
                <li>Zero quality loss compression</li>
                <li>Available for: WebP, AVIF, PNG</li>
                <li>Larger files than lossy compression</li>
            </ul>
        </div>
        
        <h2>Resize Options</h2>
        
        <table>
            <tr>
                <th>Mode</th>
                <th>Description</th>
            </tr>
            <tr>
                <td><b>None</b></td>
                <td>Keep original dimensions</td>
            </tr>
            <tr>
                <td><b>Scale by %</b></td>
                <td>Resize by percentage (e.g., 50%, 200%)</td>
            </tr>
            <tr>
                <td><b>Fit to Width</b></td>
                <td>Resize to specific width, calculate height</td>
            </tr>
            <tr>
                <td><b>Fit to Height</b></td>
                <td>Resize to specific height, calculate width</td>
            </tr>
            <tr>
                <td><b>Fit to Dimensions</b></td>
                <td>Fit within max width × height box</td>
            </tr>
        </table>
        
        <p><b>Resampling Algorithm:</b> Lanczos (high-quality for both upscaling and downscaling)</p>
        
        <h2>Format-Specific Options</h2>
        
        <div class="feature-box">
            <h3>WebP Settings</h3>
            <ul>
                <li><b>Method (0-6):</b> Compression method quality. Higher = better compression but slower. Default: 4</li>
                <li><b>Subsampling:</b> Chroma subsampling mode (4:4:4, 4:2:0, etc.)</li>
            </ul>
            
            <h3>AVIF Settings</h3>
            <ul>
                <li><b>Speed (0-10):</b> Encoding speed. Higher = faster but larger files. Default: 6</li>
                <li><b>Range:</b> Full or Limited color range</li>
            </ul>
            
            <h3>PNG Settings</h3>
            <ul>
                <li><b>Compression Level (0-9):</b> Higher = smaller files but slower. Default: 6</li>
            </ul>
            
            <h3>TIFF Settings</h3>
            <ul>
                <li><b>Compression:</b> None, LZW (lossless), JPEG (lossy), PackBits</li>
                <li><b>JPEG Quality:</b> Only when JPEG compression selected (1-100)</li>
                <li><b>Note:</b> JPEG compression requires RGB mode (converts palette images automatically)</li>
            </ul>
            
            <h3>GIF Settings</h3>
            <ul>
                <li><b>Optimize Palette:</b> Reduce file size by optimizing 256-color table</li>
                <li><b>Note:</b> Limited to 256 colors, may show dithering on photos</li>
            </ul>
            
            <h3>ICO Settings</h3>
            <ul>
                <li><b>Size:</b> 16-256 pixels (square icons only)</li>
                <li><b>Non-square images:</b> Pad with transparency or crop to center</li>
            </ul>
            
            <div class="warning-box">
                <b>⚠️ ICO Limitation:</b> Pillow supports up to 256×256 pixels (standard BMP-based ICO format). For larger icons, use PNG format instead.
            </div>
            
            <h3>BMP Settings</h3>
            <ul>
                <li>No compression options available (uncompressed format)</li>
            </ul>
        </div>
        
        <h2>Output Settings</h2>
        
        <div class="feature-box">
            <h3>Output Location</h3>
            <ul>
                <li><b>Same as Source:</b> Save in same folder as original</li>
                <li><b>Custom Folder:</b> Specify destination folder</li>
                <li><b>Ask Every Time:</b> Choose location for each conversion</li>
            </ul>
            
            <h3>Filename Templates</h3>
            <ul>
                <li><b>_converted:</b> photo.jpg → photo_converted.webp</li>
                <li><b>_{format}:</b> photo.jpg → photo_webp.webp</li>
                <li><b>_Q{quality}:</b> photo.jpg → photo_Q85.webp</li>
                <li><b>Custom:</b> Your own suffix</li>
            </ul>
            
            <p><b>Collision Handling:</b> Auto-increments filename if file exists (e.g., photo_converted_1.webp)</p>
        </div>
        
        <h2>Batch Processing</h2>
        
        <div class="feature-box">
            <ul>
                <li>Process multiple images with same settings</li>
                <li>Real-time progress tracking</li>
                <li>Pause/Resume/Cancel controls</li>
                <li>Statistics: Total files, success rate, space saved</li>
                <li>Toggle window: <code>Ctrl+B</code></li>
            </ul>
        </div>
        
        <h2>Preview Modes</h2>
        
        <div class="feature-box">
            <ul>
                <li><b>Preview:</b> Optimized thumbnail (max 1500px), cached for speed</li>
                <li><b>HD:</b> Full resolution, separate cache</li>
                <li><b>Output Preview:</b> Shows final result with quality/resize/lossless settings applied</li>
            </ul>
            
            <p><b>Note:</b> Output Preview excludes target file size mode and some advanced format options for performance.</p>
        </div>
        
        <h2>Application Settings</h2>
        
        <div class="feature-box">
            <p>Configure in App Settings dialog:</p>
            
            <ul>
                <li><b>Performance:</b> Max concurrent workers for batch processing</li>
                <li><b>Preview:</b> Cache sizes, max dimensions, debounce timing</li>
                <li><b>Defaults:</b> Default quality, format, and output settings</li>
            </ul>
        </div>
        
        <p style="margin-top: 40px; color: #858585; font-size: 11px;">
            All features are designed for speed and quality. Use Output Preview to compare settings before converting.
        </p>
        """