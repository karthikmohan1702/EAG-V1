from pydantic import BaseModel
from typing import List
import logging

# Configure basic logging (can be configured once in main.py if preferred)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class UserPreferences(BaseModel):
    name: str
    location: str
    climate_preference: str
    activity_preferences: List[str]
    budget: str
    travel_pace: str

def collect_user_preferences() -> UserPreferences | None:
    logging.info("Entering 'collect_user_preferences' function.")
    try:
        print("\nPlease provide the following details:")
        name = input("1. What is your name? ")
        location = input("2. Where are you currently located? ")
        climate = input("3. What climate do you prefer (tropical, cold, moderate)? ")
        activities = input("4. What kind of activities do you enjoy (comma-separated, e.g., hiking, food, art)? ")
        budget = input("5. What is your travel budget (low, medium, high)? ")
        pace = input("6. What travel pace do you prefer (relaxed, moderate, fast)? ")

        # Basic input validation (example)
        if not all([name, location, climate, activities, budget, pace]):
            logging.error("One or more preferences were left empty.")
            print("Error: Please provide input for all fields.")
            return None

        prefs = UserPreferences(
            name=name.strip(),
            location=location.strip(),
            climate_preference=climate.strip().lower(),
            activity_preferences=[a.strip().lower() for a in activities.split(",")],
            budget=budget.strip().lower(),
            travel_pace=pace.strip().lower()
        )
        logging.info(f"Successfully collected preferences object for {prefs.name}.")
        return prefs
    except Exception as e:
        logging.error(f"Error during preference collection: {e}")
        return None