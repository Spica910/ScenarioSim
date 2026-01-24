"""
Parser that uses a Large Language Model (LLM) to convert natural language
into a structured SystemModel.
"""
import os
import google.generativeai as genai
from src.core.models import SystemModel
from src.parsers.base_parser import BaseParser
from src.parsers.json_parser import JSONParser

# It's recommended to set the API key in your environment variables
# For example: export GOOGLE_API_KEY="your_api_key"
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

class LLMParser(BaseParser):
    """
    Parses a natural language description of a scenario into a SystemModel
    by querying the Gemini LLM.
    """
    def __init__(self, model_name="gemini-1.5-flash"):
        self.model = genai.GenerativeModel(model_name)
        self.json_parser = JSONParser()

    def parse(self, natural_language_input: str) -> SystemModel:
        """
        Converts natural language input to a SystemModel using an LLM.

        Args:
            natural_language_input: The user's description of the scenario.

        Returns:
            A SystemModel object.
        """
        prompt = self._build_prompt(natural_language_input)

        try:
            # Call the Gemini API
            response = self.model.generate_content(prompt)

            # The model should return a JSON string, which we can then parse.
            # Basic cleanup to remove markdown code fences if they exist.
            json_response = response.text.strip().replace("```json", "").replace("```", "").strip()

            # Use the existing JSONParser to validate and create the SystemModel
            return self.json_parser.parse(json_response)

        except Exception as e:
            print(f"Error calling Gemini API or parsing its response: {e}")
            # Return an empty model as a fallback
            return SystemModel(name="Failed LLM Parsing")

    def _build_prompt(self, scenario_text: str) -> str:
        """
        Creates the full prompt to send to the LLM.
        """
        # This prompt is crucial. It guides the LLM to produce the correct JSON format.
        prompt = f"""
You are an expert system designer. Your task is to convert a natural language
description of a device's behavior into a structured JSON model. The JSON
should conform to the schema defined by these Pydantic models:

```python
class StateVariable(BaseModel):
    name: str
    type: str  # 'int', 'bool', 'float', 'enum'
    initial_value: Any
    range: Tuple[float, float] = None
    enum_values: List[str] = None

class Event(BaseModel):
    name: str
    condition: str = "True"
    effect: str

class Constraint(BaseModel):
    description: str
    expression: str

class Goal(BaseModel):
    description: str
    expression: str

class SystemModel(BaseModel):
    name: str
    states: List[StateVariable]
    events: List[Event]
    constraints: List[Constraint]
    goals: List[Goal]
```

Based on the schema above, convert the following scenario description into a
single JSON object of type SystemModel. Ensure all expressions in 'condition',
'effect', 'expression' are valid Python code.

Scenario Description:
---
{scenario_text}
---

JSON Output:
"""
        return prompt
