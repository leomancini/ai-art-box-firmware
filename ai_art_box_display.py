#!/usr/bin/env python3

"""
AI Art Box Display Controller
Combines pygame image viewer with switch monitoring to create a fullscreen
HDMI display controlled by three 6-position switches.

Switch 1 controls first digit (0-5)
Switch 2 controls second digit (0-5) 
Switch 3 controls third digit (0-5)

Images are displayed as {switch1-1}-{switch2-1}-{switch3-1}.png
"""

from __future__ import annotations

import sys
import time
import threading
import json
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Any
import smbus

import pygame
from RPLCD.i2c import CharLCD

# I2C multiplexer setup
bus = smbus.SMBus(1)
channel_lock = threading.Lock()

def load_labels_file(path: Path) -> Optional[Dict[str, List[str]]]:
    """Load labels from JSON file"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate structure
        if isinstance(data, dict) and all(
            key in data and isinstance(data[key], list) and len(data[key]) == 6
            for key in ["first", "second", "third"]
        ):
            return data
        else:
            print(f"Invalid labels file structure in {path}")
            return None
    except Exception as e:
        print(f"Error loading labels file {path}: {e}")
        return None

class SwitchController:
    """Handles reading the three 6-position switches via I2C multiplexer"""
    
    def __init__(self, labels_file: Optional[Path] = None):
        # Switch device configuration from switch_monitor.py
        self.devices = [
            {"name": "SWITCH_3", "channel": 0, "address": 0x24, "type": "Switch Controller"},
            {"name": "SWITCH_1", "channel": 1, "address": 0x24, "type": "Switch Controller"},
            {"name": "SWITCH_2", "channel": 2, "address": 0x24, "type": "Switch Controller"},
        ]
        
        # Current switch positions (1-6, converted to 0-5 for image filenames)
        self.switch_positions = {"SWITCH_1": 1, "SWITCH_2": 1, "SWITCH_3": 1}
        self.last_values = {}
        self.running = True
        
        # Load labels
        self.labels = None
        if labels_file and labels_file.exists():
            self.labels = load_labels_file(labels_file)
            print(f"Loaded labels from {labels_file}")
        else:
            print("No labels file found, using switch positions only")
        
        # Initialize LCD on channel 3 (same as switch_monitor)
        self.lcd = None
        self._init_lcd()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_switches, daemon=True)
        self.monitor_thread.start()
    
    def select_channel(self, channel):
        """Select which channel of the PCA9548A multiplexer to use"""
        channel_values = {0: 0x01, 1: 0x02, 2: 0x04, 3: 0x08, 4: 0x10, 5: 0x20, 6: 0x40, 7: 0x80}
        try:
            bus.write_byte(0x70, channel_values[channel])
            time.sleep(0.01)
            return True
        except Exception as e:
            return False

    def read_device(self, channel, address):
        """Read data from a specific device"""
        try:
            if not self.select_channel(channel):
                return None
            data = bus.read_byte(address)
            return data
        except Exception as e:
            return None

    def decode_switch_position(self, data):
        """Decode 6-position switch from PCF8574 data"""
        position_map = {
            0xFE: 1,  # P0 low
            0xFD: 2,  # P1 low  
            0xFB: 3,  # P2 low
            0xF7: 4,  # P3 low
            0xEF: 5,  # P4 low
            0xDF: 6,  # P5 low
        }
        return position_map.get(data, None)
    
    def _init_lcd(self):
        """Initialize LCD on channel 3"""
        try:
            with channel_lock:
                if self.select_channel(3):  # LCD is on channel 3 (SD3)
                    self.lcd = CharLCD('PCF8574', 0x27)
                    self.lcd.clear()
                    print("✓ LCD initialized successfully")
                    return True
        except Exception as e:
            print(f"LCD init error: {e}")
            return False
        return False
    
    def _update_lcd_display(self):
        """Update LCD with current switch labels"""
        try:
            if self.lcd is None:
                return False
            
            with channel_lock:
                if not self.select_channel(3):  # LCD is on channel 3 (SD3)
                    return False
                
                self.lcd.clear()
                
                # Line 1: Title
                self.lcd.cursor_pos = (0, 0)
                self.lcd.write_string("AI Art Box Display")
                
                if self.labels:
                    # Show descriptive labels
                    labels_text = [
                        self.labels['first'][self.switch_positions['SWITCH_1'] - 1],
                        self.labels['second'][self.switch_positions['SWITCH_2'] - 1], 
                        self.labels['third'][self.switch_positions['SWITCH_3'] - 1],
                    ]
                    
                    for i, text in enumerate(labels_text):
                        self.lcd.cursor_pos = (i + 1, 0)
                        self.lcd.write_string(text[:20])  # Truncate to LCD width
                else:
                    # Show switch positions
                    self.lcd.cursor_pos = (1, 0)
                    self.lcd.write_string(f"SW1: Pos {self.switch_positions['SWITCH_1']}")
                    self.lcd.cursor_pos = (2, 0)
                    self.lcd.write_string(f"SW2: Pos {self.switch_positions['SWITCH_2']}")
                    self.lcd.cursor_pos = (3, 0)
                    self.lcd.write_string(f"SW3: Pos {self.switch_positions['SWITCH_3']}")
                
            return True
        except Exception as e:
            print(f"LCD update error: {e}")
            return False

    def _monitor_switches(self):
        """Monitor all switches in background thread"""
        print("Starting switch monitoring...")
        
        # Initial LCD update
        self._update_lcd_display()
        
        while self.running:
            changes_detected = False
            
            with channel_lock:
                for dev in self.devices:
                    data = self.read_device(dev['channel'], dev['address'])
                    dev_key = f"ch{dev['channel']}_0x{dev['address']:02X}"
                    
                    if data is not None:
                        # Check if value changed
                        if dev_key in self.last_values and self.last_values[dev_key] != data:
                            changes_detected = True
                        
                        self.last_values[dev_key] = data
                        
                        # Decode position and update if valid
                        position = self.decode_switch_position(data)
                        if position is not None:
                            old_pos = self.switch_positions[dev['name']]
                            if old_pos != position:
                                print(f"{dev['name']}: {old_pos} -> {position}")
                                self.switch_positions[dev['name']] = position
                                changes_detected = True
            
            # Update LCD when changes detected
            if changes_detected:
                self._update_lcd_display()
            
            time.sleep(0.1)
    
    def get_image_coordinates(self) -> Tuple[int, int, int]:
        """Get current image coordinates (0-5) based on switch positions (1-6)"""
        return (
            self.switch_positions["SWITCH_1"] - 1,  # Convert 1-6 to 0-5
            self.switch_positions["SWITCH_2"] - 1,
            self.switch_positions["SWITCH_3"] - 1
        )
    
    def stop(self):
        """Stop the switch monitoring"""
        self.running = False
        # Clear LCD on exit
        try:
            if self.lcd is not None:
                with channel_lock:
                    self.select_channel(3)
                    self.lcd.clear()
        except:
            pass


class AIArtBoxDisplay:
    """Fullscreen pygame display controlled by switches"""
    
    def __init__(self, images_directory: Path, fullscreen: bool = True, labels_file: Optional[Path] = None):
        self.images_directory = images_directory
        self.fullscreen = fullscreen
        
        # Initialize switch controller with labels
        self.switch_controller = SwitchController(labels_file=labels_file)
        
        # Current image coordinates
        self.current_coords = (0, 0, 0)
        
        # Pygame setup
        pygame.init()
        pygame.display.set_caption("AI Art Box Display")
        
        if fullscreen:
            # Get display info for fullscreen
            display_info = pygame.display.Info()
            self.screen_width = display_info.current_w
            self.screen_height = display_info.current_h
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
        else:
            # Window mode for testing
            self.screen_width = 1920
            self.screen_height = 1080
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 48)
        
        # Image cache
        self.surface_cache: Dict[Path, pygame.Surface] = {}
        
        print(f"Display initialized: {self.screen_width}x{self.screen_height}")
        print(f"Fullscreen: {fullscreen}")
        
        # Initial render
        self._render()

    def _current_filename(self) -> str:
        """Generate filename based on current coordinates"""
        return f"{self.current_coords[0]}-{self.current_coords[1]}-{self.current_coords[2]}.png"

    def _current_image_path(self) -> Path:
        """Get path to current image"""
        return self.images_directory / self._current_filename()

    def _load_surface(self, path: Path) -> Optional[pygame.Surface]:
        """Load and cache image surface"""
        if path in self.surface_cache:
            return self.surface_cache[path]
        
        if not path.exists():
            return None
        
        try:
            surface = pygame.image.load(str(path)).convert_alpha()
            self.surface_cache[path] = surface
            return surface
        except Exception as exc:
            print(f"Failed to load image '{path}': {exc}", file=sys.stderr)
            return None

    def _render(self):
        """Render current image fullscreen"""
        self.screen.fill((0, 0, 0))  # Black background
        
        image_path = self._current_image_path()
        surface = self._load_surface(image_path)
        
        if surface is None:
            # Show error message if image not found
            message = f"Missing: {image_path.name}"
            text_surface = self.font.render(message, True, (255, 255, 255))
            rect = text_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            self.screen.blit(text_surface, rect)
            
            # Show switch positions
            pos_message = f"Switches: {self.switch_controller.switch_positions['SWITCH_1']}-{self.switch_controller.switch_positions['SWITCH_2']}-{self.switch_controller.switch_positions['SWITCH_3']}"
            pos_surface = self.font.render(pos_message, True, (255, 255, 255))
            pos_rect = pos_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 60))
            self.screen.blit(pos_surface, pos_rect)
        else:
            # Scale image to fit screen while maintaining aspect ratio
            img_w, img_h = surface.get_size()
            scale = min(self.screen_width / img_w, self.screen_height / img_h)
            
            if scale != 1.0:
                scaled_w = max(1, int(img_w * scale))
                scaled_h = max(1, int(img_h * scale))
                scaled_surface = pygame.transform.smoothscale(surface, (scaled_w, scaled_h))
            else:
                scaled_surface = surface
            
            # Center the image on screen
            blit_rect = scaled_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            self.screen.blit(scaled_surface, blit_rect)
        
        pygame.display.flip()

    def run(self):
        """Main display loop"""
        print("Starting AI Art Box Display...")
        print("Press ESC to exit")
        
        running = True
        while running:
            # Handle pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_F11:
                        # Toggle fullscreen (for testing)
                        self.fullscreen = not self.fullscreen
                        if self.fullscreen:
                            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
                        else:
                            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
                elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
                    self.screen_width = event.w
                    self.screen_height = event.h
                    self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
                    self._render()
            
            # Check if switch positions changed
            new_coords = self.switch_controller.get_image_coordinates()
            if new_coords != self.current_coords:
                self.current_coords = new_coords
                print(f"Displaying image: {self._current_filename()}")
                self._render()
            
            self.clock.tick(30)  # 30 FPS
        
        # Cleanup
        self.switch_controller.stop()
        pygame.quit()
        print("AI Art Box Display stopped.")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Art Box Display - Switch-controlled fullscreen image viewer")
    parser.add_argument(
        "--images",
        type=str,
        default="/home/fcc-010/Desktop/ai-art-box-firmware/images",
        help="Directory containing images named 0-0-0.png to 5-5-5.png"
    )
    parser.add_argument(
        "--windowed",
        action="store_true",
        help="Run in windowed mode instead of fullscreen (for testing)"
    )
    
    args = parser.parse_args()
    
    images_directory = Path(args.images).expanduser().resolve()
    if not images_directory.exists():
        print(f"Images directory does not exist: {images_directory}", file=sys.stderr)
        sys.exit(1)
    
    # Check for some required images
    test_images = ["0-0-0.png", "1-1-1.png", "5-5-5.png"]
    missing_images = []
    for img in test_images:
        if not (images_directory / img).exists():
            missing_images.append(img)
    
    if missing_images:
        print(f"Warning: Some test images missing: {missing_images}")
        print("Continuing anyway...")
    
    # Look for labels.json file
    labels_file = None
    candidate_labels = [
        images_directory / "labels.json",
        Path(args.images).parent / "labels.json", 
        Path(__file__).parent / "labels.json"
    ]
    
    for candidate in candidate_labels:
        if candidate.exists():
            labels_file = candidate
            break
    
    try:
        app = AIArtBoxDisplay(
            images_directory=images_directory,
            fullscreen=not args.windowed,
            labels_file=labels_file
        )
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
