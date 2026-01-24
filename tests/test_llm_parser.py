"""
Unit tests for the LLM Parser function.
"""
import unittest
from unittest.mock import patch, MagicMock
import json

from src.parsers.llm_parser import parse_scenario_from_text
from src.parsers.json_parser import JSONParser
from src.core.models import SystemModel

class TestLLMParserFunction(unittest.TestCase):

    @patch('src.parsers.llm_parser.genai.GenerativeModel')
    @patch('src.parsers.llm_parser.genai.configure')
    def test_parse_successful_response(self, mock_configure, MockGenerativeModel):
        """
        Tests that the llm_parser function correctly parses a valid, mocked LLM response.
        """
        # --- Arrange ---
        # Mock the Gemini API response
        mock_api_response = MagicMock()
        mock_api_response.text = """
        {
          "name": "LLM Test Scenario",
          "states": [
            {"name": "battery", "type": "int", "initial_value": 50}
          ],
          "events": [],
          "constraints": [],
          "goals": []
        }
        """
        mock_model_instance = MockGenerativeModel.return_value
        mock_model_instance.generate_content.return_value = mock_api_response

        natural_language_input = "A simple scenario with one battery state."
        api_key = "fake_api_key"

        # --- Act ---
        json_output = parse_scenario_from_text(api_key, natural_language_input)
        system_model = JSONParser().parse(json_output) # Use JSONParser to get SystemModel

        # --- Assert ---
        mock_configure.assert_called_once_with(api_key=api_key)
        mock_model_instance.generate_content.assert_called_once()
        call_args = mock_model_instance.generate_content.call_args
        prompt = call_args.args[0]
        self.assertIn(natural_language_input, prompt)

        self.assertIsInstance(system_model, SystemModel)
        self.assertEqual(system_model.name, "LLM Test Scenario")
        self.assertEqual(len(system_model.states), 1)
        self.assertEqual(system_model.states[0].name, "battery")

    @patch('src.parsers.llm_parser.genai.GenerativeModel')
    @patch('src.parsers.llm_parser.genai.configure')
    def test_parse_api_error(self, mock_configure, MockGenerativeModel):
        """
        Tests that the parser handles an API error gracefully.
        """
        # --- Arrange ---
        mock_model_instance = MockGenerativeModel.return_value
        mock_model_instance.generate_content.side_effect = Exception("API Failure")

        # --- Act ---
        json_output = parse_scenario_from_text("fake_api_key", "Some input")
        result = json.loads(json_output)

        # --- Assert ---
        self.assertIn("error", result)
        self.assertIn("API Failure", result["error"])

    def test_no_api_key(self):
        """
        Tests that the function returns an error if no API key is provided.
        """
        # --- Act ---
        json_output = parse_scenario_from_text("", "Some input")
        result = json.loads(json_output)

        # --- Assert ---
        self.assertIn("error", result)
        self.assertIn("API key is not set", result["error"])

if __name__ == '__main__':
    unittest.main()
