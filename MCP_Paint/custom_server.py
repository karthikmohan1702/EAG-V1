# --- START OF FILE custom_server.py ---

import math
import sys
import time

# Third-party imports
import win32con
import win32gui
from mcp import types
from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from PIL import Image as PILImage
from pywinauto.application import Application
from win32api import GetSystemMetrics

# Global variable to track Paint instance
paint_app = None

# Instantiate an MCP server client
mcp = FastMCP("PaintCalculatorAgent")


# --- DEFINE TOOLS ---

# --- Math Tools ---
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    print(f"CALLED: add(a={a}, b={b}) -> int:")
    return int(a + b)


@mcp.tool()
def add_list(l: list[int]) -> int:  # Ensure list type hint is correct
    """Add all numbers in a list"""
    print(f"CALLED: add_list(l={l}) -> int:")
    return sum(l)


@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    print(f"CALLED: subtract(a={a}, b={b}) -> int:")
    return int(a - b)


@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    print(f"CALLED: multiply(a={a}, b={b}) -> int:")
    return int(a * b)


@mcp.tool()
def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    print(f"CALLED: divide(a={a}, b={b}) -> float:")
    if b == 0:
        raise ValueError("Division by zero")
    return float(a / b)


@mcp.tool()
def power(a: int, b: int) -> int:
    """Power of two numbers"""
    print(f"CALLED: power(a={a}, b={b}) -> int:")
    return int(a**b)


@mcp.tool()
def sqrt(a: int) -> float:
    """Square root of a number"""
    print(f"CALLED: sqrt(a={a}) -> float:")
    if a < 0:
        raise ValueError("Cannot calculate square root of a negative number")
    return float(a**0.5)


@mcp.tool()
def cbrt(a: int) -> float:
    """Cube root of a number"""
    print(f"CALLED: cbrt(a={a}) -> float:")
    # Handle negative numbers correctly for cube root
    return float(math.copysign(abs(a) ** (1 / 3), a))


@mcp.tool()
def factorial(a: int) -> int:
    """factorial of a number"""
    print(f"CALLED: factorial(a={a}) -> int:")
    if a < 0:
        raise ValueError("Factorial not defined for negative numbers")
    return int(math.factorial(a))


@mcp.tool()
def log(a: int) -> float:
    """natural logarithm (base e) of a number"""
    print(f"CALLED: log(a={a}) -> float:")
    if a <= 0:
        raise ValueError("Logarithm not defined for non-positive numbers")
    return float(math.log(a))


@mcp.tool()
def remainder(a: int, b: int) -> int:
    """remainder of two numbers divison (a % b)"""
    print(f"CALLED: remainder(a={a}, b={b}) -> int:")
    if b == 0:
        raise ValueError("Division by zero for remainder")
    return int(a % b)


@mcp.tool()
def sin(a: float) -> float:  # Changed to float for radians
    """sin of a number (in radians)"""
    print(f"CALLED: sin(a={a}) -> float:")
    return float(math.sin(a))


@mcp.tool()
def cos(a: float) -> float:  # Changed to float for radians
    """cos of a number (in radians)"""
    print(f"CALLED: cos(a={a}) -> float:")
    return float(math.cos(a))


@mcp.tool()
def tan(a: float) -> float:  # Changed to float for radians
    """tan of a number (in radians)"""
    print(f"CALLED: tan(a={a}) -> float:")
    return float(math.tan(a))


# --- Utility Tools ---
@mcp.tool()
def mine(a: int, b: int) -> int:  # Keeping as is, though name is ambiguous
    """special mining tool (calculates a - 2*b)"""
    print(f"CALLED: mine(a={a}, b={b}) -> int:")
    return int(a - b - b)


@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    """Create a thumbnail (100x100 max) from an image file path."""
    print(f"CALLED: create_thumbnail(image_path='{image_path}') -> Image:")
    try:
        img = PILImage.open(image_path)
        img.thumbnail((100, 100))
        # Convert to RGB if it's P mode with transparency for PNG saving
        if img.mode == "P":
            img = img.convert("RGBA")
        elif img.mode not in ("RGBA", "LA"):
            img = img.convert("RGB")  # Convert other modes to RGB suitable for PNG

        import io

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="PNG")
        img_byte_arr = img_byte_arr.getvalue()
        return Image(data=img_byte_arr, format="png")  # Use bytes directly

    except FileNotFoundError:
        raise ValueError(f"Image file not found at path: {image_path}")
    except Exception as e:
        raise ValueError(f"Error creating thumbnail: {str(e)}")


