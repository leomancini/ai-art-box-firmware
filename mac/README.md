# macOS App Build

This directory contains all the files needed to build the AI Art Box Viewer as a macOS `.app` bundle.

## Files

- `setup.py` - py2app configuration for building the macOS app
- `requirements.txt` - Python dependencies needed for the build
- `build_app.sh` - Automated build script
- `dist/` - Contains the built app (created after building)
- `build/` - Build artifacts (created during build)
- `venv/` - Virtual environment with dependencies

## Building the App

1. **Navigate to this directory:**
   ```bash
   cd mac
   ```

2. **Run the build script:**
   ```bash
   ./build_app.sh
   ```

3. **The app will be created at:**
   ```
   dist/AI Art Box Viewer.app
   ```

## Running the App

- Double-click `dist/AI Art Box Viewer.app` in Finder
- Or run: `open "dist/AI Art Box Viewer.app"`

## Distribution

- Copy the `.app` folder to Applications
- Or create a DMG for distribution to other users

## Requirements

- macOS 10.13 (High Sierra) or later
- Python 3.12+ (automatically handled by the virtual environment)
