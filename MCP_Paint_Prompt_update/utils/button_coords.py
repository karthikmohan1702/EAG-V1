import pyautogui
import time

print("Move your mouse cursor to the desired location...")
print("Coordinates will be captured in 3 seconds.")
time.sleep(3)  # Give you time to move the mouse

x, y = pyautogui.position()
print(f"Screen Coordinates: x={x}, y={y}")
