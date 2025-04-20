# main.py (Updated)
import os
# Removed direct imports of configure, load_dotenv, genai if only used for client init
from src.core.perception import collect_user_preferences, UserPreferences
from src.core.memory import store_user_preferences, get_user_preferences # Removed user_memory_store import if not directly used
from src.core.decision_making import make_decision
from src.core.action import present_itinerary
import logging
import copy
# Import from config
from src.config import load_environment, initialize_client

# Configure basic logging (can be done once here)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment and initialize client using config module
load_environment()
client = initialize_client()

# --- Main Loop Function (run_agent_workflow - keep as before) ---
# Assume run_agent_workflow function definition is here (unchanged)
def run_agent_workflow(user_id: str | None = None):
    """Runs one cycle of the agent workflow, including potential modifications."""
    logging.info(f"--- Starting Agent Workflow Cycle (User ID: {user_id if user_id else 'New User'}) ---")
    if not client: # Check the client initialized via config
        logging.error("Exiting workflow cycle: Gemini client not initialized.")
        return None

    current_prefs = None
    current_user_id = user_id

    # --- Memory Check ---
    if current_user_id:
        logging.info(f"Checking memory for existing user_id: {current_user_id}")
        existing_prefs = get_user_preferences(current_user_id)
        if existing_prefs:
            logging.info(f"Found existing preferences for user_id: {current_user_id}")
            use_existing = input(f"Hi {existing_prefs.name}! Found saved preferences. Use them? (y/n): ").lower()
            if use_existing == 'y':
                print("Using saved preferences...")
                current_prefs = existing_prefs
            else:
                print("Okay, let's get new preferences.")
                current_prefs = None; current_user_id = None # Force re-collection
        else:
             logging.info(f"No existing preferences found for {current_user_id}.")
             current_user_id = None
    else:
         logging.info("No user_id. Collecting preferences for new user.")
         current_user_id = None
    # --- End Memory Check ---

    # --- Collect Preferences if needed ---
    if not current_prefs:
        logging.info("Collecting user preferences...")
        new_prefs = collect_user_preferences() # Assumes collect_user_preferences doesn't need client
        if not new_prefs: logging.error("Failed to collect preferences."); return None
        logging.info(f"Preferences collected for: {new_prefs.name}")
        current_user_id = new_prefs.name.lower().replace(" ", "_")
        logging.info(f"Storing preferences for user_id: {current_user_id}")
        store_user_preferences(current_user_id, new_prefs)
        logging.info("Preferences stored.")
        current_prefs = new_prefs
    # --- End Collect Preferences ---

    # --- Inner Loop ---
    while True:
        if not current_prefs: logging.error("Prefs missing."); return current_user_id

        logging.info(f"Making decision for {current_prefs.name}.")
        itinerary = make_decision(client, current_prefs) # Pass initialized client

        if not itinerary:
            logging.error("Failed to generate itinerary.")
            try_again = input("Failed. Modify and try again? (y/n): ").lower()
            if try_again != 'y': break
        else:
            logging.info("Decision made."); logging.info(f"Presenting itinerary for {current_prefs.name}")
            present_itinerary(itinerary); logging.info("Itinerary presented.")

        # --- Modification Prompt ---
        modify = input("\nModify preference and regenerate? (y/n): ").lower()
        if modify != 'y': break

        print("\nModify: 1.Climate 2.Activities 3.Budget 4.Pace"); choice = input("Choice(1-4): ")
        modified_prefs = copy.deepcopy(current_prefs); valid_mod = False
        if choice == '1': modified_prefs.climate_preference = input("New climate: ").strip().lower(); valid_mod = True
        elif choice == '2': modified_prefs.activity_preferences = [a.strip().lower() for a in input("New activities: ").split(",")]; valid_mod = True
        elif choice == '3': modified_prefs.budget = input("New budget: ").strip().lower(); valid_mod = True
        elif choice == '4': modified_prefs.travel_pace = input("New pace: ").strip().lower(); valid_mod = True
        else: print("Invalid choice.")
        if valid_mod: print("Regenerating..."); current_prefs = modified_prefs; logging.info(f"Prefs temporarily modified: {current_prefs}")
        # --- End Modification ---
    # --- End Inner Loop ---
    logging.info("--- Workflow Cycle Finished ---")
    return current_user_id

# --- Main Execution ---
def main():
    # Exit if client failed to initialize
    if not client:
        print("❌ Gemini client failed to initialize. Please check API key and configuration. Exiting.")
        return

    logging.info("Starting main application loop.")
    last_user_id = None
    while True:
        returned_user_id = run_agent_workflow(last_user_id)
        run_again = input("\nStart a new session? (y/n): ").lower()
        if run_again != 'y': print("Goodbye! 👋"); break
        else:
             name_input = input("Enter name for next session: ")
             last_user_id = name_input.lower().replace(" ", "_") if name_input else None
             print("\nStarting next session...\n" + "="*30 + "\n")
    logging.info("Main loop finished.")

if __name__ == "__main__":
    main()