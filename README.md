# AI Art Box Firmware

## Overview

The `on_device_firmware.py` creates an interactive art display system controlled by three 6-position rotary switches. It displays different images based on switch positions and includes an automatic screensaver mode for continuous viewing.

## How It Works

### Switch Control

- **Three switches** control which image to display
- Each switch has **six positions** (1-6)
- Creates **216 different combinations** (6×6×6)
- Images are named using the format `0-0-0.jpeg`, `1-2-3.jpeg`, etc.

### Image Display

- Shows images **fullscreen** on HDMI display
- **Intelligent caching** - stores recently viewed images in memory
- **Automatic scaling** - fits any image to the screen while maintaining aspect ratio
- **Smooth rendering** with consistent 30 FPS performance

### LCD Screen

- Displays current switch status and image information
- Shows **descriptive labels** when available
- Updates in real-time as switches are moved

## Operation Modes

The system operates in two distinct modes that provide different user experiences and functionality.

### Interactive Mode

Interactive mode is the primary operating state where user input directly controls the displayed content.

**Activation:**

- Automatically enters when any switch is moved
- Remains active as long as switches are being adjusted
- Default mode when the system first starts

**Behavior:**

- **Real-time response** - Image changes occur immediately when switches are moved
- **Direct control** - Each switch position directly corresponds to the displayed image
- **Exploration focused** - Users can systematically explore the image collection by adjusting switch positions

**Display Information:**

- LCD displays `*** INTER-ACTIVE ***` on the first line
- Shows current switch labels or positions on remaining lines
- Updates instantly to reflect any switch changes

**User Experience:**

- Provides immediate visual feedback for all switch movements
- Allows precise navigation through the image collection
- Enables users to find and display specific images quickly
- Perfect for guided tours, demonstrations, or interactive art experiences

### Screensaver Mode

Screensaver mode provides an automated viewing experience when the system is not being actively used.

**Activation:**

- **Automatic transition** occurs after 5 minutes of no switch movement
- **Seamless transition** from the current interactive image
- **Continuous operation** until user interaction resumes

**Behavior:**

- **Automatic cycling** through all 216 images in sequence
- **3-second intervals** between image changes for comfortable viewing
- **Sequential progression** from the current image position through the entire collection
- **Looping playback** - returns to the beginning after reaching the last image

**Display Information:**

- LCD displays `*** SCREEN-SAVER ***` on the first line
- Shows labels for the currently displayed image
- Updates with each image change to maintain context

**User Experience:**

- **Hands-free operation** - no user input required
- **Continuous entertainment** - provides ongoing visual interest
- **Discovery element** - users may see images they haven't explored manually
- **Ambient display** - creates an engaging background for spaces

**Mode Transition:**

- **Immediate return** to interactive mode with any switch movement
- **Preserves context** - resumes from the last manually selected image
- **Smooth handoff** - no interruption or delay in the transition

## Hardware Requirements

### Components

- **Three rotary switches** (6 positions each)
- **I2C multiplexer** for device communication
- **LCD display** for status information
- **Raspberry Pi** or compatible single-board computer

### Connections

- Switches connect via **I2C expanders**
- LCD operates on **channel 3**
- All devices communicate through the **multiplexer**

## File Structure

```
images/
├── 0-0-0.jpeg    ← Switch positions 1-1-1
├── 0-0-1.jpeg    ← Switch positions 1-1-2
├── ...
├── 5-5-5.jpeg    ← Switch positions 6-6-6
└── labels.json   ← Optional descriptive labels
```

## Labels Configuration

Add a `labels.json` file to display descriptive text:

```json
{
  "first": ["Red", "Blue", "Green", "Yellow", "Purple", "Orange"],
  "second": ["Small", "Medium", "Large", "Tiny", "Huge", "Normal"],
  "third": ["Circle", "Square", "Triangle", "Star", "Heart", "Diamond"]
}
```

## Usage

```bash
# Fullscreen mode (default)
python3 on_device_firmware.py

# Windowed mode (for testing)
python3 on_device_firmware.py --windowed

# Custom image directory
python3 on_device_firmware.py --images /path/to/images
```

## Controls

- **ESC** - Exit the application
- **F11** - Toggle fullscreen/windowed mode
- **Switch movement** - Change displayed images

## Features

### Memory Management

- **Caches 25 images** for improved loading performance
- **LRU eviction** removes least recently used images
- **Efficient memory usage** maintains smooth operation

### Error Handling

- **Missing images** display appropriate error messages
- **Hardware failures** are handled gracefully
- **Clean shutdown** ensures proper resource cleanup

### Performance

- **30 FPS** consistent display refresh rate
- **50ms switch polling** for responsive control
- **Thread-safe operation** prevents hardware conflicts
