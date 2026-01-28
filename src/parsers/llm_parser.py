"""
Parses a natural language scenario description into a structured JSON model
using the Google Gemini LLM.
"""
import google.generativeai as genai
import json

def parse_scenario_from_text(api_key: str, text: str) -> str:
    """
    Uses the Gemini 1.5 Flash model to parse natural language text into the
    scenario JSON format.

    Args:
        api_key: The Google API key for authentication.
        text: The natural language text describing the scenario.

    Returns:
        A string containing the structured scenario in JSON format, or an
        error message string if parsing fails.
    """
    if not api_key:
        return '{"error": "API key is not set. Please configure it in Settings."}'

    genai.configure(api_key=api_key)

    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    You are an expert system designer specializing in converting natural language
    descriptions of state machines into a precise JSON format. Your task is to
    parse the user's text and convert it into a valid JSON object that strictly
    follows the provided schema.

    **JSON Schema:**
    {{
      "name": "Scenario Name",
      "states": [
        {{"name": "variable_name", "type": "int|float|bool", "initial_value": value}}
      ],
      "events": [
        {{"name": "event_name", "condition": "Python expression", "effect": "Python expression"}}
      ],
      "constraints": [
        {{"description": "A rule that must never be violated", "expression": "Python boolean expression"}}
      ],
      "goals": [
        {{"description": "A condition to verify", "expression": "Python boolean expression"}}
      ]
    }}

    **Instructions:**
    1.  **Strictly adhere to the JSON schema.** Do not add any extra fields.
    2.  **`type`** must be one of: `int`, `float`, or `bool`.
    3.  **`initial_value`** must match the specified `type`.
    4.  **`condition`** and **`effect`** in events must be valid Python expressions.
        - `effect` should be an assignment (e.g., `var = val` or `var += 1`).
        - `condition` should evaluate to a boolean (e.g., `var > 0`). Use `True` if an event can always happen.
    5.  **`expression`** in constraints and goals must be a valid Python boolean expression.
    6.  Enclose all JSON keys and string values in double quotes.
    7.  If the user's text is ambiguous or incomplete, make reasonable assumptions based on typical state machine logic.
    8.  Your entire output must be **only the JSON object**, with no surrounding text, markdown, or explanations.

    **User's Scenario Description:**
    ---
    {text}
    ---

    **Your JSON Output:**
    """

    try:
        response = model.generate_content(prompt)

        # Clean up the response to get only the JSON part
        raw_json = response.text.strip()
        if raw_json.startswith("```json"):
            raw_json = raw_json[7:]
        if raw_json.endswith("```"):
            raw_json = raw_json[:-3]

        # Validate that the result is valid JSON
        json.loads(raw_json)

        return raw_json

    except Exception as e:
        return f'{{"error": "Failed to parse scenario with LLM: {str(e)}"}}'

if __name__ == '__main__':
    # Example usage for testing
    # Make sure to set your GOOGLE_API_KEY as an environment variable
    import os
    test_api_key = os.environ.get("GOOGLE_API_KEY")

    test_scenario = """
    Name: AirPods Charging Test

    States:
    - case_battery: an integer, starts at 50
    - buds_in_case: a boolean, initially true
    - cable_connected: boolean, starts false

    Events:
    - connect_cable: can always happen, sets cable_connected to true.
    - disconnect_cable: always possible, sets cable_connected to false.
    - charge_tick: if cable is connected, case battery increases by 10 but not over 100.

    Goals:
    - The case battery should never exceed 100.

    Constraints:
    - The case battery must never be negative.
    """

    if test_api_key:
        parsed_json = parse_scenario_from_text(test_api_key, test_scenario)
        print(parsed_json)
    else:
        print("Please set the GOOGLE_API_KEY environment variable to run the test.")

    """
    Expected output structure:
    {
      "name": "AirPods Charging Test",
      "states": [
        {"name": "case_battery", "type": "int", "initial_value": 50},
        {"name": "buds_in_case", "type": "bool", "initial_value": true},
        {"name": "cable_connected", "type": "bool", "initial_value": false}
      ],
      "events": [
        {"name": "connect_cable", "condition": "True", "effect": "cable_connected = True"},
        {"name": "disconnect_cable", "condition": "True", "effect": "cable_connected = False"},
        {"name": "charge_tick", "condition": "cable_connected", "effect": "case_battery = min(100, case_battery + 10)"}
      ],
      "constraints": [
        {"description": "The case battery must never be negative.", "expression": "case_battery >= 0"}
      ],
      "goals": [
        {"description": "The case battery should never exceed 100.", "expression": "case_battery <= 100"}
      ]
    }
    """