@mcp.tool()
def strings_to_chars_to_int(string: str) -> list[int]:
    """Return the ASCII values of the characters in a word/string"""
    print(f"CALLED: strings_to_chars_to_int(string='{string}') -> list[int]:")
    if not isinstance(string, str):
        raise TypeError("Input must be a string")
    return [int(ord(char)) for char in string]


@mcp.tool()
def fibonacci_numbers(n: int) -> list[int]:  # Added type hint for return list
    """Return the first n Fibonacci Numbers"""
    print(f"CALLED: fibonacci_numbers(n={n}) -> list:")
    if not isinstance(n, int) or n < 0:
        raise ValueError("Input 'n' must be a non-negative integer")
    if n == 0:
        return []
    if n == 1:
        return [0]
    fib_sequence = [0, 1]
    while len(fib_sequence) < n:
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return fib_sequence


# --- Paint Tools ---
@mcp.tool()
async def open_paint() -> dict:
    """Opens Microsoft Paint maximized on the primary monitor. Returns success or error message."""
    global paint_app
    print("CALLED: open_paint() -> dict:")
    try:
        # Check if Paint is already open via the global variable
        if paint_app is not None:
            try:
                # Verify the window still exists and is valid
                paint_window = paint_app.window(class_name="MSPaintApp")
                if paint_window.is_visible():
                    print("Paint is already open.")
                    # Bring to front and maximize just in case
                    paint_window.set_focus()
                    win32gui.ShowWindow(paint_window.handle, win32con.SW_MAXIMIZE)
                    time.sleep(0.2)
                    return {
                        "content": [
                            TextContent(
                                type="text", text="Paint is already open and focused."
                            )
                        ]
                    }
                else:
                    print("Paint app object exists but window not found. Re-opening.")
                    paint_app = None  # Reset global variable
            except Exception:
                print("Error checking existing paint window. Re-opening.")
                paint_app = None  # Reset global variable

        print("Starting mspaint.exe...")
        # Use connect if already running, otherwise start
        try:
            paint_app = Application(backend="uia").connect(
                class_name="MSPaintApp", timeout=2
            )
            print("Connected to existing Paint instance.")
            paint_window = paint_app.window(class_name="MSPaintApp")
            paint_window.wait("visible", timeout=5)
        except Exception:
            print("No existing instance found or connect failed, starting new one.")
            paint_app = Application(backend="uia").start("mspaint.exe")
            time.sleep(1.5)  # Increased delay for Paint to start reliably
            paint_window = paint_app.window(class_name="MSPaintApp")
            paint_window.wait("visible", timeout=10)  # Wait longer for window

        print("Maximizing Paint window...")
        win32gui.ShowWindow(paint_window.handle, win32con.SW_MAXIMIZE)
        time.sleep(0.7)  # Increased delay for window to maximize and settle
        paint_window.set_focus()  # Ensure it has focus
        time.sleep(0.3)

        return {
            "content": [
                TextContent(type="text", text="Paint opened successfully and maximized.")
            ]
        }
    except Exception as e:
        paint_app = None  # Reset on error
        print(f"Error in open_paint: {str(e)}")
        import traceback

        traceback.print_exc()
        return {
            "content": [TextContent(type="text", text=f"Error opening Paint: {str(e)}")]
        }


@mcp.tool()
async def draw_rectangle(x1: int, y1: int, x2: int, y2: int) -> dict:
    """Draws a rectangle in MS Paint from top-left (x1,y1) to bottom-right (x2,y2) canvas coordinates. Assumes the rectangle tool is selectable at coords (441, 65)."""
    global paint_app
    print(f"CALLED: draw_rectangle(x1={x1}, y1={y1}, x2={x2}, y2={y2}) -> dict:")
    try:
        if not paint_app:
            return {
                "content": [
                    TextContent(
                        type="text", text="Paint is not open. Please call open_paint first."
                    )
                ]
            }

        paint_window = paint_app.window(class_name="MSPaintApp")
        paint_window.set_focus()
        time.sleep(0.3)  # Delay for focus

        # Click on the Rectangle tool button
        # These coords might need adjustment depending on screen resolution and Paint version
        rect_tool_coords = (441, 65)
        print(f"Clicking Rectangle tool at {rect_tool_coords}...")
        paint_window.click_input(coords=rect_tool_coords, absolute=True)
        time.sleep(0.6)  # Increased delay for tool selection to register

        # Get the canvas area
        try:
            canvas = paint_window.child_window(class_name="MSPaintView")
            canvas.wait("visible", timeout=5)  # Wait for canvas
        except Exception as e:
            print(f"Could not find canvas 'MSPaintView', trying default window area. Error: {e}")
            canvas = paint_window  # Fallback, might be inaccurate

        print(f"Drawing rectangle from ({x1},{y1}) to ({x2},{y2})...")
        canvas.press_mouse_input(coords=(x1, y1))
        time.sleep(0.2)
        canvas.move_mouse_input(coords=(x2, y2))
        time.sleep(0.2)
        canvas.release_mouse_input(coords=(x2, y2))
        time.sleep(0.3)  # Delay after drawing

        return {
            "content": [
                TextContent(
                    type="text", text=f"Rectangle drawn from ({x1},{y1}) to ({x2},{y2})."
                )
            ]
        }
    except Exception as e:
        print(f"Error in draw_rectangle: {str(e)}")
        import traceback

        traceback.print_exc()
        return {
            "content": [
                TextContent(type="text", text=f"Error drawing rectangle: {str(e)}")
            ]
        }


