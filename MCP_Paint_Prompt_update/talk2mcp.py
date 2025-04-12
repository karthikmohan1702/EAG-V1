# --- START OF FILE talk2mcp.py ---

import asyncio
import os
import sys
import traceback
from concurrent.futures import TimeoutError
from functools import partial

# Third-party imports
import google.generativeai as genai
from dotenv import load_dotenv
from google.generativeai import configure
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "Neither GEMINI_API_KEY nor GOOGLE_API_KEY found in environment variables or .env file."
        )
try:
    configure(api_key=api_key)
    print("Google AI SDK configured successfully with API key.")
except Exception as config_error:
    print(f"Error configuring Google AI SDK: {config_error}")
    raise

# Initialize the client
client = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    safety_settings={
        "HARASSMENT": "block_none",
        "HATE_SPEECH": "block_none",
        "SEXUAL": "block_none",
        "DANGEROUS": "block_none",
    },
)

# Global state variables
max_iterations = 8
last_response_content = None
iteration = 0
iteration_history = []
current_phase = 1
phase2_step = 0
final_answer_value = None  # Will store the pure number

# Define fixed coordinates for the rectangle
RECT_X1, RECT_Y1 = 438, 322
RECT_X2, RECT_Y2 = 796, 531

# Calculate text click point slightly inside the top-left corner
TEXT_PADDING = 15
TEXT_CLICK_X = RECT_X1 + TEXT_PADDING
TEXT_CLICK_Y = RECT_Y1 + TEXT_PADDING
TEXT_CLICK_X = min(TEXT_CLICK_X, (RECT_X1 + RECT_X2) // 2)
TEXT_CLICK_Y = min(TEXT_CLICK_Y, (RECT_Y1 + RECT_Y2) // 2)

print(f"Rectangle Coordinates: ({RECT_X1},{RECT_Y1}) to ({RECT_X2},{RECT_Y2})")
print(f"Calculated Text Click Coordinates: ({TEXT_CLICK_X}, {TEXT_CLICK_Y})")


async def generate_with_timeout(model_client, prompt_list, timeout=30):
    """Generate content with a timeout. Accepts list of content parts."""
    print(f"\n--- Starting LLM generation (timeout={timeout}s) ---")
    if not isinstance(prompt_list, list) or not all(
        isinstance(item, dict) for item in prompt_list
    ):
        print("Error: prompt_list must be a list of dictionaries.")
        raise TypeError("Invalid prompt_list format.")
    try:
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                partial(
                    model_client.generate_content,
                    contents=prompt_list,
                    request_options={"timeout": timeout},
                ),
            ),
            timeout=timeout + 5,
        )
        print("--- LLM generation completed ---")
        if not response:
            return ""
        if not hasattr(response, "candidates") or not response.candidates:
            if (
                hasattr(response, "prompt_feedback")
                and response.prompt_feedback.block_reason
            ):
                print(f"LLM response BLOCKED. Reason: {response.prompt_feedback.block_reason}")
            return ""
        try:
            candidate = response.candidates[0]
            finish_reason = getattr(candidate, "finish_reason", None)
            if finish_reason not in ("STOP", "MAX_TOKENS", None):
                print(f"Warning: LLM generation finished with reason: {finish_reason}")
                if finish_reason == "SAFETY":
                    return ""
            content = getattr(candidate, "content", None)
            if content and hasattr(content, "parts") and content.parts:
                return "".join(
                    part.text for part in content.parts if hasattr(part, "text")
                )
            elif content and hasattr(content, "text"):
                return content.text
            else:
                return ""
        except (AttributeError, IndexError, TypeError) as e:
            print(f"Error extracting response text: {e}")
            return ""
    except TimeoutError:
        print(f"LLM generation timed out after {timeout} seconds!")
        raise
    except Exception as e:
        print(f"Error during LLM generation: {type(e).__name__}: {e}")
        raise


def reset_state():
    """Reset relevant global variables to their initial state"""
    global last_response_content, iteration, iteration_history, current_phase, phase2_step, final_answer_value
    last_response_content = None
    iteration = 0
    iteration_history = []
    current_phase = 1
    phase2_step = 0
    final_answer_value = None
    print("Global state reset.")


