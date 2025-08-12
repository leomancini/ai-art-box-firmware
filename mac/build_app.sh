#!/bin/bash

# Build script for AI Art Box Viewer macOS app

echo "Building AI Art Box Viewer macOS app..."

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Activate virtual environment and install dependencies
echo "Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Build the app
echo "Building app with py2app..."
python setup.py py2app

echo "Build complete!"
echo "Your app is located at: dist/AI Art Box Viewer.app"
echo ""
echo "To run the app:"
echo "  open 'dist/AI Art Box Viewer.app'"
echo ""
echo "To distribute:"
echo "  - Copy the .app folder to Applications"
echo "  - Or create a DMG for distribution"
