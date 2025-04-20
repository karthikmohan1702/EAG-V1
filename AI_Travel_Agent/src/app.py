# app.py (Final Version - Attempt 4 Simplified Email Body)
import streamlit as st
import os
import google.generativeai as genai
from google.generativeai import configure
from dotenv import load_dotenv
import logging
import copy
import io
import sys
from fpdf import FPDF
import requests
import subprocess # Import subprocess

import sys
import os

# --- BEGIN PATH MODIFICATION ---
# Get the absolute path of the directory containing app.py (i.e., src/)
src_dir = os.path.dirname(os.path.abspath(__file__))
# Get the absolute path of the project root directory (one level up from src/)
project_root = os.path.dirname(src_dir)
# Add the project root to the Python path if it's not already there
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- END PATH MODIFICATION ---
# --- Import components from project modules ---
try:
    from src.core.perception import UserPreferences
    from src.core.memory import UserMemory
    from src.core.decision_making import Itinerary, DestinationDetail, make_decision
    # Import from NEW config module
    from src.config import load_environment, initialize_client, get_telegram_credentials
except ImportError as e:
    st.error(f"Fatal Error: Could not import required modules. {e}")
    st.stop()

# --- Logger Setup (Once per session) ---
log_format = '%(asctime)s - %(levelname)s - %(message)s'; formatter = logging.Formatter(log_format)
if 'log_stream' not in st.session_state: st.session_state.log_stream = io.StringIO()
if 'logging_configured' not in st.session_state: st.session_state.logging_configured = False
if not st.session_state.logging_configured:
    root_logger = logging.getLogger();
    if not root_logger.hasHandlers(): root_logger.setLevel(logging.INFO)
    ui_h_exists = any(isinstance(h, logging.StreamHandler) and getattr(h,'stream',None) == st.session_state.log_stream for h in root_logger.handlers)
    if not ui_h_exists: ui_h = logging.StreamHandler(st.session_state.log_stream); ui_h.setFormatter(formatter); root_logger.addHandler(ui_h)
    con_h_exists = any(isinstance(h, logging.StreamHandler) and getattr(h,'stream',None) == sys.stdout for h in root_logger.handlers)
    # Prevent adding duplicate console handlers
    if not con_h_exists and not any(isinstance(h, logging.StreamHandler) and h.stream in (sys.stdout, sys.stderr) for h in root_logger.handlers):
        con_h = logging.StreamHandler(sys.stdout); con_h.setFormatter(formatter); root_logger.addHandler(con_h)
    st.session_state.logging_configured = True; logging.info("Logging configured (app.py).")


# --- Configuration via config.py ---
load_environment()
client = initialize_client()
TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID = get_telegram_credentials()
if client is None: st.error("❌ Gemini client init failed."); logging.error("Client is None."); st.stop()

# --- Session State ---
if 'user_id' not in st.session_state: st.session_state.user_id = None
if 'preferences' not in st.session_state: st.session_state.preferences = None
if 'itinerary' not in st.session_state: st.session_state.itinerary = None
if 'memory_store' not in st.session_state: st.session_state.memory_store = {}; logging.info("Initialized memory store.")
if 'app_state' not in st.session_state: st.session_state.app_state = 'login'
if 'error_message' not in st.session_state: st.session_state.error_message = None
if 'show_modify_form' not in st.session_state: st.session_state.show_modify_form = False


# --- Memory Functions ---
def store_prefs_in_session(user_id: str, prefs: UserPreferences):
    if not user_id or not prefs or not isinstance(prefs, UserPreferences): return
    logging.info(f"Storing prefs for {user_id}.")
    st.session_state.memory_store[user_id] = UserMemory(preferences=prefs)

def get_prefs_from_session(user_id: str) -> UserPreferences | None:
    if not user_id: return None
    logging.info(f"Retrieving prefs for {user_id}.")
    memory_entry = st.session_state.memory_store.get(user_id)
    if isinstance(memory_entry, UserMemory) and hasattr(memory_entry, 'preferences') and isinstance(memory_entry.preferences, UserPreferences):
        logging.info(f"Prefs found for {user_id}."); return memory_entry.preferences
    logging.warning(f"No valid prefs found for {user_id}."); return None

