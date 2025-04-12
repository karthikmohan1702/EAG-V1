# --- START OF FILE utils/find_coords.py ---
# Note: This script primarily finds the *window* coordinates.
# For drawing coordinates *relative* to the window, see the manual
# method described in the README using button_coords.py (or pyautogui.position)
# and calculation.

import time
from pywinauto.application import Application
from pywinauto.findwindows import ElementNotFoundError
import sys

print("Attempting to start mspaint.exe...")
try:
    # Start a new Paint instance directly
    app = Application(backend="uia").start("mspaint.exe", timeout=20)
    print("Started new Paint instance. Waiting for window to load...")
    time.sleep(4)  # Give it a bit more time to fully load

except Exception as e:
    print(f"Failed to start Paint: {e}")
    sys.exit(1)  # Exit if we can't start Paint

try:
    # Find the window
    paint_window = app.window(
        title_re=".*Paint",
        class_name="MSPaintApp",
        visible_only=True,
        enabled_only=True,
        found_index=0,
    )
    print("Found Paint window.")
    time.sleep(1)
    paint_window.set_focus()
    print("Paint window focused.")

    # Get the Paint window's rectangle
    window_rect = paint_window.rectangle()
    print(f"\nPaint Window Screen Coordinates: {window_rect}")
    print(f"  Left:   {window_rect.left}")
    print(f"  Top:    {window_rect.top}")
    print(f"  Right:  {window_rect.right}")
    print(f"  Bottom: {window_rect.bottom}")
    print("\nThese coordinates define the window's position on the screen.")
    print("Use Left (L) and Top (T) to calculate relative coordinates for drawing.")
    print("Exiting.")


except ElementNotFoundError:
    print(
        "\nCould not find the Paint window after starting it. Check title/class name or permissions. Exiting."
    )
except Exception as e:
    print(f"\nAn unexpected error occurred: {type(e).__name__} - {e}")

# --- END OF FILE utils/find_coords.py ---