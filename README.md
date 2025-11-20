# ConverterX

![License](https://img.shields.io/badge/license-Apache%202.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![Platform](https://img.shields.io/badge/platform-Windows-blue)
![Privacy](https://img.shields.io/badge/privacy-100%25%20local-green)

## Screenshots

<p align="center">
  <img width="49%" alt="Batch Processing Window" src="https://github.com/user-attachments/assets/9b5f8b46-052a-47af-8c6b-028e81e9aa1c" />
  <img width="49%" alt="Format Selection & Settings" src="https://github.com/user-attachments/assets/d944a69e-685a-4323-857f-650037df1736" />
</p>

<p align="center">
  <img width="49%" alt="ConverterX Main Interface" src="https://github.com/user-attachments/assets/984207cf-6299-4191-9be8-87dbf7032695" />
  <img width="49%" alt="Real-Time Preview System" src="https://github.com/user-attachments/assets/35694890-9b4a-435f-813c-7c568d0c6b15" />
</p>

<p align="center">
  <em>Professional image conversion with privacy-first local processing</em>
</p>



**Professional image format converter with batch processing and real-time preview. 100% local processing - your images never leave your computer.**

---

## Privacy First

**Your images, your computer, your privacy.** All conversions happen entirely on your machine with zero cloud uploads, zero data collection, and zero internet requirements.

- 100% offline processing
- Zero cloud uploads
- No telemetry or tracking
- No account required
- Local preview generation
- Complete file control

Perfect for photographers, designers, healthcare professionals, legal teams, and anyone handling sensitive images.

---

## Overview

Feature-rich desktop image converter built with Python and PySide6. Convert images with advanced customization, real-time previews, and multi-threaded batch processing - all locally on your device.

## Features

### Format Support

**Input: 30+ formats**
- Common: JPEG, PNG, BMP, TIFF, GIF, WebP, AVIF, HEIF/HEIC
- Additional: PCX, PPM, PGM, PBM, SGI, TGA, ICO, CUR, and more

**Output: 8 formats**
- **JPEG** - Lossy compression with quality control
- **PNG** - Lossless compression with 10 levels
- **WebP** - Modern format with lossy/lossless modes
- **AVIF** - Next-gen format with advanced compression
- **TIFF** - Professional format with multiple compression options
- **GIF** - Animation support with palette optimization
- **BMP** - Uncompressed bitmap
- **ICO** - Windows icon format

### Batch Processing

Convert multiple images simultaneously with multi-threaded processing. Real-time progress tracking with pause, resume, and cancel controls. Configurable thread pool for optimal performance.

### Real-Time Preview

See your converted output before processing. Privacy-safe previews generated entirely on your device with three-tier caching for optimal performance. Toggle between original and output with zoom controls.

### Resize Options

Five modes: None, Scale by Percentage (10-100%), Fit by Width, Fit by Height, Fit to Dimensions. Optional upscaling prevention with pixel-perfect dimension control.

### Quality Control

- Quality slider (1-100) for lossy formats
- PNG compression levels (0-9)
- WebP lossless mode with method selection
- AVIF speed/range optimization
- TIFF compression (None, LZW, JPEG, PackBits)
- GIF palette optimization with dithering
- Target file size with iterative compression

### Output Management

**Location modes:** Same as Source, Custom Folder, Ask Every Time

**Filename templates:** Original + "_converted", Original + "_WebP" (format), Original + "_Q85" (quality), Custom suffix, Auto-increment prevention

---

## Why ConverterX?

### Privacy & Security

Unlike online converters that upload files to remote servers, ConverterX processes everything locally:

- **Sensitive documents** - Medical images, legal docs, ID scans stay on your device
- **Professional work** - Client photos, unreleased designs remain confidential
- **Personal photos** - Family photos never exposed to third parties
- **No data breaches** - Can't leak what isn't uploaded
- **GDPR compliant** - No data collection
- **Air-gapped operation** - Works on isolated systems

### Performance

- **Instant processing** - No upload/download delays
- **No file size limits** - Process any size image
- **Batch operations** - Convert hundreds without bandwidth constraints
- **No subscription fees** - Completely free
- **Works offline** - Convert anywhere, anytime

---

## Use Cases

- **Personal privacy** - Convert ID documents without tracking
- **Web optimization** - Convert to WebP/AVIF for 30-50% size reduction
- **Batch migration** - Convert entire libraries from legacy to modern formats
- **Icon generation** - Create ICO files with automatic square enforcement
- **Target file size** - Achieve specific sizes with iterative compression
- **HEIF/HEIC conversion** - Convert iPhone photos to universal formats

---

## Screenshots

*Coming soon*

---

## Format Comparison

| Format | Quality | Compression | Transparency | Animation | Best For |
|--------|---------|-------------|--------------|-----------|----------|
| JPEG | 1-100 | Lossy | No | No | Photos, web |
| PNG | 0-9 | Lossless | Yes | No | Graphics, screenshots |
| WebP | 1-100 | Both | Yes | Yes | Modern web |
| AVIF | 1-100 | Both | Yes | No | Next-gen web |
| HEIF/HEIC | Input only | - | - | - | iPhone photos |
| TIFF | Multiple | Multiple | Yes | No | Professional/print |
| GIF | Palette | Lossless | Yes | Yes | Simple animations |
| BMP | None | None | No | No | Uncompressed |
| ICO | None | None | Yes | No | Windows icons |

---

## Technical Stack

- **PySide6/Qt** - Cross-platform GUI framework
- **Pillow** - Image processing library
- **QThreadPool** - Multi-threaded conversion
- **QSettings** - Local configuration storage

**Key capabilities:** EXIF auto-rotation, color space conversion, memory-efficient streaming, binary search for target sizes, debounced preview generation, three-tier caching.

---

## Keyboard Shortcuts

- **F12** - Toggle log window
- **Ctrl+B** - Toggle batch window
- **Drag & Drop** - Add files

---

## Performance

**Threading:** 1-32 configurable threads (optimal: CPU core count)

**Caching:** Thumbnail, preview, and output preview caching - all local in-memory

**Memory:** Streaming for large files, automatic cleanup, configurable cache sizes

---

## License

Apache License Version 2.0 - see [LICENSE](https://github.com/Avaxerrr/converterx-image-converter?tab=Apache-2.0-1-ov-file) file.

---

## Support

- **Issues:** [GitHub Issues](https://github.com/Avaxerrr/converterx-image-converter/issues)
- **Documentation:** [Wiki](https://github.com/Avaxerrr/converterx-image-converter/wiki)
- **Discussions:** [GitHub Discussions](https://github.com/Avaxerrr/converterx-image-converter/discussions)
