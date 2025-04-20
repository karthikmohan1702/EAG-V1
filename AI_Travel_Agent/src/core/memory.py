from pydantic import BaseModel
from src.core.perception import UserPreferences # Make sure UserPreferences is importable
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class UserMemory(BaseModel):
    preferences: UserPreferences
    recent_destinations: list = [] # Could be used later

# Using a simple dictionary for in-memory storage
user_memory_store = {}
logging.info("In-memory user store initialized.")

def store_user_preferences(user_id: str, prefs: UserPreferences):
    """Stores user preferences in the in-memory dictionary."""
    logging.info(f"Attempting to store preferences for user_id: {user_id}")
    if not isinstance(prefs, UserPreferences):
         logging.error(f"Invalid data type for prefs: {type(prefs)}. Expected UserPreferences.")
         return
    try:
        user_memory_store[user_id] = UserMemory(preferences=prefs)
        logging.info(f"Preferences successfully stored for user_id: {user_id}")
    except Exception as e:
        logging.error(f"Error storing preferences for user_id {user_id}: {e}")

def get_user_preferences(user_id: str) -> UserPreferences | None:
    """Retrieves user preferences from the in-memory dictionary."""
    logging.info(f"Attempting to retrieve preferences for user_id: {user_id}")
    try:
        memory = user_memory_store.get(user_id)
        if memory and isinstance(memory, UserMemory):
            logging.info(f"Preferences found and retrieved for user_id: {user_id}")
            return memory.preferences
        else:
            logging.warning(f"No preferences found or invalid data for user_id: {user_id}")
            return None
    except Exception as e:
        logging.error(f"Error retrieving preferences for user_id {user_id}: {e}")
        return None