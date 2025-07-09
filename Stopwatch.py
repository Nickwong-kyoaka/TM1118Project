import RPi.GPIO as GPIO
import time
from datetime import datetime

# Setup GPIO
GPIO.setmode(GPIO.BCM)
SW1 = 21  # Typically the first button
SW2 = 20  # Typically the second button

# Set up buttons with pull-up resistors
GPIO.setup(SW1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SW2, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Stopwatch variables
running = False
start_time = 0
elapsed_time = 0
last_display_time = 0

def format_time(seconds):
    """Format seconds into HH:MM:SS.milliseconds"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"

def button_callback(channel):
    global running, start_time, elapsed_time
    
    if channel == SW1:
        # SW1 - Start/Stop
        if not running:
            # Start the stopwatch
            start_time = time.time() - elapsed_time
            running = True
            print("Stopwatch STARTED")
        else:
            # Stop the stopwatch
            elapsed_time = time.time() - start_time
            running = False
            print(f"Stopwatch STOPPED: {format_time(elapsed_time)}")
    
    elif channel == SW2:
        # SW2 - Reset
        if not running:
            elapsed_time = 0
            print("Stopwatch RESET")
        else:
            print("Cannot reset while running!")

# Add event detection for both buttons
GPIO.add_event_detect(SW1, GPIO.FALLING, callback=button_callback, bouncetime=200)
GPIO.add_event_detect(SW2, GPIO.FALLING, callback=button_callback, bouncetime=200)

print("Raspberry Pi Stopwatch")
print("SW1: Start/Stop")
print("SW2: Reset")
print("Press Ctrl+C to exit")

try:
    while True:
        if running:
            current_time = time.time()
            if current_time - last_display_time >= 0.1:  # Update display every 100ms
                elapsed_time = current_time - start_time
                print(f"\r{format_time(elapsed_time)}", end="")
                last_display_time = current_time
        time.sleep(0.01)  # Small delay to reduce CPU usage

except KeyboardInterrupt:
    print("\nExiting stopwatch")
finally:
    GPIO.cleanup()