def build_llm_prompt(system_prompt, user_query, history):
    """Builds the prompt list for the LLM API"""
    messages = [
        {"role": "user", "parts": [system_prompt + "\n\nInitial Query:\n" + user_query]}
    ]
    for entry in history:
        if entry.get("llm_response"):
            messages.append({"role": "model", "parts": [entry["llm_response"]]})
        if entry.get("tool_result"):
            messages.append({"role": "user", "parts": [entry["tool_result"]]})
        else:
            messages.append(
                {
                    "role": "user",
                    "parts": [
                        "Tool execution returned no specific result or action was skipped."
                    ],
                }
            )
    return messages


async def main():
    global iteration, last_response_content, iteration_history, current_phase, phase2_step, final_answer_value
    reset_state()
    print("Starting main execution...")
    try:
        print("Establishing connection to MCP server...")
        server_params = StdioServerParameters(command=sys.executable, args=["custom_server.py"])
        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                await session.initialize()
                print("Initialization successful.")
                print("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"Successfully retrieved {len(tools)} tools.")

                # Generate tool descriptions
                tools_description = []
                for i, tool in enumerate(tools):
                    try:
                        schema = getattr(tool, "inputSchema", {})
                        params = schema.get("properties", {})
                        required_params = schema.get("required", [])
                        param_details = []
                        for name, info in params.items():
                            p_type = info.get("type", "any")
                            p_desc = info.get("description", "")
                            req_star = "*" if name in required_params else ""
                            detail = f"{name}{req_star}({p_type})"
                            if p_desc:
                                detail += f": {p_desc}"
                            param_details.append(detail)
                        params_str = ", ".join(param_details) if param_details else "None"
                        desc = getattr(tool, "description", "No description available")
                        name = getattr(tool, "name", f"tool_{i}")
                        tool_desc = f"- {name}({params_str}): {desc}"
                        tools_description.append(tool_desc)
                    except Exception as e:
                        tools_description.append(
                            f"- Error processing tool '{getattr(tool, 'name', f'unknown_tool_{i}')}'"
                        )
                tools_description_str = "\n".join(tools_description)
                print(f"Tool descriptions generated ({len(tools_description)} entries).")

                final_answer_prefix = "FINAL_ANSWER:"  # Prefix for LLM reporting the number
                text_prefix_in_paint = "FINAL ANSWER - "  # Prefix to actually write in Paint

                # System Prompt
                system_prompt = f"""You are a precise agent assisting with calculations and graphical display using MS Paint. You MUST operate in two distinct phases. Adhere strictly to the response format for each phase.

Available tools:
{tools_description_str}

Your Task: Calculate the sum of the ASCII values for the characters in the string "IN". Then, display this sum in MS Paint by opening Paint, drawing a specific rectangle, and writing the text "{text_prefix_in_paint}[number]" inside it.

---

Phase 1: Calculation & Verification  
Goal: Calculate and verify the sum of ASCII values for "IN".

Steps:
1. Use `FUNCTION_CALL: strings_to_chars_to_int|IN` to retrieve ASCII values.
2. Wait for the response. Verify the output: confirm that the result matches the known ASCII codes for 'I' and 'N' (which are 73 and 78).  
   If incorrect, respond: `ERROR: Unexpected ASCII values for "IN"` and stop.
3. Use `FUNCTION_CALL: add_list|[73, 78]` to calculate the sum.
4. Wait for the result. Verify that the result is 151.
   - If the result is incorrect, respond: `ERROR: Incorrect sum of ASCII values` and stop.
5. Respond ONLY with the final result in the exact format below:
   `FINAL_ANSWER: 151`  
   Do NOT include any other explanation or text.

---

Phase 2: Graphical Display (Begins ONLY after FINAL_ANSWER)

Goal: Display the calculated number prefixed with "{text_prefix_in_paint}" in MS Paint.

Steps (execute strictly in order, one per turn):
1. `FUNCTION_CALL: open_paint`
2. `FUNCTION_CALL: draw_rectangle|{RECT_X1}|{RECT_Y1}|{RECT_X2}|{RECT_Y2}`
3. `FUNCTION_CALL: add_text_in_paint|{text_prefix_in_paint}151|{TEXT_CLICK_X}|{TEXT_CLICK_Y}`  
   - IMPORTANT: The text string must include the literal prefix "{text_prefix_in_paint}" followed by the number from Phase 1 (e.g., `FINAL ANSWER - 151`).

---

IMPORTANT RULES:
- Respond with EXACTLY ONE line per turn: either a `FUNCTION_CALL:` or the `FINAL_ANSWER:`.
- NEVER add extra text or commentary.
- Follow all steps in exact sequence.
- If a tool fails or returns invalid output, report it using `ERROR:` with a short reason.
"""

                query = "Calculate the sum of ASCII values for 'IN', then display it in Paint as described in the instructions."
                print(f"Initial Query: {query}")
                print("Starting interaction loop...")

                # --- Main Loop ---
                while iteration < max_iterations:
                    print(f"\n--- Iteration {iteration + 1}/{max_iterations} ---")
                    print(f"Current Phase: {current_phase}, Phase 2 Step: {phase2_step}")
                    llm_prompt_messages = build_llm_prompt(
                        system_prompt, query, iteration_history
                    )

                    try:
                        print("Querying LLM...")
                        llm_response_text = await generate_with_timeout(
                            client, llm_prompt_messages
                        )
                        llm_response_first_line = llm_response_text.split("\n")[0].strip()
                        print(
                            f"LLM Raw Response (First Line): '{llm_response_first_line}'"
                        )

                        if not llm_response_first_line:
                            print("LLM returned empty line. Stopping.")
                            iteration_history.append(
                                {
                                    "llm_response": llm_response_text,
                                    "tool_result": "LLM provided no actionable response line, stopping.",
                                }
                            )
                            break

                        current_llm_output = llm_response_first_line
                        current_tool_result = (
                            "No specific action taken based on LLM response."
                        )

                        if current_llm_output.startswith("FUNCTION_CALL:"):
                            print("Action: Function Call")
                            if current_phase == 1:
                                print("  Phase 1 call")
                            elif current_phase == 2:
                                print(f"  Phase 2 call (Expected step: {phase2_step+1})")

                            try:
                                parts = current_llm_output.split(":", 1)
                                if len(parts) != 2 or not parts[1]:
                                    raise ValueError(
                                        f"Invalid FUNCTION_CALL format: '{current_llm_output}'"
                                    )
                                function_info = parts[1]
                                params_parts = [p.strip() for p in function_info.split("|")]
                                func_name = params_parts[0]
                                params_str_list = params_parts[1:]
                                if not func_name:
                                    raise ValueError(
                                        f"Invalid FUNCTION_CALL format: Tool name missing in '{current_llm_output}'"
                                    )
                                print(f"  Tool: {func_name}")
                                print(f"  Raw Params: {params_str_list}")

                                # Phase 2 Step Enforcement
                                if current_phase == 2:
                                    expected_tool = ""
                                    if phase2_step == 0:
                                        expected_tool = "open_paint"
                                    elif phase2_step == 1:
                                        expected_tool = "draw_rectangle"
                                    elif phase2_step == 2:
                                        expected_tool = "add_text_in_paint"
                                    if expected_tool and func_name != expected_tool:
                                        print(
                                            f"!!! Strict Plan Deviation: Expected '{expected_tool}', got '{func_name}'. Asking LLM to correct."
                                        )
                                        current_tool_result = f"Error: Incorrect tool called for Phase 2, Step {phase2_step+1}. Expected '{expected_tool}', but received '{func_name}'. Please follow the plan exactly."
                                        iteration_history.append(
                                            {
                                                "llm_response": current_llm_output,
                                                "tool_result": current_tool_result,
                                            }
                                        )
                                        iteration += 1
                                        continue

                                tool = next((t for t in tools if t.name == func_name), None)
                                if not tool:
                                    raise ValueError(
                                        f"Unknown tool '{func_name}' requested by LLM."
                                    )

                                arguments = {}
                                schema = getattr(tool, "inputSchema", {})
                                schema_properties = schema.get("properties", {})
                                param_names_ordered = list(schema_properties.keys())

                                # Parameter Count Check (Correction logic removed for add_text_in_paint)
                                if len(params_str_list) != len(param_names_ordered):
                                    raise ValueError(
                                        f"Incorrect number of parameters for '{func_name}'. Expected {len(param_names_ordered)}, got {len(params_str_list)}."
                                    )

                                # Type Conversion
                                for i, param_name in enumerate(param_names_ordered):
                                    param_info = schema_properties.get(param_name, {})
                                    value_str = params_str_list[i]
                                    param_type = param_info.get("type", "string")
                                    print(
                                        f"    Converting '{value_str}' to {param_type} for '{param_name}'"
                                    )
                                    try:
                                        if param_type == "integer":
                                            arguments[param_name] = int(value_str)
                                        elif param_type == "number":
                                            arguments[param_name] = float(value_str)
                                        elif param_type == "array":
                                            val_inner = (
                                                value_str[1:-1]
                                                if (
                                                    value_str.startswith("[")
                                                    and value_str.endswith("]")
                                                )
                                                else value_str
                                            )
                                            items_str = (
                                                [
                                                    item.strip()
                                                    for item in val_inner.split(",")
                                                    if item.strip()
                                                ]
                                                if val_inner
                                                else []
                                            )
                                            item_schema = param_info.get("items", {})
                                            item_type = item_schema.get(
                                                "type", "string"
                                            )
                                            converted_items = []
                                            for item_s in items_str:
                                                if item_type == "integer":
                                                    converted_items.append(int(item_s))
                                                elif item_type == "number":
                                                    converted_items.append(float(item_s))
                                                else:
                                                    converted_items.append(str(item_s))
                                            arguments[param_name] = converted_items
                                        elif param_type == "string":
                                            arguments[param_name] = str(
                                                value_str
                                            )  # Ensure text param is string
                                        elif param_type == "boolean":
                                            if value_str.lower() in [
                                                "true", "1", "yes", "y"
                                            ]:
                                                arguments[param_name] = True
                                            elif value_str.lower() in [
                                                "false", "0", "no", "n"
                                            ]:
                                                arguments[param_name] = False
                                            else:
                                                raise ValueError(
                                                    f"Invalid boolean value: '{value_str}'"
                                                )
                                        else:
                                            arguments[param_name] = value_str
                                    except ValueError as ve:
                                        raise ValueError(
                                            f"Type conversion error for '{param_name}': Cannot convert '{value_str}' to {param_type}. {ve}"
                                        )

                                # Call Tool
                                print(
                                    f"  Calling tool '{func_name}' with args: {arguments}"
                                )
                                result = await session.call_tool(
                                    func_name, arguments=arguments
                                )
                                print(f"  Raw tool result: {result}")

                                # Process Tool Result
                                tool_executed_successfully = True
                                last_response_content_str = (
                                    "Tool returned no specific content."
                                )
                                if (
                                    result
                                    and hasattr(result, "content")
                                    and isinstance(result.content, list)
                                ):
                                    result_texts = [
                                        item.text
                                        for item in result.content
                                        if isinstance(item, types.TextContent)
                                        and hasattr(item, "text")
                                    ]
                                    last_response_content_str = (
                                        " ".join(result_texts)
                                        if result_texts
                                        else str(result.content)
                                    )
                                    if any("error" in t.lower() for t in result_texts):
                                        tool_executed_successfully = False
                                        print(
                                            f"  Tool reported an error: {last_response_content_str}"
                                        )
                                elif (
                                    result
                                    and isinstance(result, dict)
                                    and "content" in result
                                ):
                                    content_list = result.get("content", [])
                                    result_texts = [
                                        item.get("text", "")
                                        for item in content_list
                                        if isinstance(item, dict)
                                    ]
                                    last_response_content_str = (
                                        " ".join(filter(None, result_texts)) or str(result)
                                    )
                                    if any("error" in t.lower() for t in result_texts):
                                        tool_executed_successfully = False
                                        print(
                                            f"  Tool reported an error: {last_response_content_str}"
                                        )
                                else:
                                    last_response_content_str = (
                                        str(result)
                                        if result is not None
                                        else "Tool returned None."
                                    )
                                    if "error" in last_response_content_str.lower():
                                        tool_executed_successfully = False
                                        print(
                                            f"  Tool result might indicate error: {last_response_content_str}"
                                        )
                                last_response_content = last_response_content_str
                                current_tool_result = f"Tool '{func_name}' executed. Result: {last_response_content}"
                                print(
                                    f"  Formatted Result for History: {current_tool_result}"
                                )
                                if current_phase == 2 and tool_executed_successfully:
                                    phase2_step += 1
                                elif current_phase == 2 and not tool_executed_successfully:
                                    print(
                                        "  Tool failed/error, Phase 2 step not advanced."
                                    )

                            except Exception as e:
                                print(
                                    f"!!! Error processing function call '{func_name}': {type(e).__name__}: {e}"
                                )
                                traceback.print_exc()
                                current_tool_result = (
                                    f"Error processing call for '{func_name}': {str(e)}"
                                )

                        elif current_llm_output.startswith(final_answer_prefix):
                            print("Action: Final Answer")
                            if current_phase == 1:
                                print("Processing Phase 1 Final Answer...")
                                final_answer_parts = current_llm_output.split(":", 1)
                                if len(final_answer_parts) < 2 or not final_answer_parts[
                                    1
                                ].strip():
                                    print(
                                        f"Error: Malformed FINAL_ANSWER: '{current_llm_output}'"
                                    )
                                    current_tool_result = (
                                        "Error: Malformed FINAL_ANSWER line."
                                    )
                                else:
                                    final_answer_str = final_answer_parts[1].strip()
                                    try:
                                        try:
                                            final_answer_value = int(final_answer_str)
                                        except ValueError:
                                            final_answer_value = float(final_answer_str)
                                        print(
                                            f"  Final Answer Calculated: {final_answer_value}"
                                        )
                                        last_response_content = final_answer_value
                                        current_tool_result = f"Phase 1 complete. Final Answer is {final_answer_value}."
                                        print("\n=== Phase 1 Complete, Moving to Phase 2 ===")
                                        current_phase = 2
                                        phase2_step = 0
                                    except ValueError:
                                        print(
                                            f"Error: FINAL_ANSWER not valid number: '{final_answer_str}'"
                                        )
                                        current_tool_result = f"Error: Invalid FINAL_ANSWER format: {final_answer_str}."
                            else:  # Phase 2
                                print("Warning: FINAL_ANSWER during Phase 2. Ignoring.")
                                current_tool_result = (
                                    "Ignored FINAL_ANSWER in Phase 2."
                                )

                        else:
                            print(
                                f"Warning: Unexpected LLM response: '{current_llm_output}'"
                            )
                            current_tool_result = f"Unexpected response: '{current_llm_output}'. Please use FUNCTION_CALL: or FINAL_ANSWER:."

                        # Update History
                        iteration_history.append(
                            {
                                "llm_response": current_llm_output,
                                "tool_result": current_tool_result,
                            }
                        )

                    except TimeoutError:
                        print("LLM Timeout.")
                        iteration_history.append(
                            {"llm_response": "<timeout>", "tool_result": "LLM generation timed out."}
                        )
                        break
                    except Exception as e:
                        print(
                            f"!!! Critical loop error: {type(e).__name__}: {e}"
                        )
                        traceback.print_exc()
                        iteration_history.append(
                            {
                                "llm_response": "<error>",
                                "tool_result": f"Critical loop error: {str(e)}",
                            }
                        )
                        break

                    iteration += 1
                    if current_phase == 2 and phase2_step >= 3:
                        print("\n--- Phase 2 Complete ---")
                        iteration_history.append(
                            {
                                "llm_response": "<task complete>",
                                "tool_result": "Paint operations finished.",
                            }
                        )
                        break

                if iteration >= max_iterations:
                    print("\n--- Max iterations reached ---")
                    iteration_history.append(
                        {
                            "llm_response": "<max iterations>",
                            "tool_result": f"Stopped after {max_iterations} iterations.",
                        }
                    )

                # Final Summary
                print("\n--- Final State ---")
                print(f"Phase: {current_phase}, Phase 2 Step: {phase2_step}")
                if final_answer_value is not None:
                    # Print the final value as requested in previous step
                    print(f"FINAL ANSWER - {final_answer_value}")
                else:
                    print("Final Answer: Not Calculated")

                print("\n--- Interaction History ---")
                for i, entry in enumerate(iteration_history):
                    print(f"Turn {i+1}:\n  LLM > {entry['llm_response']}\n  SYS > {entry['tool_result']}")
                print("------------------------\n--- Interaction Loop Ended ---")

    except ConnectionRefusedError:
        print("Error: Connection refused. Is custom_server.py running?")
        traceback.print_exc()
    except Exception as e:
        print(f"Error during setup/main execution: {type(e).__name__}: {e}")
        traceback.print_exc()
    finally:
        print("Cleaning up...")
        print("Main execution finished.")


if __name__ == "__main__":
    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExecution interrupted.")
    except Exception as e:
        print(f"Top level error: {type(e).__name__}: {e}")
        traceback.print_exc()

# --- END OF FILE talk2mcp.py ---