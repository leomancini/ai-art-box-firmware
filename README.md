# AI Art Box Firmware - Technical Documentation

## Overview

The `on_device_firmware.py` is a sophisticated Python application that creates an interactive art display system controlled by three 6-position rotary switches. It combines hardware I2C communication, LCD display management, and fullscreen image viewing to create an engaging user experience.

## System Architecture

The firmware consists of two main classes that work together:

### 1. SwitchController Class
Handles all hardware communication and LCD display management.

### 2. AIArtBoxDisplay Class  
Manages the fullscreen display, image rendering, and user interaction logic.

## Hardware Configuration

### I2C Multiplexer Setup
- **Multiplexer**: PCA9548A at address `0x70`
- **Bus**: SMBus(1) with thread-safe channel selection
- **Channel Lock**: Prevents concurrent access conflicts

### Switch Configuration
Three 6-position rotary switches connected via PCF8574 I/O expanders:

| Switch | Channel | Address | Purpose |
|--------|---------|---------|---------|
| SWITCH_1 | 1 | 0x24 | Controls first digit (0-5) |
| SWITCH_2 | 2 | 0x24 | Controls second digit (0-5) |
| SWITCH_3 | 0 | 0x24 | Controls third digit (0-5) |

### LCD Display
- **Type**: 20x4 Character LCD with PCF8574 backpack
- **Channel**: 3 (SD3)
- **Address**: 0x27
- **Purpose**: Shows current switch positions and descriptive labels

## Switch Position Decoding

The firmware decodes 6-position switch states from PCF8574 data:

```python
position_map = {
    0xFE: 1,  # P0 low
    0xFD: 2,  # P1 low  
    0xFB: 3,  # P2 low
    0xF7: 4,  # P3 low
    0xEF: 5,  # P4 low
    0xDF: 6,  # P5 low
}
```

Switch positions (1-6) are converted to image coordinates (0-5) by subtracting 1.

## Image Naming Convention

Images are named using the format: `{switch1-1}-{switch2-1}-{switch3-1}.jpeg`

Examples:
- Switch positions 1-1-1 → Image: `0-0-0.jpeg`
- Switch positions 3-2-6 → Image: `2-1-5.jpeg`
- Switch positions 6-6-6 → Image: `5-5-5.jpeg`

This creates a 6×6×6 = 216 image coordinate space.

## Labels System

The firmware supports descriptive labels via a `labels.json` file:

```json
{
  "first": ["Label1", "Label2", "Label3", "Label4", "Label5", "Label6"],
  "second": ["Label1", "Label2", "Label3", "Label4", "Label5", "Label6"],
  "third": ["Label1", "Label2", "Label3", "Label4", "Label5", "Label6"]
}
```

Labels are displayed on both the LCD and as an overlay on the fullscreen display.

## Operation Modes

### 1. Interactive Mode (Normal)
- **Trigger**: Any switch movement
- **Behavior**: Display follows switch positions exactly
- **LCD Display**: Shows "*** INTER-ACTIVE ***" with current labels
- **Image**: Shows image corresponding to current switch positions

### 2. Screensaver Mode
- **Trigger**: 5 minutes of inactivity
- **Behavior**: Automatically cycles through all 216 images
- **Cycle Interval**: 3 seconds per image
- **LCD Display**: Shows "*** SCREEN-SAVER ***" with current image labels
- **Exit**: Any switch movement returns to interactive mode

## Image Management

### Caching System
- **LRU Cache**: Least Recently Used eviction policy
- **Cache Size**: Maximum 25 images to manage memory usage
- **Benefits**: Faster image loading for recently viewed images
- **Memory Management**: Automatically evicts least-used images when cache is full

### Image Scaling
- **Aspect Ratio**: Maintained during scaling
- **Fit Strategy**: Images are scaled to fit screen while preserving aspect ratio
- **Centering**: Images are centered on screen
- **Background**: Black background for any unused screen space

### Error Handling
- **Missing Images**: Displays error message with filename
- **Load Failures**: Graceful fallback with error logging
- **Cache Management**: Automatic cleanup on exit

## Threading Architecture

