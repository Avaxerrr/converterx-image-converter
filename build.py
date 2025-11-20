"""
Nuitka Build Script for ConverterX

Builds either a single executable file or standalone folder distribution.
"""

import subprocess
import sys
import platform
import shutil
from pathlib import Path


def get_build_mode():
    """Prompt user to choose build mode."""
    print("=" * 60)
    print("ConverterX Build Configuration")
    print("=" * 60)
    print("\nChoose build mode:")
    print("  1. One-File  - Single executable (slower startup, easier to distribute)")
    print("  2. Standalone - Folder with dependencies (faster startup, larger)")
    print("=" * 60)

    while True:
        choice = input("\nEnter your choice (1 or 2): ").strip()
        if choice == "1":
            return "onefile"
        elif choice == "2":
            return "standalone"
        else:
            print("Invalid choice. Please enter 1 or 2.")


def build(mode):
    """Build ConverterX with Nuitka in specified mode."""

    print("\n" + "=" * 60)
    print(f"Building ConverterX with Nuitka ({mode.upper()} mode)...")
    print("=" * 60)

    # Clean previous build
    dist_dir = Path("dist")
    if dist_dir.exists():
        print("\nCleaning previous build...")
        shutil.rmtree(dist_dir)

    # Common arguments for all platforms
    common_args = [
        sys.executable, "-m", "nuitka",
        "--enable-plugin=pyside6",

        # Include resource files
        "--include-data-file=assets.py=assets.py",

        # Include required packages
        "--include-package=pillow_avif",
        "--include-package=psutil",

        # Follow these imports (ensure they're included)
        "--follow-import-to=PIL",

        # Don't follow these imports (reduce bloat)
        "--nofollow-import-to=tkinter",
        "--nofollow-import-to=matplotlib",
        "--nofollow-import-to=numpy",
        "--nofollow-import-to=scipy",
        "--nofollow-import-to=pandas",
        "--nofollow-import-to=test",
        "--nofollow-import-to=tests",

        # Output settings
        "--output-dir=dist",
        "--remove-output",

        # Optimization
        "--assume-yes-for-downloads",
    ]

    # Add mode-specific argument
    if mode == "onefile":
        common_args.append("--onefile")
    else:  # standalone
        common_args.append("--standalone")

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

    if mode == "onefile":
        print("\nThis may take 5-10 minutes (one-file builds are slower)...\n")
    else:
        print("\nThis may take 3-5 minutes...\n")

    try:
        result = subprocess.run(cmd, check=True)
        print("\n" + "=" * 60)
        print("✓ Build completed successfully!")
        print("=" * 60)

        # Handle output based on mode
        if mode == "onefile":
            # One-file mode: single executable in dist/
            exe_path = dist_dir / exe_name
            final_path = dist_dir / final_name

            if exe_path.exists() and exe_path != final_path:
                exe_path.rename(final_path)
                print(f"\n✓ Renamed {exe_name} → {final_name}")

            if final_path.exists():
                exe_size = final_path.stat().st_size
                print(f"\nExecutable: {final_path.absolute()}")
                print(f"Size: {exe_size / (1024*1024):.2f} MB")

                print("\n" + "=" * 60)
                print("Single executable is ready!")
                print("=" * 60)
                print("\nTo distribute:")
                print(f"  - Just share the '{final_name}' file")
                print("  - Users can run it directly (no installation needed)")

        else:  # standalone
            # Standalone mode: folder with dependencies
            exe_path = dist_dir / "main.dist" / exe_name
            final_path = dist_dir / "main.dist" / final_name

            if exe_path.exists() and exe_path != final_path:
                exe_path.rename(final_path)
                print(f"\n✓ Renamed {exe_name} → {final_name}")

            if final_path.exists():
                folder_size = sum(f.stat().st_size for f in (dist_dir / "main.dist").rglob('*') if f.is_file())
                print(f"\nDistribution folder: {(dist_dir / 'main.dist').absolute()}")
                print(f"Executable: {final_path.absolute()}")
                print(f"Total size: {folder_size / (1024*1024):.2f} MB")

                # Count files
                file_count = len(list((dist_dir / "main.dist").rglob('*')))
                print(f"Total files: {file_count}")

                print("\n" + "=" * 60)
                print("Distribution folder is ready!")
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
    mode = get_build_mode()
    sys.exit(build(mode))
