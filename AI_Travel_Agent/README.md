# AI Travel Agent Bot (Learning Project)

## Video

https://youtu.be/c1oPvDx6ib8 

## Overview

This project breaks down a basic Python AI Travel Agent bot. It's designed not as a full-fledged travel planner, but as a **clear, simple learning exercise** to reveal the core concepts behind agentic AI systems.

The agent takes user preferences (climate, activities, budget, pace) and uses Google's Generative AI LLM model (Gemini-gemini-2.0-flash) to generate a basic, sleek travel itinerary suggestion.

**Disclaimer:** This is a beginner-friendly project focused on architecture and integration patterns. It does *not* produce exhaustive travel itineraries.

## What You'll Learn (The Real Destination)

This project's value lies in illustrating *how* AI agents are built. Its primary goal is to help beginners explore:

1.  **The Agentic Flow:** See the classic Perception -> Memory -> Decision-Making -> Action cycle in action. User input (`src/core/perception.py`) informs the AI (`src/core/decision_making.py`), which might recall past details (`src/core/memory.py`) before producing an output presented to the user (`src/core/action.py`).
2.  **Modular Design:** Understand why splitting code into logical units (`src/config.py`, `src/core/`, `src/gmail_mcp_server/`, etc.) makes development cleaner and more manageable.
3.  **Feature Integration:** Discover how to bolt on extra capabilities like:
    * Creating a user interface with Streamlit (`src/app.py`).
    * Converting output to a downloadable PDF (`src/app.py` using `fpdf2`).
    * Sending results via a Telegram bot (`src/app.py` using `requests`).
    * Connecting to external tools (like Gmail) using standards like the Model-Context Protocol (`src/gmail_mcp_server/`).

