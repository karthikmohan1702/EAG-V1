import os
import asyncio
import json
import traceback
import logging # Added
from concurrent.futures import TimeoutError
from typing import Optional, Any, Dict, Type

# --- Pydantic and Settings ---
from pydantic import BaseModel, Field, ValidationError, create_model
from pydantic_settings import BaseSettings, SettingsConfigDict

# --- Required for .env loading ---
from dotenv import load_dotenv # Still useful for pydantic-settings discovery

# --- MCP and GenAI ---
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import google.generativeai as genai
import argparse

# --- Basic Logging Configuration ---
# Configure logging to output to console with a specific format and level
# Adjust level to logging.DEBUG for more verbose output if needed
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
# --- End Logging Configuration ---


# --- Configuration via Pydantic Settings ---
# -----------
parser = argparse.ArgumentParser(description="A simple script example.")
parser.add_argument("user_query")
args = parser.parse_args() # Run the renamed main function
# -----------
# Determine base directory for correct .env path finding relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Settings(BaseSettings):
    # Configure Pydantic Settings
    # Load from .env file, ignore extra environment variables
    model_config = SettingsConfigDict(extra='ignore')

    # Define configuration fields
    GEMINI_API_KEY: str
    LLM_MODEL: str = "gemini-2.0-flash" # Using 1.5 Flash as per previous script
    LLM_TIMEOUT_SECONDS: int = 30
    MAX_ITERATIONS: int = 10
    # Define paths relative to the project root (where the client is run)
    SERVER_SCRIPT_PATH: str = "src/gmail_mcp_server/gmail/server.py"
    CREDS_FILE_PATH: str = "src/gmail_mcp_server/gmail/client_secrets.json"
    TOKEN_PATH: str = "src/gmail_mcp_server/gmail/token.json"

# Load settings - raises validation error if GEMINI_API_KEY is missing in .env
try:
    settings = Settings()
    logging.info(f"Settings loaded successfully. Attempted loading from: {settings.model_config.get('env_file')}")
except ValidationError as e:
    logging.error(f"Configuration Error: Failed to load settings.")
    logging.error(e) # Log the validation error details
    exit(1) # Exit if config is invalid

# --- API Key Setup (using loaded settings) ---
logging.info("GEMINI_API_KEY found in settings.")
genai.configure(api_key=settings.GEMINI_API_KEY)
# --- End API Key Setup ---


# --- Global State (Consider moving into a class later) ---
iteration_context = [] # Stores history for the LLM
called_functions_history = set() # Prevents exact same function calls


# --- Helper Functions ---

async def generate_with_timeout(prompt: str, timeout: int = settings.LLM_TIMEOUT_SECONDS) -> str:
    """Generate content with Gemini, handling potential timeouts."""
    logging.info(f"Generating LLM response (model: {settings.LLM_MODEL})...")
    try:
        model = genai.GenerativeModel(settings.LLM_MODEL)
        response = await asyncio.wait_for(
            asyncio.to_thread(
                model.generate_content, contents=prompt
            ),
            timeout=timeout
        )
        logging.info("LLM generation completed.")
        if not response.parts:
            logging.warning("LLM response has no parts.")
            if response.prompt_feedback.block_reason:
                logging.warning(f"Prompt blocked: {response.prompt_feedback.block_reason}")
                logging.warning(f"Safety Ratings: {response.prompt_feedback.safety_ratings}")
            return "ERROR: LLM generation failed (no content/blocked)."
        if hasattr(response, 'text'):
             return response.text.strip()
        else:
            logging.warning("LLM response object does not have a 'text' attribute.")
            return "ERROR: LLM response format unexpected (no text attribute)."
    except TimeoutError:
        logging.error(f"LLM generation timed out after {timeout} seconds!")
        return "ERROR: LLM generation timed out."
    except Exception as e:
        # Use logging.exception to include traceback automatically
        logging.exception(f"Error during LLM generation: {e}")
        if "text" in str(e).lower():
            logging.error("   LLM response might be missing the 'text' attribute.")
            return "ERROR: LLM response format issue."
        return f"ERROR: LLM generation failed: {e}"

def reset_state():
    """Reset global state variables."""
    global iteration_context, called_functions_history
    iteration_context = []
    called_functions_history = set()
    logging.info("State reset.")

# --- Dynamic Pydantic Model Creation ---

