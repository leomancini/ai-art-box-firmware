#!/usr/bin/env python3
from RPLCD.i2c import CharLCD
import smbus
import time
import sys
import threading

# I2C multiplexer setup
bus = smbus.SMBus(1)
channel_lock = threading.Lock()

# LCD initialization on channel 3 (SD3)
lcd = None

def init_lcd():
    """Initialize LCD on channel 3"""
    global lcd
    try:
        with channel_lock:
            if select_channel(3):  # LCD is on channel 3 (SD3)
                lcd = CharLCD('PCF8574', 0x27)
                lcd.clear()
                return True
    except Exception as e:
        print(f"LCD init error: {e}")
        return False
    return False

def select_channel(channel):
    """Select which channel of the PCA9548A multiplexer to use"""
    channel_values = {0: 0x01, 1: 0x02, 2: 0x04, 3: 0x08, 4: 0x10, 5: 0x20, 6: 0x40, 7: 0x80}
    try:
        bus.write_byte(0x70, channel_values[channel])
        time.sleep(0.01)
        return True
    except Exception as e:
        return False

def read_device(channel, address):
    """Read data from a specific device"""
    try:
        if not select_channel(channel):
            return None
        data = bus.read_byte(address)
        return data
    except Exception as e:
        return None

def decode_switch_position(data, switch_name=None):
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

# Store last valid positions
last_valid_positions = {'SWITCH_1': None, 'SWITCH_2': None, 'SWITCH_3': None}

def update_lcd_display(switch_values):
    """Update LCD with current switch values using RPLCD"""
    global lcd, last_valid_positions
    try:
        if lcd is None:
            return False
            
        # Update last valid positions only when we have valid readings
        switch1_pos = decode_switch_position(switch_values.get('SWITCH_1', 0xFF), 'SWITCH_1')
        if switch1_pos is not None:
            last_valid_positions['SWITCH_1'] = switch1_pos
            
        switch2_pos = decode_switch_position(switch_values.get('SWITCH_2', 0xFF), 'SWITCH_2')
        if switch2_pos is not None:
            last_valid_positions['SWITCH_2'] = switch2_pos
            
        switch3_pos = decode_switch_position(switch_values.get('SWITCH_3', 0xFF), 'SWITCH_3')
        if switch3_pos is not None:
            last_valid_positions['SWITCH_3'] = switch3_pos
            
        with channel_lock:
            if not select_channel(3):  # LCD is on channel 3 (SD3)
                return False
            
            lcd.clear()
            
            # Line 1: Title
            lcd.cursor_pos = (0, 0)
            lcd.write_string("AI Art Box Monitor")
            
            # Line 2: SWITCH_1 (Ch1) - show last valid position
            if last_valid_positions['SWITCH_1'] is not None:
                switch1_text = f"SW1: Pos {last_valid_positions['SWITCH_1']}"
                lcd.cursor_pos = (1, 0)
                lcd.write_string(switch1_text[:20])
            
            # Line 3: SWITCH_2 (Ch2) - show last valid position
            if last_valid_positions['SWITCH_2'] is not None:
                switch2_text = f"SW2: Pos {last_valid_positions['SWITCH_2']}"
                lcd.cursor_pos = (2, 0)
                lcd.write_string(switch2_text[:20])
            
            # Line 4: SWITCH_3 (Ch0) - show last valid position
            if last_valid_positions['SWITCH_3'] is not None:
                switch3_text = f"SW3: Pos {last_valid_positions['SWITCH_3']}"
                lcd.cursor_pos = (3, 0)
                lcd.write_string(switch3_text[:20])
            
        return True
    except Exception as e:
        print(f"LCD update error: {e}")
        return False



# Actual devices found from scan
devices = [
    {"name": "SWITCH_3", "channel": 0, "address": 0x24, "type": "Switch Controller"},
    {"name": "SWITCH_1", "channel": 1, "address": 0x24, "type": "Switch Controller"},
    {"name": "SWITCH_2", "channel": 2, "address": 0x24, "type": "Switch Controller"},
]

def monitor_all_devices():
    """Monitor all devices and show their values with LCD display"""
    print("AI Art Box - Device Monitor with LCD")
    print("Initializing LCD on channel 3...")
    
    # Initialize LCD
    if not init_lcd():
        print("WARNING: Could not initialize LCD on channel 3")
    else:
        print("✓ LCD initialized successfully")
    
    print("Press Ctrl+C to stop")
    
    last_values = {}
    
    # Display initial values on LCD
    if lcd is not None:
        initial_switch_values = {}
        for dev in devices:
            data = read_device(dev['channel'], dev['address'])
            if data is not None:
                initial_switch_values[dev['name']] = data
            else:
                initial_switch_values[dev['name']] = 0xFF
        update_lcd_display(initial_switch_values)
    
    try:
        while True:
            changes_detected = False
            current_switch_values = {}
            
            for dev in devices:
                data = read_device(dev['channel'], dev['address'])
                dev_key = f"ch{dev['channel']}_0x{dev['address']:02X}"
                
                if data is not None:
                    # Check if value changed
                    if dev_key in last_values and last_values[dev_key] != data:
                        changes_detected = True
                    
                    last_values[dev_key] = data
                    current_switch_values[dev['name']] = data
                else:
                    current_switch_values[dev['name']] = 0xFF
            
            # Update LCD when changes detected (will show last valid positions)
            if changes_detected and lcd is not None:
                update_lcd_display(current_switch_values)
            
            time.sleep(0.2)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
        # Clear LCD on exit
        try:
            if lcd is not None:
                with channel_lock:
                    select_channel(3)
                    lcd.clear()
        except:
            pass

if __name__ == "__main__":
    print("AI Art Box - Switch Monitor")
    print("Starting switch monitoring with LCD display...")
    monitor_all_devices()