![core_components](https://github.com/user-attachments/assets/464a8465-e33f-4edb-aa0d-9265aaebc37d)


## Features

* **AI Itinerary Generation:** Uses Google Gemini to create personalized travel suggestions based on user preferences.
* **Modular Agentic Flow:** Demonstrates Perception -> Memory -> Decision -> Action pattern using separate modules in `src/core/`.
* **Streamlit Web UI:** Provides an interactive web interface (`src/app.py`) for user input, preference modification, and itinerary display.
* **Command-Line Interface:** Includes a basic CLI runner (`src/main.py`) for non-UI interaction.
* **PDF Export:** Allows users to download the generated itinerary as a PDF file.
* **Telegram Integration:** Can send the itinerary PDF to a configured Telegram chat.
* **Gmail Integration (via MCP):** Uses the Model-Context Protocol (MCP) to interact with a Gmail account for sending the itinerary via email.


![core_components_1](https://github.com/user-attachments/assets/d9b8b3a0-84fb-4eaa-b63b-431161e48a71)


## Technology Stack

* **Language:** Python 3.10+
* **AI Model:** Google Gemini API (`google-generativeai`)
* **Web Framework:** Streamlit (`streamlit`)
* **API/Tool Integration:**
    * Model-Context Protocol (`mcp` SDK)
    * Google Gmail API (`google-api-python-client`, `google-auth-oauthlib`, `google-auth-httplib2`)
    * Telegram Bot API (`requests`)
* **Data Handling:** Pydantic (`pydantic`, `pydantic-settings`)
* **PDF Generation:** `fpdf2`
* **Configuration:** `python-dotenv`

## Project Structure
* **AI_TRAVEL_AGENT/**
    * `.env`                   *(Environment variables - KEEP SECRET)*
    * `.gitignore`             *(Specifies untracked files)*
    * `requirements.txt`       *(Python dependencies - Recommended)*
    * **src/**
        * `__init__.py`
        * **core/** *(Core agent logic modules)*
            * `__init__.py`
            * `action.py`        *(Handles presenting output - CLI)*
            * `decision_making.py` *(Interacts with AI model)*
            * `memory.py`        *(Stores/Retrieves user preferences)*
            * `perception.py`    *(Gathers user input - CLI)*
        * **gmail_mcp_server/** *(Gmail integration via MCP)*
            * `__init__.py`
            * **gmail/**
                * `__init__.py`
                * `client.py`      *(MCP Client for Gmail)*
                * `server.py`      *(MCP Server for Gmail)*
                * `client_secrets.json` *(Google API Credentials - KEEP SECRET)*
                * `token.json`       *(Google API Token - KEEP SECRET)*
        * `config.py`            *(Loads config, initializes clients)*
        * `main.py`              *(Entry point for CLI version)*
        * `app.py`               *(Entry point for Streamlit Web App)*
    * `README.md`              *(This file)*              

## Setup Instructions

1.  **Clone Repository:**
    ```bash
    git clone <your-repository-url>
    cd AI_TRAVEL_AGENT
    ```

2.  **Create Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**
    * *(Create a `requirements.txt` file based on the imports in the project or the Technology Stack section above).*
    * Install using pip:
        ```bash
        pip install -r requirements.txt
        ```
    * *(Make sure to include `mcp @ git+https://github.com/modelcontextprotocol/python-sdk.git` or the relevant source if installing individually).*

4.  **Set Up Environment Variables:**
    * Create `.env` file in the project root.
    * Add your credentials:
        ```dotenv
        GEMINI_API_KEY="YOUR_GOOGLE_GEMINI_API_KEY"
        TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
        TELEGRAM_CHAT_ID="YOUR_TELEGRAM_CHAT_ID"
        ```

5.  **Set Up Google Gmail API Credentials:**
    * Follow Google's instructions to enable the Gmail API and create OAuth 2.0 Client ID credentials ([Quickstart Guide](https://developers.google.com/gmail/api/quickstart/python#authorize_credentials_for_a_desktop_application)).
    * Download the credentials JSON file.
    * Rename it to `client_secrets.json` and place it in `src/gmail_mcp_server/gmail/`.
    * Run the application (`src/app.py` or `src/gmail_mcp_server/gmail/server.py` if possible). The first time it needs Gmail access, it should initiate an OAuth flow in your browser.
    * Completing the flow will create `token.json` in the same directory.
    * **Important:** Add `client_secrets.json` and `token.json` to your `.gitignore` file.

6.  **Configure `.gitignore`:**
    * Ensure `.env`, `src/gmail_mcp_server/gmail/client_secrets.json`, `src/gmail_mcp_server/gmail/token.json`, `venv/`, `__pycache__/` etc., are included.

## Running the Application

1.  **Activate Virtual Environment:**
    ```bash
    source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
    ```

2.  **Run Streamlit Web App:**
    ```bash
    streamlit run src/app.py
    ```
    Access the app via the URL provided (usually `http://localhost:8501`).

3.  **Run Command-Line Version (Optional):**
    ```bash
    python src/main.py
    ```
    Interact with the agent directly in your terminal.

## Notes & Limitations

* **Itinerary Simplicity:** The generated travel plan is basic and serves primarily to demonstrate the AI interaction flow.
* **Non-Interactive Gmail:** The Gmail integration via Streamlit is non-interactive. The *original intent* was for the MCP client to ask clarifying questions (recipient, subject, body) within the Streamlit UI if needed. However, this was blocked by technical challenges involving `asyncio` subprocess management (`NotImplementedError` on Windows with `asyncio.create_subprocess_exec`) and the complexities of maintaining interactive state between Streamlit and an external async process. The current implementation requires all email details upfront.
* **Error Handling:** Basic error handling is included, but production applications would require more comprehensive strategies.
* **Memory Persistence:** Memory is session-based in Streamlit (`st.session_state`) or uses a simple global dictionary in the CLI version (`memory.py`); no persistent database is used.

## References

* **Gmail Agent with MCP Article:** [https://medium.com/@jason.summer/create-a-gmail-agent-with-model-context-protocol-mcp-061059c07777](https://medium.com/@jason.summer/create-a-gmail-agent-with-model-context-protocol-mcp-061059c07777)
* **Gmail MCP Server GitHub Repository:** [https://github.com/jasonsum/gmail-mcp-server/tree/main](https://github.com/jasonsum/gmail-mcp-server/tree/main)
* **Model-Context Protocol Official Site:** [https://modelcontextprotocol.io/](https://modelcontextprotocol.io/)
