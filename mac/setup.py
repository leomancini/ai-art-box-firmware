from setuptools import setup
import os
import glob

# Get the directory containing this setup.py file
base_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(base_dir)  # Go up one level to the project root

# Get all image files from the parent directory
image_files = glob.glob(os.path.join(parent_dir, 'images', '*.png'))

APP = [os.path.join(parent_dir, 'image_viewer.py')]
DATA_FILES = [
    ('images', image_files),
    ('', [os.path.join(parent_dir, 'labels.json')]),
    ('', [os.path.join(base_dir, 'Mac App Icon.png')]),
]
OPTIONS = {
    'argv_emulation': False,  # Changed to False for better compatibility
    'iconfile': 'AI_Art_Box_Viewer.icns',  # Custom icon for the app
    'plist': {
        'CFBundleName': 'AI Art Box Viewer',
        'CFBundleDisplayName': 'AI Art Box Viewer',
        'CFBundleIdentifier': 'com.aiartbox.viewer',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13.0',
        'NSAppleEventsUsageDescription': 'This app needs to access files.',
    },
    'packages': ['pygame'],
    'includes': ['pathlib', 'argparse', 'json', 're', 'sys', 'os'],
    'excludes': ['tkinter', 'matplotlib', 'numpy'],
    'optimize': 0,
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
