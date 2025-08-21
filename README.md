# AI Art Box Firmware

## 🚀 Overview

The `on_device_firmware.py` creates an interactive art display controlled by three 6-position switches! 🎛️ It shows different images based on switch positions and has a cool screensaver mode. 📺✨

## 🔧 How It Works

### 🎮 Switch Control

- **3 switches** control which image to show
- Each switch has **6 positions** (1-6)
- Creates **216 different combinations** (6×6×6)
- Images are named like `0-0-0.jpeg`, `1-2-3.jpeg`, etc.

### 🖼️ Image Display

- Shows images **fullscreen** on HDMI display
- **Smart caching** - remembers recently viewed images
- **Auto-scaling** - fits any image to your screen
- **Smooth transitions** between images

### 📱 LCD Screen

- Shows what the switches are doing
- Displays **descriptive labels** (if you have them)
- Updates in real-time as you move switches

## 🎯 Two Modes

### 🎪 Interactive Mode

- **Move any switch** → image changes instantly
- LCD shows "**_ INTER-ACTIVE _**"
- Perfect for exploring your art collection

### 🌟 Screensaver Mode

- **5 minutes of no movement** → automatic slideshow
- Cycles through all 216 images every 3 seconds
- LCD shows "**_ SCREEN-SAVER _**"
- **Move any switch** → back to interactive mode

## 🏗️ Hardware Setup

### 🔌 What You Need

- **3 rotary switches** (6 positions each)
- **I2C multiplexer** to connect everything
- **LCD display** to show current status
- **Raspberry Pi** or similar computer

### 📋 Connections

- Switches connect via **I2C expanders**
- LCD on **channel 3**
- Everything talks through the **multiplexer**

## 📁 File Organization

```
images/
├── 0-0-0.jpeg    ← Switch positions 1-1-1
├── 0-0-1.jpeg    ← Switch positions 1-1-2
├── ...
├── 5-5-5.jpeg    ← Switch positions 6-6-6
└── labels.json   ← Optional descriptive labels
```

## 🎨 Labels (Optional)

Add a `labels.json` file to show nice descriptions:

```json
{
  "first": ["Red", "Blue", "Green", "Yellow", "Purple", "Orange"],
  "second": ["Small", "Medium", "Large", "Tiny", "Huge", "Normal"],
  "third": ["Circle", "Square", "Triangle", "Star", "Heart", "Diamond"]
}
```

## 🚀 Running It

```bash
# Fullscreen mode (default)
python3 on_device_firmware.py

# Windowed mode (for testing)
python3 on_device_firmware.py --windowed

# Custom image folder
python3 on_device_firmware.py --images /path/to/images
```

## ⌨️ Controls

- **ESC** - Exit the program
- **F11** - Toggle fullscreen/windowed mode
- **Move switches** - Change images instantly

## 🧠 Smart Features

### 💾 Memory Management

- **Caches 25 images** for fast loading
- **Forgets old images** to save memory
- **Smooth performance** even with lots of images

### 🛡️ Error Handling

- **Missing images** → shows error message
- **Hardware problems** → keeps working
- **Graceful shutdown** → cleans up everything

### ⚡ Performance

- **30 FPS** smooth display
- **50ms switch polling** for instant response
- **Thread-safe** - no conflicts between hardware and display

## 🎯 The Magic

This firmware turns your switches into a **magic remote control** for your art gallery! 🎨✨

- **Turn switches** → instantly see different art
- **Walk away** → enjoy automatic slideshow
- **Come back** → pick up right where you left off

Perfect for interactive art installations, galleries, or just showing off your digital art collection! 🎭🎪
