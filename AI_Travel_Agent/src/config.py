# config.py
import os
import google.generativeai as genai
from google.generativeai import configure
from dotenv import load_dotenv
import logging

def load_environment():
    """Loads environment variables from .env file."""
    load_dotenv()
    logging.info("Environment variables loaded (from config.py).")

def initialize_client():
    """Loads API key, configures, and returns the Gemini client."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logging.error("GEMINI_API_KEY environment variable not set.")
        # In a Streamlit context, we might show an error, but here we return None
        # In a main script context, we might exit.
        return None

    try:
        configure(api_key=api_key)
        # Consider making the model name configurable if needed
        client = genai.GenerativeModel(model_name="gemini-2.0-flash") # Changed model name
        logging.info("Gemini client configured successfully (from config.py).")
        return client
    except Exception as e:
        logging.error(f"Error configuring Gemini client (from config.py): {e}")
        return None

def get_telegram_credentials():
    """Loads and returns Telegram credentials."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        logging.warning("Telegram Bot Token or Chat ID is missing in .env file.")
    return token, chat_id