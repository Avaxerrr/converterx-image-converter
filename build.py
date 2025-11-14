"""
Nuitka Build Script for ConverterX

Builds a standalone folder distribution for faster startup.
"""

import subprocess
import sys
import platform
import shutil
from pathlib import Path

def build():
    """Build ConverterX with Nuitka in standalone mode."""

    print("=" * 60)
    print("Building ConverterX with Nuitka (Standalone Mode)...")
    print("=" * 60)

    # Clean previous build
    dist_dir = Path("dist")
    if dist_dir.exists():
        print("\nCleaning previous build...")
        shutil.rmtree(dist_dir)

    # Common arguments for all platforms
    common_args = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--enable-plugin=pyside6",
        "--include-data-file=theme.qss=theme.qss",
        "--include-data-file=resources_rc.py=resources_rc.py",
        "--include-package=pillow_avif",
        "--nofollow-import-to=tkinter",
        "--nofollow-import-to=matplotlib",
        "--nofollow-import-to=numpy",
        "--output-dir=dist",
        "--remove-output",
    ]

    # Platform-specific arguments
    if platform.system() == "Windows":
        platform_args = [
            "--windows-icon-from-ico=app_icon.ico",
            "--company-name=Avaxerrr",
            "--product-name=ConverterX",
            "--file-version=1.0.0",
            "--product-version=1.0.0",
            "--file-description=Modern Image Format Converter",
            "--copyright=Copyright (c) 2025 Avaxerrr",
            "--windows-console-mode=disable",
        ]
        exe_name = "main.exe"
        final_name = "ConverterX.exe"
    elif platform.system() == "Darwin":  # macOS
        platform_args = [
            "--macos-app-icon=app_icon.icns",
            "--macos-app-name=ConverterX",
            "--macos-app-version=1.0.0",
        ]
        exe_name = "main.bin"
        final_name = "ConverterX"
    else:  # Linux
        platform_args = [
            "--linux-icon=app_icon.png",
        ]
        exe_name = "main.bin"
        final_name = "ConverterX"

    # Entry point
    entry_point = ["main.py"]

    # Build command
    cmd = common_args + platform_args + entry_point

    print("\nRunning Nuitka with the following command:")
    print(" ".join(cmd))
    print("\nThis may take 3-5 minutes...\n")

    try:
        result = subprocess.run(cmd, check=True)
        print("\n" + "=" * 60)
        print("✓ Build completed successfully!")
        print("=" * 60)

        # Rename executable
        exe_path = dist_dir / "main.dist" / exe_name
        final_path = dist_dir / "main.dist" / final_name

        if exe_path.exists() and exe_path != final_path:
            exe_path.rename(final_path)
            print(f"\n✓ Renamed {exe_name} → {final_name}")

        # Show output info
        if final_path.exists():
            folder_size = sum(f.stat().st_size for f in (dist_dir / "main.dist").rglob('*') if f.is_file())
            print(f"\nDistribution folder: {(dist_dir / 'main.dist').absolute()}")
            print(f"Executable: {final_path.absolute()}")
            print(f"Total size: {folder_size / (1024*1024):.2f} MB")

            # Count files
            file_count = len(list((dist_dir / "main.dist").rglob('*')))
            print(f"Total files: {file_count}")

        print("\n" + "=" * 60)
        print("Distribution is ready for deployment!")
        print("=" * 60)
        print("\nTo distribute:")
        print("  1. Zip the entire 'dist/main.dist' folder")
        print("  2. Or create an installer with Inno Setup / NSIS")

        return 0

    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 60)
        print("✗ Build failed!")
        print("=" * 60)
        print(f"Error: {e}")
        return 1

    except FileNotFoundError:
        print("\n" + "=" * 60)
        print("✗ Nuitka not found!")
        print("=" * 60)
        print("Please install Nuitka first:")
        print("  pip install nuitka")
        return 1


if __name__ == "__main__":
    sys.exit(build())
