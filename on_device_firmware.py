#!/usr/bin/env python3

"""
AI Art Box Display Controller
Combines pygame image viewer with switch monitoring to create a fullscreen
HDMI display controlled by three 6-position switches.

Switch 1 controls first digit (0-5)
Switch 2 controls second digit (0-5) 
Switch 3 controls third digit (0-5)

Images are displayed as {switch1-1}-{switch2-1}-{switch3-1}.jpeg
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
                    print("LCD initialized successfully")
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
                self.lcd.write_string("*** INTER-ACTIVE ***")
                
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

    def update_lcd_for_coords(self, coords: Tuple[int, int, int]) -> bool:
        """Update LCD with labels corresponding to provided image coordinates"""
        try:
            if self.lcd is None:
                return False
            with channel_lock:
                if not self.select_channel(3):
                    return False
                self.lcd.clear()
                # Line 1: Title
                self.lcd.cursor_pos = (0, 0)
                self.lcd.write_string("*** SCREEN-SAVER ***")
                if self.labels:
                    lines = [
                        self.labels['first'][coords[0]],
                        self.labels['second'][coords[1]],
                        self.labels['third'][coords[2]],
                    ]
                    for i, text in enumerate(lines):
                        self.lcd.cursor_pos = (i + 1, 0)
                        self.lcd.write_string(text[:20])
                else:
                    self.lcd.cursor_pos = (1, 0)
                    self.lcd.write_string(f"SW1: Pos {coords[0] + 1}")
                    self.lcd.cursor_pos = (2, 0)
                    self.lcd.write_string(f"SW2: Pos {coords[1] + 1}")
                    self.lcd.cursor_pos = (3, 0)
                    self.lcd.write_string(f"SW3: Pos {coords[2] + 1}")
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
        
        # Screensaver state
        self.mode = "screensaver"  # start in screensaver mode as requested
        self.last_interaction_ts = 0.0  # tracks last time switches changed
        self.inactivity_seconds = 5 * 60  # 5 minutes
        self.screensaver_cycle_index = 0
        self.screensaver_cycle_interval = 3.0  # seconds per image while in screensaver
        self._last_cycle_ts = time.time()
        
        # Track last observed switch coordinates to detect real movement
        self._last_switch_coords: Tuple[int, int, int] = self.switch_controller.get_image_coordinates()
        # Start from the switch coordinates to make labels consistent initially
        self.current_coords = self._last_switch_coords
        # Ensure screensaver starts cycling from the current image
        self.screensaver_cycle_index = self._coords_to_index(self.current_coords)
        
        # Pygame setup
        pygame.init()
        pygame.mouse.set_visible(False)
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
        
        # Crossfade settings
        self.enable_crossfade: bool = True
        self.crossfade_duration: float = 0.4  # seconds
        self.crossfade_fps: int = 60
        self._last_scaled_surface: Optional[pygame.Surface] = None
        self._last_blit_rect: Optional[pygame.Rect] = None
        
        print(f"Display initialized: {self.screen_width}x{self.screen_height}")
        print(f"Fullscreen: {fullscreen}")
        
        # Initial render
        self._render()

    def _current_filename(self) -> str:
        """Generate filename based on current coordinates"""
        return f"{self.current_coords[0]}-{self.current_coords[1]}-{self.current_coords[2]}.jpeg"

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
            # No crossfade for missing images; render fallback text
            message = f"Missing: {image_path.name}"
            text_surface = self.font.render(message, True, (255, 255, 255))
            rect = text_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            self.screen.blit(text_surface, rect)
            
            pos_message = f"Switches: {self.switch_controller.switch_positions['SWITCH_1']}-{self.switch_controller.switch_positions['SWITCH_2']}-{self.switch_controller.switch_positions['SWITCH_3']}"
            pos_surface = self.font.render(pos_message, True, (255, 255, 255))
            pos_rect = pos_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 60))
            self.screen.blit(pos_surface, pos_rect)
            
            self._draw_labels_overlay(self.current_coords)
            
            try:
                if self.mode == "screensaver":
                    self.switch_controller.update_lcd_for_coords(self.current_coords)
                else:
                    self.switch_controller._update_lcd_display()
            except Exception:
                pass
            pygame.display.flip()
            # Do not update last surface on missing image
            return
        
        # Compute scaled surface and destination rect
        scaled_surface, blit_rect = self._get_scaled_surface_and_rect(surface)
        
        performed_crossfade = False
        if self.enable_crossfade and self._last_scaled_surface is not None and self._last_blit_rect is not None:
            try:
                self._crossfade(self._last_scaled_surface, self._last_blit_rect, scaled_surface, blit_rect)
                performed_crossfade = True
            except Exception:
                performed_crossfade = False
        
        if not performed_crossfade:
            # Simple render without transition
            self.screen.fill((0, 0, 0))
            self.screen.blit(scaled_surface, blit_rect)
            pygame.display.flip()
        
        # Update the LCD to show labels depending on mode (after final frame)
        try:
            if self.mode == "screensaver":
                self.switch_controller.update_lcd_for_coords(self.current_coords)
            else:
                self.switch_controller._update_lcd_display()
        except Exception:
            pass
        
        # Cache for next transition
        self._last_scaled_surface = scaled_surface
        self._last_blit_rect = blit_rect

    def _get_scaled_surface_and_rect(self, surface: pygame.Surface) -> Tuple[pygame.Surface, pygame.Rect]:
        img_w, img_h = surface.get_size()
        scale = min(self.screen_width / img_w, self.screen_height / img_h)
        if scale != 1.0:
            scaled_w = max(1, int(img_w * scale))
            scaled_h = max(1, int(img_h * scale))
            scaled_surface = pygame.transform.smoothscale(surface, (scaled_w, scaled_h))
        else:
            scaled_surface = surface
        blit_rect = scaled_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        return scaled_surface, blit_rect

    def _crossfade(self, old_surface: pygame.Surface, old_rect: pygame.Rect, new_surface: pygame.Surface, new_rect: pygame.Rect) -> None:
        duration = max(0.0, float(self.crossfade_duration))
        if duration == 0:
            # Instant switch
            self.screen.fill((0, 0, 0))
            self.screen.blit(new_surface, new_rect)
            pygame.display.flip()
            return
        frames = max(1, int(self.crossfade_fps * duration))
        for i in range(frames + 1):
            alpha = int(255 * (i / frames))
            # Render frame: old fully visible, new with increasing alpha
            self.screen.fill((0, 0, 0))
            self.screen.blit(old_surface, old_rect)
            if alpha >= 255:
                self.screen.blit(new_surface, new_rect)
            else:
                temp = new_surface.copy()
                temp.set_alpha(alpha)
                self.screen.blit(temp, new_rect)
            pygame.display.flip()
            # Keep UI responsive during transition
            pygame.event.pump()
            self.clock.tick(self.crossfade_fps)

    def _draw_labels_overlay(self, coords: Tuple[int, int, int]):
        """Draw translucent overlay with labels for the given coordinates"""
        try:
            labels = self.switch_controller.labels
            if labels and all(k in labels for k in ("first", "second", "third")):
                lines = [
                    labels['first'][coords[0]],
                    labels['second'][coords[1]],
                    labels['third'][coords[2]],
                ]
            else:
                # Fallback to numeric labels
                lines = [str(coords[0]), str(coords[1]), str(coords[2])]
            
            text_surfaces: List[pygame.Surface] = [self.font.render(line, True, (240, 240, 240)) for line in lines]
            padding = 12
            gap = 6
            widths = [s.get_width() for s in text_surfaces]
            fixed_line_height = self.font.get_height()
            box_w = max(widths) + padding * 2
            box_h = len(text_surfaces) * fixed_line_height + gap * (len(text_surfaces) - 1) + padding * 2
            
            box_surface = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            box_surface.fill((0, 0, 0, 160))
            
            for idx, s in enumerate(text_surfaces):
                y = padding + idx * (fixed_line_height + gap)
                y_offset = max(0, (fixed_line_height - s.get_height()) // 2)
                box_surface.blit(s, (padding, y + y_offset))
            
            # Top-left corner placement with small margin
            self.screen.blit(box_surface, (10, 10))
        except Exception:
            # If anything goes wrong with labels rendering, silently skip overlay
            pass

    @staticmethod
    def _coords_to_index(coords: Tuple[int, int, int]) -> int:
        return coords[0] * 36 + coords[1] * 6 + coords[2]

    @staticmethod
    def _index_to_coords(index: int) -> Tuple[int, int, int]:
        index = index % 216
        a = index // 36
        b = (index // 6) % 6
        c = index % 6
        return (a, b, c)

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
                        # Reset crossfade cache on mode change
                        self._last_scaled_surface = None
                        self._last_blit_rect = None
                elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
                    self.screen_width = event.w
                    self.screen_height = event.h
                    self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
                    # Reset crossfade cache on resize
                    self._last_scaled_surface = None
                    self._last_blit_rect = None
                    self._render()
            
            now = time.time()
            # Check if switch positions changed (user interaction)
            new_switch_coords = self.switch_controller.get_image_coordinates()
            if new_switch_coords != self._last_switch_coords:
                # Update last seen switch state
                self._last_switch_coords = new_switch_coords
                # Any movement exits screensaver and updates interaction timestamp
                self.last_interaction_ts = now
                if self.mode != "normal":
                    self.mode = "normal"
                # In normal mode, the displayed image follows the switches
                if new_switch_coords != self.current_coords:
                    self.current_coords = new_switch_coords
                    self._render()

            # In normal mode, enter screensaver after inactivity
            if self.mode == "normal" and (now - self.last_interaction_ts >= self.inactivity_seconds):
                self.mode = "screensaver"
                # Start cycling from current image
                self.screensaver_cycle_index = self._coords_to_index(self.current_coords)
                self._last_cycle_ts = now
                # Immediate render keeps current image but with overlay already handled
                self._render()

            # In screensaver mode, cycle through all images periodically
            if self.mode == "screensaver":
                if now - self._last_cycle_ts >= self.screensaver_cycle_interval:
                    self.screensaver_cycle_index = (self.screensaver_cycle_index + 1) % 216
                    self.current_coords = self._index_to_coords(self.screensaver_cycle_index)
                    self._last_cycle_ts = now
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
        help="Directory containing images named 0-0-0.jpeg to 5-5-5.jpeg"
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
    test_images = ["0-0-0.jpeg", "1-1-1.jpeg", "5-5-5.jpeg"]
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
