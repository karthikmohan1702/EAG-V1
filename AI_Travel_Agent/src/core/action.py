# Ensure Itinerary and DestinationDetail are importable from decision_making.py
# If decision_making.py is in the same directory, this should work:
try:
    # This line imports the Pydantic models defined in decision_making.py
    from src.core.decision_making import Itinerary, DestinationDetail
except ImportError:
    # Fallback or specific error handling if needed
    print("Error: Could not import Itinerary/DestinationDetail from decision_making. Check file location and imports.")
    # Define dummy classes or raise an error if critical
    class Itinerary: pass
    class DestinationDetail: pass

import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# This function EXPECTS an Itinerary object (structured by Pydantic) as input
def present_itinerary(itinerary: Itinerary | None):
    """Displays the detailed itinerary (structured by Pydantic models) to the user."""
    logging.info("Entering 'present_itinerary' function (v2 - detailed).")

    # Check if the received itinerary object is valid
    if not itinerary or not isinstance(itinerary, Itinerary) or not hasattr(itinerary, 'destinations') or not isinstance(itinerary.destinations, list) or not itinerary.destinations:
         logging.error("Invalid, empty, or None itinerary received.")
         print("\nSorry, could not generate or display a valid itinerary this time.")
         return

    try:
        print("\n✨ Your Personalized Detailed Travel Itinerary ✨")
        print("-" * 50) # Wider separator

        # Loop through the list of DestinationDetail objects within the Itinerary
        for idx, dest in enumerate(itinerary.destinations, 1):
            # Check if 'dest' is actually a DestinationDetail object
            if not isinstance(dest, DestinationDetail):
                 logging.warning(f"Item {idx} in destinations list is not a DestinationDetail object: {type(dest)}. Skipping.")
                 continue

            # Access attributes defined in the DestinationDetail Pydantic model
            print(f"\n📍 Destination {idx}: {getattr(dest, 'name', 'N/A')}")
            print(f"   - Why it Fits: {getattr(dest, 'why_it_fits', 'N/A')}")

            activities = getattr(dest, 'suggested_activities', [])
            if isinstance(activities, list):
                 print(f"   - Suggested Activities: {', '.join(activities) if activities else 'N/A'}")
            else:
                 logging.warning(f"Suggested activities for {getattr(dest, 'name', 'N/A')} is not a list: {type(activities)}")
                 print(f"   - Suggested Activities: Invalid data format received")

            print(f"   - Estimated Cost Level: {getattr(dest, 'estimated_cost_level', 'N/A')}")

        print("-" * 50)
        # Access the overall_reasoning attribute from the Itinerary Pydantic model
        print("\n💡 Overall Reasoning:")
        print(getattr(itinerary, 'overall_reasoning', 'N/A'))
        logging.info("Detailed itinerary displayed successfully.")

    except AttributeError as ae:
         logging.error(f"Error accessing itinerary attribute: {ae}. Itinerary object might be malformed.")
         logging.error(f"Problematic itinerary object: {itinerary}")
         print("\nSorry, there was an issue displaying parts of the itinerary due to unexpected data format.")
    except Exception as e:
        logging.error(f"Error displaying detailed itinerary: {e}")
        print("\nSorry, an unexpected error occurred while trying to display the detailed itinerary.")