# --- PDF Generation Function ---
# (Keep PDF function as before, it formats correctly for PDF)
def create_itinerary_pdf(itinerary: Itinerary, preferences: UserPreferences) -> bytes:
    pdf = FPDF(); pdf.add_page(); pdf.set_auto_page_break(auto=True, margin=15); pdf.set_font("Helvetica", size=12)
    pdf.set_font("Helvetica", "B", 16); pdf.multi_cell(0, 10, f"Itinerary for {preferences.name}", align='C'); pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12); pdf.write(6, "Preferences:\n"); pdf.set_font("Helvetica", size=10)
    prefs_text = (f"- Climate: {preferences.climate_preference.title()}\n- Activities: {', '.join(preferences.activity_preferences)}\n- Budget: {preferences.budget.title()}\n- Pace: {preferences.travel_pace.title()}"); pdf.multi_cell(0, 5, prefs_text.encode('latin-1', 'replace').decode('latin-1')); pdf.ln(5)
    for idx, dest in enumerate(itinerary.destinations):
        pdf.set_font("Helvetica", "B", 14); pdf.write(7, f"Dest {idx+1}: {getattr(dest, 'name', 'N/A')}\n"); pdf.set_font("Helvetica", size=10); pdf.ln(1)
        def write_pdf_section(title, content):
             if content or isinstance(content, list):
                pdf.set_font("Helvetica", "B", 10); pdf.write(5, f"{title}:\n"); pdf.set_font("Helvetica", size=10); encoded_content = None
                if isinstance(content, list): encoded_content = "".join([f"- {item}\n" for item in content]).encode('latin-1', 'replace').decode('latin-1') if content else "- N/A"
                elif content is not None: encoded_content = str(content).encode('latin-1', 'replace').decode('latin-1')
                else: encoded_content = "N/A"
                pdf.multi_cell(0, 5, encoded_content); pdf.ln(2)
        write_pdf_section("Duration", getattr(dest, 'suggested_duration_days', None)); write_pdf_section("Accommodation", getattr(dest, 'suggested_accommodation_type', None)); write_pdf_section("Cost Level", getattr(dest, 'estimated_cost_level', 'N/A').title()); write_pdf_section("Why it Fits", getattr(dest, 'why_it_fits', [])); write_pdf_section("Activities", getattr(dest, 'suggested_activities', [])); write_pdf_section("Food", getattr(dest, 'food_highlights', [])); write_pdf_section("Transport", getattr(dest, 'transportation_notes', [])); write_pdf_section("Daily Focus", getattr(dest, 'sample_daily_focus', [])); write_pdf_section("Day Trip", getattr(dest, 'potential_day_trip', None))
        pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12); pdf.write(6, "Reasoning:\n"); pdf.set_font("Helvetica", size=10); reasoning_text = getattr(itinerary, 'overall_reasoning', 'N/A'); pdf.multi_cell(0, 5, reasoning_text.encode('latin-1', 'replace').decode('latin-1')); pdf.ln(5)
    return bytes(pdf.output()) # Explicitly convert to bytes


# --- Telegram Function ---
def send_pdf_to_telegram(pdf_bytes: bytes, user_name: str, bot_token: str, chat_id: str) -> bool:
    # (Keep Telegram function as before)
    if not bot_token or not chat_id: logging.error("Telegram creds missing."); st.error("Telegram creds missing."); return False
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"; caption = f"Itinerary for {user_name}."
    files = {'document': ('itinerary.pdf', pdf_bytes, 'application/pdf')}; payload = {'chat_id': chat_id, 'caption': caption}
    try:
        logging.info(f"Sending PDF to Telegram: {chat_id}"); response = requests.post(url, data=payload, files=files, timeout=30); response.raise_for_status()
        if response.json().get("ok"): logging.info("Sent PDF to Telegram."); return True
        else: logging.error(f"Telegram API error: {response.json().get('description')}"); st.error(f"Telegram error: {response.json().get('description')}"); return False
    except requests.exceptions.RequestException as e: logging.error(f"Telegram network error: {e}"); st.error(f"Network error: {e}"); return False
    except Exception as e: logging.exception("Telegram unexpected error."); st.error(f"Unexpected error: {e}"); return False


