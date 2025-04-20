from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional
import re
import json
# Ensure UserPreferences is importable from perception.py
# If perception.py is in the same directory, this should work:
try:
    from src.core.perception import UserPreferences
except ImportError:
    # Fallback or specific error handling if needed
    print("Error: Could not import UserPreferences from perception. Check file location and imports.")
    # Define a dummy class or raise an error if critical
    class UserPreferences: pass

import logging
import google.generativeai as genai # Import library for potential type hinting

# Configure basic logging
# Note: Streamlit app handles its own logging config, this is fallback/module level
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Updated Pydantic model for highly detailed, bulleted destination ---
class DestinationDetail(BaseModel):
    name: str = Field(..., description="Name of the city/region, Country")
    # Expecting lists for bullet points
    why_it_fits: List[str] = Field(..., description="List of bullet points explaining why it fits user preferences (climate, activities, pace, budget).")
    suggested_activities: List[str] = Field(..., description="Bulleted list of 3-5 specific activities aligning with user preferences.")
    food_highlights: List[str] = Field(..., description="Bulleted list of 2-3 specific food items or restaurant types to try.")
    transportation_notes: List[str] = Field(..., description="Bulleted list of notes on local transportation (e.g., ['- Walkable center', '- Good public transport', '- Taxis available']).")
    sample_daily_focus: List[str] = Field(..., description="Bulleted list suggesting a possible focus for each day based on suggested duration (e.g., ['Day 1: Explore Old Town', 'Day 2: Museum visits', 'Day 3: Food tour & relaxation']).")
    # Other fields remain similar
    estimated_cost_level: str = Field(..., description="Estimated cost (Low, Medium, High) relative to user's budget.")
    suggested_duration_days: Optional[str] = Field(None, description="Suggested trip duration in days (e.g., '3-4 days', '5 days')")
    suggested_accommodation_type: Optional[str] = Field(None, description="Type of accommodation suitable for budget (e.g., 'Hostels, Budget Hotels', 'Mid-range Hotels, Airbnb', 'Luxury Resorts')")
    potential_day_trip: Optional[str] = Field(None, description="Suggestion for a relevant nearby day trip (or null if none suitable)")


# --- Itinerary model remains the same ---
class Itinerary(BaseModel):
    destinations: List[DestinationDetail] = Field(..., description="List of detailed destination recommendations")
    overall_reasoning: str = Field(..., description="General reasoning for selecting these destinations as a group") # Can also ask for bullets here if desired

def extract_json_string(text: str) -> str | None:
    """ Extracts a JSON string block from text, handling markdown fences. """
    logging.info("Attempting to extract JSON string from text.")
    # Pattern 1: ```json ... ```
    # Making regex non-greedy and handling optional json language tag
    match_fence = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL | re.IGNORECASE)
    if match_fence:
        extracted_json = match_fence.group(1).strip()
        logging.info("Extracted JSON using ```json fence.")
        return extracted_json
    # Pattern 2: Raw JSON object (potentially with surrounding text/whitespace)
    match_raw = re.search(r'^\s*(\{.*?\})\s*$', text, re.DOTALL)
    if match_raw:
         extracted_json = match_raw.group(1).strip()
         logging.info("Extracted raw JSON object (entire string).")
         return extracted_json
    # Pattern 3: Fallback - find any structure starting with { and ending with }
    # Be careful as this might grab unintended parts if LLM response is malformed
    match_fallback = re.search(r'(\{.*\})', text, re.DOTALL)
    if match_fallback:
        extracted_json = match_fallback.group(1).strip()
        # Basic validation: check if it starts/ends with braces
        if extracted_json.startswith('{') and extracted_json.endswith('}'):
            logging.warning("Extracted JSON using fallback pattern - validation needed.")
            return extracted_json
        else:
             logging.error("Fallback pattern matched non-JSON-like structure.")
             # Continue to raise error below
             pass

    logging.error("❌ No valid JSON structure found in LLM output.")
    raise ValueError("❌ No valid JSON structure found in LLM output.")