def create_pydantic_model_from_schema(model_name: str, schema: Dict[str, Any]) -> Type[BaseModel]:
    """Dynamically creates a Pydantic model from a JSON schema dict."""
    fields = {}
    properties = schema.get('properties', {})
    required = schema.get('required', [])

    # Basic JSON Schema type to Python type mapping
    type_mapping = {
        'string': str,
        'integer': int,
        'number': float,
        'boolean': bool,
        'array': list, # Note: Does not specify item types
        'object': dict, # Note: Does not specify nested structure
    }

    for name, prop_schema in properties.items():
        if not isinstance(prop_schema, dict): continue # Skip malformed property schemas

        field_type_str = prop_schema.get('type', 'string')
        # Map schema type to Python type, default to Any if unknown
        field_type = type_mapping.get(field_type_str, Any)

        description = prop_schema.get('description')
        default_value = prop_schema.get('default') # Pydantic handles default logic

        # Create Field definition
        field_definition_args = {}
        if description:
            field_definition_args['description'] = description

        if name in required:
            # Required field: Use Ellipsis (...) unless a default is explicitly provided
            field_definition_args['default'] = ... if default_value is None else default_value
            field_annotation = field_type
        else:
            # Optional field: Use Optional[type] and provide default
            field_definition_args['default'] = default_value # Can be None
            # Make type annotation Optional[T] unless default is explicitly not None
            if default_value is None:
                 field_annotation = Optional[field_type]
            else:
                 field_annotation = field_type # If default is set, type hint is just T

        fields[name] = (field_annotation, Field(**field_definition_args))

    # Sanitize model name for Pydantic create_model
    safe_model_name = "".join(c if c.isalnum() else '_' for c in model_name).strip('_')
    if not safe_model_name or not safe_model_name[0].isalpha():
        safe_model_name = "ToolArgs_" + safe_model_name # Ensure valid class name starting with letter

    try:
        DynamicModel = create_model(safe_model_name, **fields)
        # Add a docstring for clarity
        DynamicModel.__doc__ = f"Auto-generated Pydantic model for arguments of tool '{model_name}'."
        return DynamicModel
    except Exception as e:
        # Use logging.exception here as well if you want the traceback for model creation failure
        logging.error(f"Error creating Pydantic model '{safe_model_name}': {e}")
        raise # Re-raise to indicate failure


# --- Main Client Logic ---