# --- Email Body Formatting Function (MODIFIED) ---
def format_itinerary_for_email(itinerary: Itinerary, preferences: UserPreferences) -> str:
    if not itinerary or not preferences: return "Error: Missing itinerary/preference data."
    lines = []
    lines.append(f"Itinerary for {preferences.name}")
    lines.append("="*40)
    lines.append("\nPreferences:")
    lines.append(f"- Climate: {preferences.climate_preference.title()}")
    lines.append(f"- Activities: {', '.join(preferences.activity_preferences)}")
    lines.append(f"- Budget: {preferences.budget.title()}")
    lines.append(f"- Pace: {preferences.travel_pace.title()}")
    lines.append("\n" + "="*40 + "\n")

    for idx, dest in enumerate(itinerary.destinations):
        if not isinstance(dest, DestinationDetail): continue
        lines.append(f"Destination {idx+1}: {getattr(dest, 'name', 'N/A')}")
        lines.append("-" * len(f"Destination {idx+1}: {getattr(dest, 'name', 'N/A')}"))

        # --- Nested Function Modification ---
        def format_section_simplified(title, content):
            lines.append(f"\n{title}:")
            formatted_content = "N/A" # Default if content is empty or None
            if isinstance(content, list):
                if content:
                    # Join list items into a single comma-separated string
                    formatted_content = ", ".join(str(item).replace('\n', ' ').strip() for item in content) # Added replace newline
            elif content is not None:
                 formatted_content = str(content).replace('\n', ' ').strip() # Added replace newline
            lines.append(formatted_content) # Append the (potentially simplified) content
        # --- End Nested Function Modification ---

        format_section_simplified("Duration", getattr(dest, 'suggested_duration_days', None))
        format_section_simplified("Accommodation", getattr(dest, 'suggested_accommodation_type', None))
        format_section_simplified("Cost Level", getattr(dest, 'estimated_cost_level', 'N/A').title())
        format_section_simplified("Why it Fits", getattr(dest, 'why_it_fits', [])) # Uses simplified format
        format_section_simplified("Activities", getattr(dest, 'suggested_activities', [])) # Uses simplified format
        format_section_simplified("Food", getattr(dest, 'food_highlights', [])) # Uses simplified format
        format_section_simplified("Transport", getattr(dest, 'transportation_notes', [])) # Uses simplified format
        format_section_simplified("Daily Focus", getattr(dest, 'sample_daily_focus', [])) # Uses simplified format

        day_trip = getattr(dest, 'potential_day_trip', None)
        if day_trip: format_section_simplified("Day Trip", day_trip)
        lines.append("\n" + "="*40 + "\n")

    lines.append("Overall Reasoning:")
    # Simplify reasoning too, just in case
    reasoning = getattr(itinerary, 'overall_reasoning', 'N/A')
    lines.append(reasoning.replace('\n', ' ').strip() if reasoning else 'N/A')

    body_text = "\n".join(lines)
    # Log the exact body being generated for debugging
    logging.info(f"Formatted email body (simplified):\n------\n{body_text}\n------")
    return body_text
# --- End Email Body Formatting Function ---


# --- UI Rendering Functions ---
def display_login():
    st.header("Welcome!"); name_input = st.text_input("Enter name:", key="login_name")
    if st.button("Start", key="start_btn"):
        if name_input: user_id = name_input.strip().lower().replace(" ", "_"); st.session_state.user_id = user_id; st.session_state.preferences = get_prefs_from_session(user_id); st.session_state.itinerary = None; st.session_state.show_modify_form = False; st.session_state.app_state = 'collecting_prefs'; logging.info(f"User '{name_input}' started."); st.rerun()
        else: st.warning("Enter name.")

def display_preference_form(existing_prefs: UserPreferences | None):
    user_display_name = st.session_state.user_id.replace('_', ' ').title(); st.header(f"Preferences for {user_display_name}")
    use_existing = False;
    if existing_prefs: st.info("Found saved preferences!"); use_existing = st.checkbox("Use saved?", value=True, key="use_existing_prefs")
    default_loc = existing_prefs.location if use_existing and existing_prefs else ""; default_clim = existing_prefs.climate_preference if use_existing and existing_prefs else "cold"; default_act = ", ".join(existing_prefs.activity_preferences) if use_existing and existing_prefs else "food, art"; default_bud = existing_prefs.budget if use_existing and existing_prefs else "medium"; default_pace = existing_prefs.travel_pace if use_existing and existing_prefs else "relaxed"
    clim_opts = ["cold", "moderate", "tropical"]; bud_opts = ["low", "medium", "high"]; pace_opts = ["relaxed", "moderate", "fast"]
    try: clim_idx = clim_opts.index(default_clim)
    except ValueError: clim_idx = 0
    default_bud = default_bud if default_bud in bud_opts else bud_opts[1]; default_pace = default_pace if default_pace in pace_opts else pace_opts[0]
    with st.form(key="prefs_form"):
        loc = st.text_input("Location", default_loc, key="p_loc"); clim = st.selectbox("Climate", clim_opts, clim_idx, key="p_clim"); act_str = st.text_input("Activities", default_act, key="p_act"); bud = st.select_slider("Budget", bud_opts, default_bud, key="p_bud"); pace = st.select_slider("Pace", pace_opts, default_pace, key="p_pace")
        submitted = st.form_submit_button("Generate")
        if submitted:
            if not all([loc, clim, act_str, bud, pace]): st.error("Fill all fields.")
            else:
                act_list = [a.strip().lower() for a in act_str.split(",") if a.strip()]
                if not act_list: st.error("Enter activities.")
                else:
                    prefs = UserPreferences(name=user_display_name, location=loc, climate_preference=clim, activity_preferences=act_list, budget=bud, travel_pace=pace); st.session_state.preferences = prefs; store_prefs_in_session(st.session_state.user_id, prefs)
                    st.session_state.itinerary = None; st.session_state.error_message = None; st.session_state.show_modify_form = False; st.session_state.app_state = 'showing_itinerary'; logging.info(f"Prefs updated for {st.session_state.user_id}."); st.rerun()

