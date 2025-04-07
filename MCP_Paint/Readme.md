# MCP Agent: Calculation and Paint Automation

This project demonstrates an agentic system using the `mcp-ai` library and Google's Gemini LLM (`gemini-2.0-flash`) to perform a multi-step task:

1.  Calculate the sum of ASCII values for the characters in the string "IN".
2.  Automate Microsoft Paint on Windows to:
    *   Open Paint (maximized).
    *   Draw a predefined rectangle.
    *   Write the calculated sum (prefixed with "FINAL ANSWER - ") inside the rectangle.

## How it Works

The system consists of two main components:

1.  **`custom_server.py`**: This script acts as the **MCP Server**. It defines a set of tools (functions) that the agent can use. These include mathematical operations and Windows UI automation tools for interacting with MS Paint (`open_paint`, `draw_rectangle`, `add_text_in_paint`) using `pywinauto`. It listens for instructions from the client.
2.  **`talk2mcp.py`**: This script is the **MCP Client and Agent Controller**.
    *   It connects to the MCP server (`custom_server.py`) over standard I/O.
    *   It initializes a session and retrieves the list of available tools.
    *   It interacts with the Gemini LLM, providing it with the goal, tools, and history.
    *   It follows a strict two-phase plan defined in the system prompt:
        *   **Phase 1:** Instructs the LLM to calculate the ASCII sum using tools.
        *   **Phase 2:** Instructs the LLM to call Paint tools (`open_paint`, `draw_rectangle`, `add_text_in_paint`) sequentially, passing the result (prefixed) to the text tool.
    *   It parses the LLM's response, executes the requested tool call via MCP, or transitions phases.

This demonstrates a basic perception-planning-action loop where the LLM acts as the planning component, constrained by detailed instructions.

## Requirements

*   Python 3.10+
*   Windows Operating System (for MS Paint automation)
*   Google Gemini API Key

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <repository-directory>
    ```
2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # Activate (Windows PowerShell/cmd)
    .\venv\Scripts\activate
    # Activate (Git Bash / Linux / macOS)
    # source venv/bin/activate
    ```
3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  Create a file named `.env` in the root directory of the project.
2.  Add your Google Gemini API key to the `.env` file. The script looks for `GEMINI_API_KEY` first, then `GOOGLE_API_KEY`.
    ```dotenv
    # .env file
    GEMINI_API_KEY="YOUR_API_KEY_HERE"
    ```
    Replace `"YOUR_API_KEY_HERE"` with your actual key.

## Finding Coordinates (Manual Setup Step)

The agent needs specific coordinates to interact with Paint correctly (drawing the rectangle, placing text). These can vary based on your screen resolution, DPI scaling, and Paint version. The current script uses predefined values, but here's how you can find them if needed:

**Tools Used:**

*   `utils/button_coords.py`: A simple script using `pyautogui` to report the **screen coordinates** of your mouse cursor after a 3-second delay.
*   `utils/find_coords.py`: A script using `pywinauto` to find the Paint window and report its **screen coordinates** (Left, Top, Right, Bottom).

**Process:**

1.  **Get Paint Window Coordinates:**
    *   Run `python utils/find_coords.py`.
    *   This will start Paint and print the screen coordinates of its window border.
    *   Note down the **Left** (`window_L`) and **Top** (`window_T`) values. These are the reference point for relative coordinates. Example: `L: -8, T: -8`.

2.  **Get Button Coordinates (Optional - Currently Hardcoded):**
    *   The coordinates for the Rectangle button (`441, 65`) and Text button (`291, 65`) are currently hardcoded in `custom_server.py`.
    *   If these don't work for you, open Paint manually.
    *   Run `python utils/button_coords.py`.
    *   Quickly move your mouse cursor to the center of the desired button (e.g., Rectangle tool) within the 3-second delay.
    *   The script will print the button's screen coordinates. Update the corresponding values in `custom_server.py` if necessary.

3.  **Get Rectangle Drawing Coordinates (Relative to Window):**
    *   Open Paint manually.
    *   Run `python utils/button_coords.py`.
    *   Quickly move your mouse to the desired **top-left corner** for your drawing rectangle *inside* the Paint canvas.
    *   Record the screen coordinates printed (`top_left_x`, `top_left_y`).
    *   Run `python utils/button_coords.py` again.
    *   Quickly move your mouse to the desired **bottom-right corner** for your drawing rectangle *inside* the Paint canvas.
    *   Record the screen coordinates printed (`bottom_right_x`, `bottom_right_y`).
    *   **Calculate Relative Coordinates:**
        *   `x1 = top_left_x - window_L`
        *   `y1 = top_left_y - window_T`
        *   `x2 = bottom_right_x - window_L`
        *   `y2 = bottom_right_y - window_T`
    *   These calculated `x1`, `y1`, `x2`, `y2` are the values needed for the `draw_rectangle` tool call. Update the `RECT_X1`, `RECT_Y1`, `RECT_X2`, `RECT_Y2` variables near the top of `talk2mcp.py` with these values.

4.  **Calculate Text Placement Coordinates (Relative to Window):**
    *   The script `talk2mcp.py` automatically calculates the text placement coordinates (`TEXT_CLICK_X`, `TEXT_CLICK_Y`) based on the rectangle coordinates (`RECT_X1`, `RECT_Y1`) and a `TEXT_PADDING` value defined near the top of the script.
    *   It aims to place the text slightly inside the top-left corner of the rectangle.
    *   You usually don't need to find these manually, but you can adjust the `TEXT_PADDING` in `talk2mcp.py` if the text isn't positioned well inside the rectangle.

5.  **Update `talk2mcp.py`:**
    *   Modify the `RECT_X1`, `RECT_Y1`, `RECT_X2`, `RECT_Y2` variables at the top of `talk2mcp.py` with the relative values calculated in step 3.
    *   The system prompt within `talk2mcp.py` will automatically use these updated values when instructing the LLM.
    *   Adjust `TEXT_PADDING` if needed.

**Accuracy Tips:**

*   **DPI Scaling:** Ensure Windows display scaling is set to 100%. Higher scaling factors will affect coordinates.
*   **Zoom:** Zooming in within Paint can help with precise mouse positioning for corner coordinates.
*   **Consistency:** Try to measure coordinates with Paint maximized or in a consistent window size each time.

## Usage

Ensure you have completed the Configuration and Coordinate Finding steps if necessary.

1.  **Activate Virtual Environment (if used):**
    ```bash
    # Windows
    .\venv\Scripts\activate
    # Git Bash / Linux / macOS
    # source venv/bin/activate
    ```
2.  **Run the Agent:**
    ```bash
    python talk2mcp.py
    ```

The script will start the `custom_server.py` process, connect to it, interact with the LLM, and attempt to automate Paint as described. Watch the console output for progress and potential errors.

## Video
https://github.com/user-attachments/assets/e27b08ff-c406-4955-8f27-8392cf0fea00

## Notes

*   UI automation can be sensitive to timing and screen layout changes.
*   Error handling is basic; the script might fail if Paint behaves unexpectedly.