# --- Updated make_decision function for bullet points & detail ---
def make_decision(client: genai.GenerativeModel, preferences: UserPreferences) -> Itinerary | None:
    """Generates a highly detailed, bulleted itinerary."""
    logging.info("Entering 'make_decision' function (v4 - bullets & detail).")
    if not isinstance(preferences, UserPreferences):
        logging.error("Invalid preferences object received in make_decision.")
        return None

    activity_prefs_str = ", ".join(preferences.activity_preferences)

    # --- Updated Prompt for Bullet Points ---
    prompt = f'''
You are an exceptionally detailed and structured travel consultant AI. Your goal is to provide personalized, highly detailed, actionable, and easy-to-read travel recommendations using bullet points for clarity.

**User Preferences:**
- **Activities:** {activity_prefs_str}
- **Climate:** {preferences.climate_preference}
- **Budget:** {preferences.budget}
- **Pace:** {preferences.travel_pace}
- **Current Location:** {preferences.location}

**Your Task:**
1.  **Analyze Preferences:** Deeply analyze the user's profile.
2.  **Select Destinations:** Choose exactly 3 distinct destinations matching the profile.
3.  **Provide Structured Details:** For *each* destination, provide comprehensive details. Crucially, use JSON lists of strings for fields marked with "(bullet points)" to represent distinct points.
    * `name`: City/Region, Country
    * `why_it_fits` (bullet points): List explaining fit (climate, activities, pace, budget).
    * `suggested_activities` (bullet points): List of 3-5 specific activities.
    * `food_highlights` (bullet points): List of 2-3 specific food items/types.
    * `transportation_notes` (bullet points): List of notes on local transport.
    * `sample_daily_focus` (bullet points): List suggesting a focus for each day (match number of points roughly to duration).
    * `estimated_cost_level`: Low, Medium, or High.
    * `suggested_duration_days`: Estimated duration (e.g., "4 days").
    * `suggested_accommodation_type`: Suitable types (e.g., "Boutique hotels").
    * `potential_day_trip`: A nearby trip suggestion (or null).
4.  **Format Output:** Structure your *entire* response **only** as a single, valid JSON object following the format below. Ensure all requested fields are present, using JSON lists for bulleted items and null where appropriate. No extra text before or after the JSON.

**Fallback:** If perfect matches aren't found, explain compromises in 'why_it_fits' bullets or 'overall_reasoning'.

**Required JSON Output Format Example:**
```json
{{
  "destinations": [
    {{
      "name": "Example City, Example Country",
      "why_it_fits": [
        "Matches 'cold' climate preference perfectly during winter.",
        "Offers excellent 'art' museums and galleries.",
        "Relaxed pace suitable for exploring cafes and parks.",
        "Fits within the 'high' budget range for recommended activities."
      ],
      "suggested_activities": [
        "Visit the National Art Gallery.",
        "Explore the historic Old Town district.",
        "Attend a classical music concert.",
        "Take a guided food tour focused on local specialties."
      ],
      "food_highlights": [
        "Try the traditional 'City Cake'.",
        "Explore diverse international restaurants in the West End.",
        "Visit the Central Food Market for local produce and snacks."
      ],
      "transportation_notes": [
        "Highly walkable city center.",
        "Efficient and affordable tram system.",
        "Airport easily accessible via express train."
      ],
      "sample_daily_focus": [
        "Day 1: Arrival, check-in, explore Old Town & dinner.",
        "Day 2: National Art Gallery visit, explore West End cafes.",
        "Day 3: Concert (evening), relax in City Park.",
        "Day 4: Food tour (morning), departure."
      ],
      "estimated_cost_level": "High",
      "suggested_duration_days": "4 days",
      "suggested_accommodation_type": "Boutique Hotels, Serviced Apartments",
      "potential_day_trip": "Visit the nearby Castle ruins (requires bus)."
    }}
    // ... two more destination objects similar to above ...
  ],
  "overall_reasoning": "These destinations provide a strong match for the user's preferences, focusing on [key theme like art/food] in a [climate] setting, while respecting the [budget/pace] requirements. [Note any compromises]."
}}
```
'''
    # Initialize variables for robust error logging
    json_string = None
    response_text = "No response received from LLM."
    itinerary_data = None
    response = None # Initialize response variable

    try:
        logging.info("--- SENDING PROMPT TO LLM (v4 - bullets & detail) ---")
        safety_settings = [ {"category": c, "threshold": "BLOCK_MEDIUM_AND_ABOVE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
        response = client.generate_content(prompt, safety_settings=safety_settings)
        logging.info("--- LLM RESPONSE RECEIVED (v4 - bullets & detail) ---")

        # It's safer to check existence before accessing .text
        if hasattr(response, 'text'):
            response_text = response.text
        else:
             # Handle cases where the response might be blocked or malformed early
             feedback = getattr(response, 'prompt_feedback', 'Unknown reason')
             logging.error(f"LLM response missing text attribute. Feedback: {feedback}")
             # Propagate error to Streamlit if possible (assuming st is available in context)
             try:
                 import streamlit as st
                 st.error(f"LLM response issue. Feedback: {feedback}")
             except ImportError:
                 print(f"LLM response issue. Feedback: {feedback}")
             return None


        # Check for blocked content based on parts attribute
        if not hasattr(response, 'parts') or not response.parts:
             feedback = getattr(response, 'prompt_feedback', 'N/A')
             logging.error(f"LLM response blocked/empty. Feedback: {feedback}")
             try: # Try to show error in Streamlit
                 import streamlit as st
                 st.error(f"LLM response blocked or empty. Feedback: {feedback}")
             except ImportError: # Fallback for non-Streamlit environments
                  print(f"LLM response blocked or empty. Feedback: {feedback}")
             return None

        logging.info("Extracting JSON from response...")
        json_string = extract_json_string(response_text) # Will raise ValueError if not found

        logging.info("Parsing JSON string...")
        itinerary_data = json.loads(json_string) # Will raise JSONDecodeError on failure

        logging.info("Validating parsed data using Pydantic model...")
        itinerary = Itinerary(**itinerary_data) # Will raise ValidationError on failure

        logging.info("Itinerary object created and validated successfully.")
        return itinerary

    # Specific error handling
    except ValueError as ve: # From extract_json_string
         logging.error(f"JSON Extraction Error: {ve}. Problematic Text:\n'''{response_text}'''")
         try: import streamlit as st; st.error("Error extracting itinerary data from LLM response.")
         except ImportError: print("Error extracting itinerary data from LLM response.")
         return None
    except json.JSONDecodeError as jde: # From json.loads
         logging.error(f"JSON Parsing Error: {jde}. Problematic String:\n'''{json_string}'''")
         try: import streamlit as st; st.error("Error parsing itinerary data structure.")
         except ImportError: print("Error parsing itinerary data structure.")
         return None
    except ValidationError as pve: # From Itinerary(**itinerary_data)
        logging.error(f"Pydantic Validation Error: {pve}. Problematic Data:\n'''{itinerary_data}'''")
        try: import streamlit as st; st.error("Generated itinerary structure is invalid or missing required fields.")
        except ImportError: print("Generated itinerary structure is invalid.")
        return None
    # Catch-all for other unexpected errors (e.g., API call failures)
    except Exception as e:
        logging.error(f"❌ Unexpected error in make_decision: {e}. Response (if available): {response_text}")
        # Log feedback if available from response object
        if response and hasattr(response, 'prompt_feedback'):
            logging.error(f"Prompt Feedback: {getattr(response, 'prompt_feedback', 'N/A')}")
        try: import streamlit as st; st.error("An unexpected error occurred while generating the itinerary.")
        except ImportError: print("An unexpected error occurred.")
        return None