def display_itinerary(itinerary: Itinerary, prefs: UserPreferences):
    # (Display itinerary should remain as before to show rich formatting in UI)
    st.header("✨ Your Itinerary ✨"); st.subheader("Based on Preferences:")
    cols = st.columns(2);
    with cols[0]: st.markdown(f"**Climate:** {prefs.climate_preference.title()}"); st.markdown(f"**Budget:** {prefs.budget.title()}")
    with cols[1]: st.markdown(f"**Activities:** {', '.join(prefs.activity_preferences)}"); st.markdown(f"**Pace:** {prefs.travel_pace.title()}")
    st.divider();
    if not itinerary or not isinstance(itinerary, Itinerary) or not itinerary.destinations: st.error("Invalid itinerary."); logging.warning("Display invalid itinerary."); return
    try:
        for idx, dest in enumerate(itinerary.destinations):
            if not isinstance(dest, DestinationDetail): logging.warning(f"Skip invalid dest {idx}"); continue
            with st.expander(f"📍 Dest {idx+1}: {getattr(dest, 'name', 'N/A')}", expanded=(idx==0)):
                st.markdown(f"**Duration:** {getattr(dest, 'suggested_duration_days', 'N/A')}"); st.markdown(f"**Accommodation:** {getattr(dest, 'suggested_accommodation_type', 'N/A')}"); st.markdown(f"**Cost Level:** {getattr(dest, 'estimated_cost_level', 'N/A').title()}")
                def display_list_items(title, attribute_name):
                    st.markdown(f"**{title}:**"); items = getattr(dest, attribute_name, [])
                    if isinstance(items, list) and items:
                        for item in items: st.markdown(f"- {item}")
                    else: st.caption("N/A")
                display_list_items("Why it Fits", 'why_it_fits'); display_list_items("Activities", 'suggested_activities'); display_list_items("Food Highlights", 'food_highlights'); display_list_items("Transportation", 'transportation_notes'); display_list_items("Daily Focus", 'sample_daily_focus')
                day_trip = getattr(dest, 'potential_day_trip', None);
                if day_trip: st.markdown(f"**Day Trip:** {day_trip}")
        st.divider(); st.subheader("💡 Overall Reasoning:"); st.markdown(getattr(itinerary, 'overall_reasoning', 'N/A'))
    except Exception as e: st.error(f"Display error: {e}"); logging.exception("Display itinerary error.")