@mcp.tool()
async def add_text_in_paint(text: str, x: int, y: int) -> dict:
    """Adds text in MS Paint. Clicks the Text tool button at (291, 65), then clicks at canvas coordinates (x, y) to place the text cursor, and types the text."""
    global paint_app
    print(f"CALLED: add_text_in_paint(text='{text}', x={x}, y={y}) -> dict:")
    try:
        if not paint_app:
            return {
                "content": [
                    TextContent(
                        type="text", text="Paint is not open. Please call open_paint first."
                    )
                ]
            }

        paint_window = paint_app.window(class_name="MSPaintApp")
        paint_window.set_focus()
        time.sleep(0.3)  # Delay for focus

        # Click on the Text tool button (adjust if needed)
        text_tool_coords = (291, 65)
        print(f"Clicking Text tool at {text_tool_coords}...")
        paint_window.click_input(coords=text_tool_coords, absolute=True)
        time.sleep(0.6)  # Increased delay for tool selection

        # Get the canvas area
        try:
            canvas = paint_window.child_window(class_name="MSPaintView")
            canvas.wait("visible", timeout=5)
        except Exception as e:
            print(f"Could not find canvas 'MSPaintView', trying default window area. Error: {e}")
            canvas = paint_window  # Fallback

        # Click where to start typing
        print(f"Clicking canvas at ({x},{y}) to place text cursor...")
        canvas.click_input(coords=(x, y))
        time.sleep(0.5)  # Delay for text cursor to appear

        # Type the text passed from client
        print(f"Typing text: '{text}'...")
        text_to_type = str(text) # Ensure text is string
        paint_window.type_keys(text_to_type, with_spaces=True, pause=0.05)
        time.sleep(0.5)  # Delay after typing

        # Click somewhere else to finalize the text entry (optional but good practice)
        finalize_x = x + 150  # Adjust as needed (further away)
        finalize_y = y + 100  # Adjust as needed
        print(f"Clicking canvas at ({finalize_x},{finalize_y}) to finalize text entry...")
        try:
            # Ensure click is within window bounds if using fallback canvas
            if canvas == paint_window:
                 window_rect = canvas.rectangle()
                 finalize_x = min(finalize_x, window_rect.right - 10)
                 finalize_y = min(finalize_y, window_rect.bottom - 10)

            canvas.click_input(coords=(finalize_x, finalize_y))
            time.sleep(0.2)
        except Exception as e:
            print(f"Optional finalize click failed: {e}. Text should still be entered.")

        return {
            "content": [
                TextContent(type="text", text=f"Text '{text}' added at approx ({x},{y}).")
            ]
        }
    except Exception as e:
        print(f"Error in add_text_in_paint: {str(e)}")
        import traceback

        traceback.print_exc()
        return {"content": [TextContent(type="text", text=f"Error adding text: {str(e)}")]}


# --- DEFINE RESOURCES ---
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    print(f"CALLED: get_greeting(name='{name}') -> str:")
    return f"Hello, {name}!"


# --- DEFINE AVAILABLE PROMPTS (Examples) ---
@mcp.prompt()
def review_code(code: str) -> str:
    """Example prompt: Request code review."""
    print("CALLED: review_code(code=...) -> str:")
    return f"Please review this code:\n\n{code}"


@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    """Example prompt: Start debugging conversation."""
    print(f"CALLED: debug_error(error='{error}') -> list[base.Message]:")
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]


# --- Main Execution ---
if __name__ == "__main__":
    print("--- Starting MCP Server (custom_server.py) ---")
    is_dev_mode = len(sys.argv) > 1 and sys.argv[1] == "dev"

    if is_dev_mode:
        print("Running in DEV mode (no transport)")
        mcp.run()
    else:
        print("Running in STDIO transport mode")
        mcp.run(transport="stdio")
    print("--- MCP Server (custom_server.py) Finished ---")

# --- END OF FILE custom_server.py ---