async def main_async():
    """Main async function to run the Gmail MCP client."""
    # Access global state (consider class-based approach for larger apps)
    global iteration_context, called_functions_history

    reset_state() # Reset at the start
    logging.info("Starting Gmail MCP Client...")
    tool_map: Dict[str, types.Tool] = {} # Stores MCP Tool objects
    tool_arg_models: Dict[str, Type[BaseModel]] = {} # Stores Pydantic models for tool args

    try:
        # --- Define server_params using loaded settings ---
        logging.info(f"Defining server parameters to run: {settings.SERVER_SCRIPT_PATH}")
        server_params = StdioServerParameters(
            command="python", # Or python3 if needed
            args=[
                settings.SERVER_SCRIPT_PATH,
                "--creds-file-path", settings.CREDS_FILE_PATH,
                "--token-path", settings.TOKEN_PATH
            ]
        )

        logging.info("Attempting to connect to MCP server via stdio...")
        async with stdio_client(server_params) as (read, write):
            logging.info("Connection established.")
            logging.info("Creating MCP session...")
            async with ClientSession(read, write) as session:
                logging.info("Session created. Initializing...")
                await session.initialize()
                logging.info("Session initialized.")

                # --- 2. Get Available Tools & Create Pydantic Models ---
                logging.info("Requesting tool list from server...")
                try:
                    tools_result = await session.list_tools()
                    tools = tools_result.tools
                    if not tools:
                        logging.warning("No tools reported by the server. Exiting.")
                        return
                    logging.info(f"Successfully retrieved {len(tools)} tools:")

                    for tool in tools:
                        tool_map[tool.name] = tool # Store original tool object
                        logging.info(f"Found Tool: {tool.name} ({getattr(tool, 'description', 'No description')})")
                        try:
                            schema = getattr(tool, 'inputSchema', {})
                            # Create model only if schema is dict and has properties
                            if isinstance(schema, dict) and schema.get('properties'):
                                 ArgModel = create_pydantic_model_from_schema(tool.name, schema)
                                 tool_arg_models[tool.name] = ArgModel # Store Pydantic model
                                 logging.info(f"   - Created Pydantic model '{ArgModel.__name__}' for arguments.")
                            else:
                                 logging.info(f"   - Tool has no input properties or invalid schema; Pydantic model not created.")
                        except Exception as e:
                            # Using logging.exception to include traceback for model creation failure
                            logging.exception(f"Failed to create Pydantic model for tool '{tool.name}': {e}")

                except Exception as e:
                    logging.exception(f"Error retrieving tools or creating models: {e}")
                    return

                # --- 3. Create System Prompt for LLM ---
                logging.info("Creating system prompt for LLM...")
                # (This part remains largely the same, using tool_map for descriptions)
                tools_description_list = []
                for i, (name, tool) in enumerate(tool_map.items()):
                    try:
                        schema = getattr(tool, 'inputSchema', {})
                        if not isinstance(schema, dict): schema = {}

                        params_dict = schema.get('properties', {})
                        param_details = []
                        required_params = schema.get('required', [])
                        for param_name, param_info in params_dict.items():
                            param_type = param_info.get('type', 'any') if isinstance(param_info, dict) else 'any'
                            required_marker = "(required)" if param_name in required_params else "(optional)"
                            param_desc = param_info.get('description', '') if isinstance(param_info, dict) else ''
                            param_details.append(f"{param_name}: {param_type} {required_marker} {f'- {param_desc}' if param_desc else ''}")

                        params_str = "\n     Parameters:\n       " + "\n       ".join(param_details) if param_details else "   Parameters: None"
                        tool_desc = f"{i+1}. {name}:\n   Description: {getattr(tool, 'description', 'No description available')}\n{params_str}"
                        tools_description_list.append(tool_desc)
                    except Exception as e:
                        logging.error(f"Error processing tool description for {name}: {e}")
                        tools_description_list.append(f"{i+1}. {name} - Error processing description")

                tools_description = "\n".join(tools_description_list)

                # --- Define the System Prompt (with updated rule and example) ---
                system_prompt = f"""You are an assistant that interacts with Gmail using available tools.

Available Gmail tools:
{tools_description}

You MUST respond with EXACTLY ONE line in one of these formats (no extra text, explanations, or formatting):
1. To call a tool:
   FUNCTION_CALL: tool_name|param_name1=param_value1|param_name2=param_value2|...
   - Use the exact tool name. Provide parameters as key=value pairs, separated by '|'.
   - For tools with no parameters, use: FUNCTION_CALL: tool_name

2. When the task is fully complete or you cannot proceed:
   FINAL_ANSWER: [Your final message to the user]

Important Rules:
- Analyze the request and the conversation history. Choose the single best tool.
# --- NEW RULE ADDED HERE ---
- If the user asks to perform an action (like sending an email or reading a specific email) but does not provide all the required information (like recipient/subject/body for sending, or message ID for reading), YOU MUST ASK THE USER FOR THE MISSING DETAILS FIRST using a FINAL_ANSWER. Do not call the function with placeholder, assumed, or hallucinated values.
# --- END NEW RULE ---
- Use the correct parameters based on the tool's schema.
- Do NOT call the same function with the exact same arguments repeatedly. Check the history.
- Provide a FINAL_ANSWER only when all steps of the request are done or if you are stuck/cannot proceed/need more info.
- If the server returns an error, explain it in the FINAL_ANSWER or try a different approach if appropriate.
- Be concise.

Example Interaction:
User Query: Send an email to test@example.com with subject "Hello" and body "Hi there".
LLM Response: FUNCTION_CALL: send-email|recipient_id=test@example.com|subject=Hello|message=Hi there
Server Response: {{'message': 'Email sent successfully', 'messageId': '123abc456def'}}
LLM Response: FINAL_ANSWER: Email sent successfully to test@example.com.

User Query: What are my latest 3 emails?
LLM Response: FUNCTION_CALL: get-unread-emails|max_results=3
Server Response: [{{'subject': 'Sub1', 'sender': 'a@b.com', 'snippet': 'Snip1'}}, {{'subject': 'Sub2', 'sender': 'c@d.com', 'snippet': 'Snip2'}}]
LLM Response: FINAL_ANSWER: Your latest 3 unread emails are: 1. Subject: Sub1, From: a@b.com...

# --- NEW EXAMPLE ADDED HERE ---
Example Interaction (Clarification):
User Query: Send an email please.
LLM Response: FINAL_ANSWER: Okay, I can help with that. Who should I send the email to, what should the subject be, and what message do you want to send?
User Query: Send it to manager@work.com with subject "Report" and body "Here is the weekly report.".
LLM Response: FUNCTION_CALL: send-email|recipient_id=manager@work.com|subject=Report|message=Here is the weekly report.
Server Response: {{'message': 'Email sent successfully', 'messageId': '...'}}
LLM Response: FINAL_ANSWER: Okay, I've sent the email to manager@work.com.
# --- END NEW EXAMPLE ---

Now, await the user's query.
"""
                logging.info("System prompt created.")

                # --- 4. Define Task & Start Interaction Loop ---
                query = args.user_query
                if not query:
                    logging.warning("No query entered. Exiting.")
                    return

                logging.info(f"Starting interaction loop for query: \"{query}\" (Max iterations: {settings.MAX_ITERATIONS})")

                current_context = f"{system_prompt}\n\nUser Query: {query}"
                iteration = 0 # Local iteration counter for the loop

                while iteration < settings.MAX_ITERATIONS:
                    logging.info(f"--- Iteration {iteration + 1}/{settings.MAX_ITERATIONS} ---")

                    # --- Build Prompt ---
                    full_prompt = current_context
                    if iteration_context:
                        full_prompt += "\n\nConversation History:\n" + "\n".join(iteration_context)
                    full_prompt += "\n\nWhat is the next step? Respond in the required format (FUNCTION_CALL or FINAL_ANSWER)."

                    # --- 5. Get LLM Action ---
                    llm_response = await generate_with_timeout(full_prompt)

                    if not llm_response or llm_response.startswith("ERROR:"):
                        logging.error(f"LLM failed or returned error. Aborting. Last error: {llm_response}")
                        break # Exit loop

                    logging.info(f"LLM Response: {llm_response}")

                    # --- 6. Parse LLM Action ---
                    if llm_response.startswith("FUNCTION_CALL:"):
                        try:
                            # --- Extract and Check Duplicate ---
                            call_str = llm_response.replace("FUNCTION_CALL:", "").strip()
                            parts = call_str.split('|')
                            func_name = parts[0].strip()
                            raw_params = parts[1:]
                            call_signature = f"{func_name}|{'|'.join(sorted(raw_params))}"

                            if call_signature in called_functions_history:
                                logging.warning(f"LLM attempted to repeat exact call: {call_signature}. Asking again.")
                                iteration_context.append(f"System note: You just tried calling '{call_signature}', which was already executed. Please choose a different action or provide a FINAL_ANSWER.")
                                continue # Skip rest, ask LLM again

                            if func_name not in tool_map:
                                raise ValueError(f"LLM called unknown tool: '{func_name}'. Available tools: {list(tool_map.keys())}")

                            # --- Parse key=value args ---
                            provided_args = {}
                            for param_part in raw_params:
                                if '=' not in param_part:
                                    logging.warning(f"Skipping invalid parameter format: '{param_part}' (expected key=value)")
                                    continue
                                key, value = param_part.split('=', 1)
                                provided_args[key.strip()] = value.strip()
                            # Consider logging arguments at DEBUG level if too verbose for INFO
                            logging.info(f"Parsed Call - Function: {func_name}, Raw Args: {provided_args}")

                            # --- Validate with Pydantic ---
                            arguments_to_send = {} # Default to empty dict
                            if func_name in tool_arg_models:
                                ArgModel = tool_arg_models[func_name]
                                logging.info(f"Validating args for '{func_name}' using Pydantic model '{ArgModel.__name__}'...")
                                try:
                                        validated_args_model = ArgModel(**provided_args)
                                        # Use .model_dump() to get dict, exclude None values if desired
                                        arguments_to_send = validated_args_model.model_dump(exclude_none=True)
                                        logging.info(f"Pydantic validation successful. Args to send: {arguments_to_send}")
                                except ValidationError as e:
                                        logging.error(f"Pydantic validation failed for {func_name}:")
                                        # Provide detailed error feedback to LLM
                                        error_details = "; ".join([f"'{err['loc'][0]}': {err['msg']}" for err in e.errors()])
                                        raise ValueError(f"Invalid arguments provided for {func_name}. Errors: {error_details}") from e
                            elif provided_args:
                                # Tool exists but has no Pydantic model (likely no args defined in schema)
                                # BUT the LLM provided args anyway. Raise an error or warn.
                                logging.warning(f"LLM provided arguments {provided_args} for tool '{func_name}' which expects no arguments based on schema. Ignoring provided args.")
                                arguments_to_send = {} # Ensure empty args sent
                            else:
                                # Tool exists, no Pydantic model, no args provided by LLM - Correct for no-arg tools
                                logging.info(f"Tool '{func_name}' expects no arguments, and none were provided.")
                                arguments_to_send = {}


                            # --- 7. Execute Tool Call ---
                            logging.info(f"Calling tool '{func_name}' on server with validated args: {arguments_to_send}")
                            tool_result = await session.call_tool(func_name, arguments=arguments_to_send)
                            # Consider logging raw result at DEBUG level
                            logging.info(f"Raw server result: {tool_result}")

                            # --- Process Result for Context ---
                            result_content = "Tool execution successful, but no specific content returned."
                            result_content_for_context = result_content
                            if tool_result.content and isinstance(tool_result.content, list) and len(tool_result.content) > 0:
                                content_part = tool_result.content[0]
                                if hasattr(content_part, 'text'): result_content = content_part.text
                                elif isinstance(content_part, (str, bytes)): result_content = str(content_part)
                                else: result_content = repr(content_part)
                                try:
                                        if isinstance(result_content, str) and result_content.strip().startswith(('[', '{')) and result_content.strip().endswith((']', '}')):
                                            parsed_json = json.loads(result_content)
                                            result_content_for_context = json.dumps(parsed_json, indent=2)
                                            # Consider logging parsed result at DEBUG level
                                            logging.info(f"Server Result (parsed JSON): {result_content_for_context}")
                                        else:
                                            result_content_for_context = result_content
                                            logging.info(f"Server Result (text/other): {result_content}")
                                except json.JSONDecodeError:
                                        result_content_for_context = result_content
                                        logging.info(f"Server Result (text, not valid JSON): {result_content}")
                                except Exception as json_ex:
                                        logging.error(f"Error processing result content for context: {json_ex}")
                                        result_content_for_context = result_content
                            else:
                                logging.info("Tool executed, server returned no specific content or content format was unexpected.")

                            # --- Update History ---
                            called_functions_history.add(call_signature)
                            iteration_context.append(f"LLM Action: {llm_response}")
                            iteration_context.append(f"Server Response: {result_content_for_context}")

                        except (ValidationError, ValueError, Exception) as e: # Catch Pydantic & other errors
                            logging.error(f"Error processing FUNCTION_CALL: {e}")
                            iteration_context.append(f"LLM Action: {llm_response}")
                            iteration_context.append(f"System Error: Failed to process or validate call. Error: {e}. Please analyze the error, check argument format/types, and try again or provide a FINAL_ANSWER.")


                    elif llm_response.startswith("FINAL_ANSWER:"):
                        final_message = llm_response.replace("FINAL_ANSWER:", "").strip()
                        logging.info("===========================================")
                        logging.info(f"LLM provided FINAL_ANSWER: {final_message}")
                        logging.info("===========================================")
                        break # Exit loop

                    else:
                        logging.warning(f"LLM response did not match expected format: {llm_response}")
                        iteration_context.append(f"LLM Response (invalid format): {llm_response}")
                        iteration_context.append("System Note: Your response was not in the correct format. Please respond with either 'FUNCTION_CALL: tool|param=value' or 'FINAL_ANSWER: message'.")

                    iteration += 1 # Increment iteration counter

                if iteration >= settings.MAX_ITERATIONS:
                    logging.warning("===========================================")
                    logging.warning(f"Reached maximum iterations ({settings.MAX_ITERATIONS}). Task may be incomplete.")
                    logging.warning("===========================================")

    except ConnectionRefusedError:
         logging.error(f"Connection Refused: Could not connect to the MCP server. Is the script '{settings.SERVER_SCRIPT_PATH}' runnable and correct?")
    except FileNotFoundError:
         logging.error(f"File Not Found: Ensure the server script exists at '{settings.SERVER_SCRIPT_PATH}' and Python is in your PATH.")
    except Exception as e:
         logging.exception(f"An unexpected error occurred in the main client execution:") # Use .exception here
    finally:
         logging.info("Gmail MCP Client finished.")
         # reset_state() called at start of main_async now


# --- Run the client ---
if __name__ == "__main__":
    # Optional: Windows asyncio policy adjustment
    # if os.name == 'nt':
    #      asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received, shutting down.")