def display_modification_form(current_prefs: UserPreferences):
    # (Keep as before)
    st.subheader("Modify Preferences");
    with st.form("modify_prefs_form"):
        st.write("Change & regenerate:"); clim_opts=["cold", "moderate", "tropical"]; bud_opts=["low", "medium", "high"]; pace_opts=["relaxed", "moderate", "fast"]
        try: clim_idx = clim_opts.index(current_prefs.climate_preference)
        except ValueError: clim_idx = 0
        def_bud = current_prefs.budget if current_prefs.budget in bud_opts else bud_opts[1]; def_pace = current_prefs.travel_pace if current_prefs.travel_pace in pace_opts else pace_opts[0]
        mod_clim = st.selectbox("Climate", clim_opts, clim_idx, key="mf_clim"); mod_act_str = st.text_input("Activities", ", ".join(current_prefs.activity_preferences), key="mf_act"); mod_bud = st.select_slider("Budget", bud_opts, def_bud, key="mf_bud"); mod_pace = st.select_slider("Pace", pace_opts, def_pace, key="mf_pace")
        submitted = st.form_submit_button("Regenerate")
        if submitted:
            act_list = [a.strip().lower() for a in mod_act_str.split(",") if a.strip()]
            if not act_list: st.error("Enter activities.")
            else:
                mod_prefs = UserPreferences(name=current_prefs.name, location=current_prefs.location, climate_preference=mod_clim, activity_preferences=act_list, budget=mod_bud, travel_pace=mod_pace)
                if mod_prefs != current_prefs:
                    st.session_state.preferences = mod_prefs; store_prefs_in_session(st.session_state.user_id, mod_prefs); st.info("Prefs updated & saved. Regenerating..."); logging.info(f"Prefs modified for {st.session_state.user_id}.")
                    st.session_state.itinerary = None; st.session_state.error_message = None; st.session_state.show_modify_form = False; st.session_state.app_state = 'showing_itinerary'; st.rerun()
                else: st.info("No changes.")


# --- Main App Logic ---
st.set_page_config(layout="wide", page_title="AI Travel Agent")
st.title("AI Travel Agent ✈️")

# --- Sidebar ---
# (Keep sidebar code exactly as before)
st.sidebar.title("Controls & Info"); st.sidebar.divider(); st.sidebar.subheader("🧠 User Memory");
if not st.session_state.get('memory_store'): st.sidebar.caption("No users stored.")
else:
    sorted_ids = sorted(st.session_state.memory_store.keys())
    for uid in sorted_ids:
        mem_data = st.session_state.memory_store[uid]
        if isinstance(mem_data, UserMemory) and hasattr(mem_data, 'preferences'):
            prefs = mem_data.preferences; name = prefs.name if hasattr(prefs, 'name') else uid
            with st.sidebar.expander(f"User: {name} ({uid})"):
                try: st.json(prefs.model_dump(), expanded=False)
                except Exception as e: st.warning(f"Can't display: {e}")
        else: st.sidebar.warning(f"Invalid entry: {uid}")
st.sidebar.divider(); st.sidebar.subheader("📜 Log")
log_content = st.session_state.log_stream.getvalue()
if not log_content: st.sidebar.caption("No logs.")
else: st.sidebar.text_area("Logs", value=log_content, height=300, key="log_disp", disabled=True)
if st.sidebar.button("Clear Log"): st.session_state.log_stream.truncate(0); st.session_state.log_stream.seek(0); logging.info("Log cleared."); st.rerun()


# --- Main Panel Logic ---
current_state = st.session_state.get('app_state', 'login')

if current_state == 'login':
    display_login()

elif current_state == 'collecting_prefs':
    if not st.session_state.get('user_id'): logging.warning("State 'collecting' no user_id."); st.session_state.app_state = 'login'; st.rerun()
    else: display_preference_form(st.session_state.preferences)