### Background Switch Monitoring
- **Thread**: Daemon thread for continuous switch monitoring
- **Polling Rate**: 50ms intervals for responsive detection
- **Thread Safety**: Channel lock prevents I2C conflicts
- **Change Detection**: Only updates when switch positions actually change

### Main Display Loop
- **Frame Rate**: 30 FPS
- **Event Handling**: Pygame events (keyboard, window resize)
- **Mode Transitions**: Seamless switching between interactive and screensaver modes

## LCD Display Management

### Channel Management
- **Exclusive Access**: Channel lock ensures only one device accesses I2C at a time
- **Channel Selection**: Automatic switching between devices
- **Error Recovery**: Graceful handling of communication failures

### Display Modes
1. **Initialization**: Shows "*** INITIALIZING ***"
2. **Interactive**: Shows "*** INTER-ACTIVE ***" with switch labels
3. **Screensaver**: Shows "*** SCREEN-SAVER ***" with image labels

### Text Formatting
- **Truncation**: Labels truncated to 20 characters (LCD width)
- **Positioning**: 4-line display with proper spacing
- **Fallback**: Shows switch positions if no labels available

## User Interface Features

### Keyboard Controls
- **ESC**: Exit application
- **F11**: Toggle fullscreen/windowed mode (for testing)

### Visual Feedback
- **Label Overlay**: Translucent overlay in top-left corner
- **Missing Image Display**: Clear error messages for missing files
- **Switch Position Display**: Shows current switch positions on error screens

## Performance Optimizations

### Memory Management
- **Image Caching**: LRU cache reduces disk I/O
- **Surface Conversion**: `convert_alpha()` for optimal rendering
- **Cache Eviction**: Automatic cleanup prevents memory leaks

### Rendering Efficiency
- **Smooth Scaling**: High-quality image scaling
- **Frame Rate Control**: Consistent 30 FPS
- **Event-Driven Updates**: Only re-render when necessary

## Error Handling and Robustness

### Hardware Failures
- **I2C Communication**: Graceful handling of bus errors
- **LCD Failures**: Application continues without LCD
- **Switch Reading**: Continues operation with last known positions

### Software Failures
- **Image Loading**: Fallback display for missing/corrupt images
- **Label Loading**: Graceful degradation to numeric display
- **Thread Safety**: Proper locking prevents race conditions

## Configuration and Setup

### Command Line Arguments
```bash
python3 on_device_firmware.py [--images /path/to/images] [--windowed]
```

- `--images`: Directory containing image files (default: `/home/fcc-010/Desktop/ai-art-box-firmware/images`)
- `--windowed`: Run in windowed mode instead of fullscreen (for testing)

### File Structure Requirements
```
images/
├── 0-0-0.jpeg
├── 0-0-1.jpeg
├── ...
├── 5-5-5.jpeg
└── labels.json (optional)
```

### Dependencies
- `pygame`: Display and rendering
- `RPLCD`: LCD communication
- `smbus`: I2C communication
- Standard Python libraries: `threading`, `json`, `pathlib`, etc.

## Initialization Sequence

1. **Hardware Setup**: Initialize I2C bus and LCD
2. **Switch Monitoring**: Start background thread
3. **Label Loading**: Load and validate labels.json
4. **Display Setup**: Initialize pygame in fullscreen mode
5. **Image Cache**: Initialize LRU cache
6. **Initial Render**: Display first image
7. **Main Loop**: Begin event processing and mode management

## Shutdown Sequence

1. **Stop Monitoring**: Terminate switch monitoring thread
2. **Clear LCD**: Clear display and show shutdown message
3. **Clear Cache**: Free all cached image surfaces
4. **Pygame Cleanup**: Proper pygame shutdown
5. **Resource Cleanup**: Release all system resources

## Technical Specifications

- **Image Format**: JPEG files
- **Coordinate Space**: 6×6×6 = 216 unique positions
- **Display Modes**: Fullscreen (default) or windowed
- **Frame Rate**: 30 FPS
- **Cache Size**: 25 images maximum
- **Inactivity Timeout**: 5 minutes
- **Screensaver Interval**: 3 seconds per image
- **Switch Polling**: 50ms intervals
- **LCD Update Rate**: On-demand (when switches change or screensaver cycles)

This firmware creates a robust, interactive art display system that seamlessly combines hardware control with sophisticated image management and user experience features.
