from RPLCD.i2c import CharLCD
import smbus
import time
import threading

# I2C multiplexer setup
bus = smbus.SMBus(1)
channel_lock = threading.Lock()

def select_channel(channel):
    """Select which channel of the PCA9548A multiplexer to use"""
    channel_values = {0: 0x01, 1: 0x02, 2: 0x04, 3: 0x08}
    try:
        bus.write_byte(0x70, channel_values[channel])
        time.sleep(0.01)
        return True
    except Exception as e:
        print(f"Channel select error: {e}")
        return False

# Initialize LCD on channel 0 (SD0)
with channel_lock:
    select_channel(0)
    lcd = CharLCD('PCF8574', 0x27)

# PCF8574 I2C expander address
EXPANDER_ADDR = 0x24

# Switch variables for 3 switches
switch1_position = 1  # Controls section 1 (scene)
switch2_position = 1  # Controls section 2 (art style) 
switch3_position = 1  # Controls section 3 (activity)
last_raw_data = None

# Text sections for rendering
section1_options = [
    "CROWDED SUBWAY",  # Position 1
    "CITY SKYLINE SUNSET",   # Position 2
    "DESERT GAS AT NIGHT",   # Position 3
    "ICE CREAM TRUCK",     # Position 4
    "BUSY DINER SCENE",      # Position 5
    "FOGGY LIGHTHOUSE"       # Position 6
]

section2_options = [
    "VINTAGE TRAVEL",
    "AFRO-FUTURISTIC", 
    "IMPRESSIONIST",
    "CHINESE PAINTING",
    "SPACE-AGE NASA",
    "FILM NOIR"
]

section3_options = [
    "READING BOOK",
    "WASHING DISHES",
    "GARDENING YARD", 
    "PICKING APPLES",
    "PETTING CAT",
    "RIDING BICYCLE"
]

def get_text_for_all_switches(switch1_pos, switch2_pos, switch3_pos):
    """Get text from all sections based on their respective switch positions"""
    # Section 1 controlled by switch 1
    section1_text = section1_options[switch1_pos - 1] if 1 <= switch1_pos <= 6 else section1_options[0]
    
    # Section 2 controlled by switch 2
    section2_text = section2_options[switch2_pos - 1] if 1 <= switch2_pos <= 6 else section2_options[0]
    
    # Section 3 controlled by switch 3
    section3_text = section3_options[switch3_pos - 1] if 1 <= switch3_pos <= 6 else section3_options[0]
    
    return section1_text, section2_text, section3_text

def read_pcf8574():
    """Read all pins from PCF8574 expander"""
    with channel_lock:
        try:
            if not select_channel(1):
                return 0xFF
            data = bus.read_byte(EXPANDER_ADDR)
            return data
        except Exception as e:
            print(f"PCF8574 read error: {e}")
            return 0xFF

def decode_switch_position(data):
    """Decode the 6-position switch from PCF8574 data"""
    # Direct mapping based on your observed patterns
    position_map = {
        0xFE: 1,  # P0 low
        0xFD: 2,  # P1 low
        0xFB: 3,  # P2 low
        0xF7: 4,  # P3 low
        0xEF: 5,  # P4 low
        0xDF: 6,  # P5 low
    }
    
    return position_map.get(data, None)  # Return None if between positions

def read_switch():
    global switch1_position, last_raw_data
    
    while True:
        try:
            # Read current state (currently only reading switch 1)
            raw_data = read_pcf8574()
            
            # Only process if data changed
            if raw_data != last_raw_data:
                # Decode position
                new_position = decode_switch_position(raw_data)
                
                # Only update if we have a valid position (not between switches)
                if new_position is not None:
                    # Print debug info
                    print(f"Raw: 0x{raw_data:02X} -> Switch 1 Position: {new_position}")
                    switch1_position = new_position
                else:
                    # Between positions
                    print(f"Raw: 0x{raw_data:02X} -> Between positions")
                
                last_raw_data = raw_data
            
        except Exception as e:
            print(f"Switch read error: {e}")
        
        time.sleep(0.05)

def get_switch_visual(position):
    """Create visual representation of switch position: ○○●○○○"""
    visual = list("......") 
    if 1 <= position <= 6:
        visual[position - 1] = "*"
    return "".join(visual)

def update_display():
    global switch1_position, switch2_position, switch3_position
    last_positions = (None, None, None)
    
    while True:
        try:
            current_positions = (switch1_position, switch2_position, switch3_position)
            
            # Update display when any position changes
            if current_positions != last_positions:
                # Get text for all sections
                section1_text, section2_text, section3_text = get_text_for_all_switches(
                    switch1_position, switch2_position, switch3_position)
                
                with channel_lock:
                    if not select_channel(0):
                        continue
                    
                    lcd.clear()
                    
                    # Display section 1 (controlled by switch 1)
                    lcd.cursor_pos = (0, 0)
                    lcd.write_string(f"{section1_text[:20]}")
                    
                    # Display section 2 (controlled by switch 2)
                    lcd.cursor_pos = (1, 0)
                    lcd.write_string(f"{section2_text[:20]}")
                    
                    # Display section 3 (controlled by switch 3)
                    lcd.cursor_pos = (2, 0)
                    lcd.write_string(f"{section3_text[:20]}")
                    
                    # Display all switch positions visually (fits exactly in 20 chars: 6+1+6+1+6=20)
                    lcd.cursor_pos = (3, 0)
                    switch1_visual = get_switch_visual(switch1_position)
                    switch2_visual = get_switch_visual(switch2_position)
                    switch3_visual = get_switch_visual(switch3_position)
                    lcd.write_string(f"{switch1_visual} {switch2_visual} {switch3_visual}")
                
                # Print to console for debugging
                print(f"Switches: {switch1_position}/{switch2_position}/{switch3_position}")
                print(f"  Section 1: {section1_text}")
                print(f"  Section 2: {section2_text}")
                print(f"  Section 3: {section3_text}")
                print("-" * 40)
                
                last_positions = current_positions
                
        except Exception as e:
            print(f"Display update error: {e}")
            time.sleep(1)
            continue
        
        time.sleep(0.1)

try:
    # Clear display initially
    with channel_lock:
        select_channel(0)
        lcd.clear()
    
    print("6-Position Switch Active")
    print("Position mapping:")
    print("  0xFE -> Position 1")
    print("  0xFD -> Position 2") 
    print("  0xFB -> Position 3")
    print("  0xF7 -> Position 4")
    print("  0xEF -> Position 5")
    print("  0xDF -> Position 6")
    print("-" * 30)
    
    # Start threads
    switch_thread = threading.Thread(target=read_switch, daemon=True)
    display_thread = threading.Thread(target=update_display, daemon=True)
    
    switch_thread.start()
    display_thread.start()
    
    # Keep main thread alive
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Exiting...")
finally:
    with channel_lock:
        select_channel(0)
        lcd.clear()