elif current_state == 'showing_itinerary':
    if not st.session_state.get('preferences'): st.warning("Prefs missing."); st.session_state.app_state = 'collecting_prefs'; st.rerun()
    if client is None: st.error("Client not available."); st.stop() # Ensure client is valid

    # Generate itinerary if needed
    if st.session_state.itinerary is None and st.session_state.error_message is None:
        logging.info("Generating itinerary...")
        with st.spinner('🧠 Calling AI...'):
            try:
                st.session_state.itinerary = make_decision(client, st.session_state.preferences) # Use client from config
                st.session_state.error_message = None
                if st.session_state.itinerary: logging.info("Itinerary generated.")
                elif not st.session_state.error_message: st.session_state.error_message = "Failed."; logging.error("make_decision None.")
            except Exception as e: st.session_state.error_message = f"Error: {e}"; st.session_state.itinerary = None; logging.exception("make_decision exc.")

    # Display Itinerary (if successful)
    if st.session_state.itinerary:
        display_itinerary(st.session_state.itinerary, st.session_state.preferences) # Display retains rich formatting
        st.divider()

        # --- Action Buttons Section ---
        st.subheader("Export Itinerary")
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1: # PDF Download
            if st.session_state.preferences:
                try:
                     pdf_bytes = create_itinerary_pdf(st.session_state.itinerary, st.session_state.preferences) # PDF uses original rich format
                     st.download_button(label="📄 Download PDF", data=pdf_bytes, file_name=f"itinerary_{st.session_state.user_id}.pdf", mime="application/pdf", key="pdf_dl")
                except Exception as e: st.error(f"PDF failed: {e}"); logging.exception("PDF gen failed.")

        with col2: # Telegram Send
             if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                 if st.button("📲 Send to Telegram", key="telegram_btn"):
                     pdf_bytes_tg = create_itinerary_pdf(st.session_state.itinerary, st.session_state.preferences) # PDF uses original rich format
                     with st.spinner("Sending..."):
                         success = send_pdf_to_telegram(pdf_bytes=pdf_bytes_tg, user_name=st.session_state.preferences.name, bot_token=TELEGRAM_BOT_TOKEN, chat_id=TELEGRAM_CHAT_ID)
                         if success: st.success("Sent to Telegram!")
             else: st.caption("Telegram not configured.")

        with col3: # Email Sending UI
            st.markdown("**Send via Email**")
            email_recipient = st.text_input("Recipient Email:", value="abc@gmail.com", key="email_recipient_input", label_visibility="collapsed", placeholder="abc@gmail.com")
            if st.button("✉️ Send Email", key="email_send_btn"):
                if not email_recipient or "@" not in email_recipient:
                    st.warning("Please enter a valid recipient email address.")
                else:
                    # Use the MODIFIED function to get a SIMPLIFIED body for the command line
                    email_body = format_itinerary_for_email(st.session_state.itinerary, st.session_state.preferences)
                    email_subject = "AI Travel Plan"
                    # Construct the user query with the simplified body
                    user_query = f"Send email to {email_recipient} subject {email_subject} body {email_body}"
                    logging.info(f"Preparing email command for: {email_recipient}")
                    # Log the query being sent (which includes the simplified body)
                    logging.debug(f"Executing command with query: {user_query}")

                    with st.spinner("Executing email command..."):
                        process_result = None
                        try:
                            script_path = "src/gmail_mcp_server/gmail/client.py"
                            if not os.path.exists(script_path):
                                 st.error(f"Error: Script '{script_path}' not found.")
                                 logging.error(f"MCP script not found: {script_path}")
                            else:
                                env = os.environ.copy(); env["PYTHONIOENCODING"] = "utf-8"
                                # Using the previous fix for subprocess output handling (stdout=DEVNULL)
                                process_result = subprocess.run(
                                    ["python", script_path, user_query], # user_query now has simplified body
                                    text=True,
                                    stdout=subprocess.DEVNULL, # Keep suppressing stdout
                                    stderr=subprocess.PIPE,    # Capture stderr for errors
                                    check=True,
                                    env=env,
                                    timeout=60
                                )
                                st.success("Email command executed successfully!")
                                if process_result and process_result.stderr:
                                     logging.warning(f"MCP script stderr (on success):\n{process_result.stderr}")

                        except subprocess.CalledProcessError as e:
                            st.error(f"Email command failed (Code: {e.returncode}):")
                            st.text("Error Output (from script):")
                            st.code(e.stderr) # Display stderr ONLY on failure
                            logging.error(f"MCP script failed:\n{e.stderr}")
                        except subprocess.TimeoutExpired: st.error("Email command timed out."); logging.error("MCP script timed out.")
                        except Exception as e: st.error(f"Error running script: {e}"); logging.exception("Subprocess error.")
        # --- End Action Buttons ---
        st.divider()

        # --- Modification Section Trigger ---
        if not st.session_state.get('show_modify_form', False):
            if st.button("✏️ Modify Preferences?", key="show_modify_btn"):
                 st.session_state.show_modify_form = True; st.rerun()

    # Display Error Message
    if st.session_state.error_message: st.error(st.session_state.error_message)

    # Display Modification Form
    if st.session_state.get('show_modify_form', False) and st.session_state.preferences:
        display_modification_form(st.session_state.preferences)
        if st.button("Cancel Modification", key="cancel_mod_btn"):
             st.session_state.show_modify_form = False; st.rerun()

    # Start Over Button
    st.divider()
    if st.button("Start Over / Change User", key="start_over"):
        logging.info("Start Over clicked.")
        keys_to_reset = ['user_id', 'preferences', 'itinerary', 'error_message', 'show_modify_form']
        for key in keys_to_reset:
            if key in st.session_state: del st.session_state[key]
        st.session_state.app_state = 'login'; st.rerun()

else: # Invalid state fallback
    st.error("Invalid app state."); logging.error(f"Invalid state: {current_state}. Resetting.")
    st.session_state.app_state = 'login'; st.rerun()