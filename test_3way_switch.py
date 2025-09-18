#!/usr/bin/env python3

"""
Simple 3-Way Switch Test Script
Run this via SSH to test your ON-OFF-ON toggle switch wiring before running the full firmware.

Switch Specs:
- Type: ON-OFF-ON Toggle Switch (Twidec)
- Rating: 10A @ 250V
- Contact: Normally Open, Silver contacts
- Mounting: Panel Mount with crimp terminals
"""

import time
import sys

try:
    import RPi.GPIO as GPIO
    print("✓ RPi.GPIO imported successfully")
except ImportError:
    print("✗ RPi.GPIO not available. Make sure you're running on a Raspberry Pi.")
    sys.exit(1)

# GPIO pins for the ON-OFF-ON toggle switch
PIN_A = 0   # GPIO 0 (Physical Pin 27)
PIN_B = 5   # GPIO 5 (Physical Pin 29)
# Ground connection: Physical Pin 30 or any other ground pin

def setup_gpio():
    """Initialize GPIO pins for the ON-OFF-ON toggle switch"""
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIN_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(PIN_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        print(f"✓ GPIO pins {PIN_A} and {PIN_B} configured with pull-up resistors")
        return True
    except Exception as e:
        print(f"✗ GPIO setup failed: {e}")
        return False

def read_switch_position():
    """Read current switch position and return 0, 1, or 2"""
    try:
        # Read pin states (inverted because we use pull-up resistors)
        pin_a_active = not GPIO.input(PIN_A)
        pin_b_active = not GPIO.input(PIN_B)
        
        if pin_a_active and not pin_b_active:
            return 1  # Position 2 (GPIO 24 active)
        elif pin_b_active and not pin_a_active:
            return 2  # Position 3 (GPIO 25 active)
        else:
            return 0  # Position 1 (neutral/default)
    except Exception as e:
        print(f"✗ Error reading switch: {e}")
        return -1

def test_switch():
    """Main test function with enhanced debugging"""
    print("=" * 60)
    print("ON-OFF-ON Toggle Switch Test (DEBUG MODE)")
    print("=" * 60)
    print("Switch: Twidec ON-OFF-ON Toggle (10A @ 250V)")
    print(f"GPIO {PIN_A} (Pin 27) -> Switch Terminal A")
    print(f"GPIO {PIN_B} (Pin 29) -> Switch Terminal B") 
    print("Ground (Pin 30) -> Switch Common Terminal")
    print()
    
    if not setup_gpio():
        return False
    
    # Show initial state
    initial_pin_a = GPIO.input(PIN_A)
    initial_pin_b = GPIO.input(PIN_B)
    initial_position = read_switch_position()
    print(f"INITIAL STATE: GPIO [{initial_pin_a}, {initial_pin_b}] -> Position {initial_position}")
    print()
    
    print("CONTINUOUS GPIO MONITORING (shows ALL state changes)")
    print("Move your switch to different positions to test.")
    print("Press Ctrl+C to exit.")
    print()
    print("Format: [PIN_24_state, PIN_25_state] -> Position -> Mode")
    print("-" * 60)
    
    last_pin_a = None
    last_pin_b = None
    position_names = ["OFF (Center/Neutral)", "ON Position A (GPIO 24)", "ON Position B (GPIO 25)"]
    mode_names = ["GALLERY Mode", "SLIDESHOW Mode", "INTERACTIVE Mode"]
    
    try:
        while True:
            # Read raw GPIO states
            pin_a_state = GPIO.input(PIN_A)
            pin_b_state = GPIO.input(PIN_B)
            
            # Show ANY change in GPIO states
            if pin_a_state != last_pin_a or pin_b_state != last_pin_b:
                current_position = read_switch_position()
                timestamp = time.strftime("%H:%M:%S")
                
                print(f"[{timestamp}] GPIO States: [{pin_a_state}, {pin_b_state}] -> Position {current_position} -> {mode_names[current_position]}")
                
                # Additional debugging info
                pin_a_voltage = "HIGH" if pin_a_state else "LOW"
                pin_b_voltage = "HIGH" if pin_b_state else "LOW"
                print(f"            PIN_0: {pin_a_voltage}, PIN_5: {pin_b_voltage}")
                
                last_pin_a = pin_a_state
                last_pin_b = pin_b_state
                print()
            
            time.sleep(0.05)  # Check every 50ms for more responsiveness
            
    except KeyboardInterrupt:
        print("\n\nTest stopped by user.")
        return True
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False

def cleanup():
    """Clean up GPIO resources"""
    try:
        GPIO.cleanup([PIN_A, PIN_B])
        print("✓ GPIO cleanup completed")
    except Exception as e:
        print(f"⚠ GPIO cleanup warning: {e}")

def main():
    """Main entry point"""
    try:
        success = test_switch()
        if success:
            print("✓ Test completed successfully!")
        else:
            print("✗ Test failed!")
            sys.exit(1)
    finally:
        cleanup()

if __name__ == "__main__":
    main()
