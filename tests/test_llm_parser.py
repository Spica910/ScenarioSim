"""
Unit tests for the LLM Parser.
"""
import unittest
from unittest.mock import patch, MagicMock
from src.parsers.llm_parser import LLMParser
from src.core.models import SystemModel

class TestLLMParser(unittest.TestCase):

    @patch('google.generativeai.GenerativeModel')
    def test_parse_successful_response(self, MockGenerativeModel):
        """
        Tests that the LLM parser correctly parses a valid, mocked LLM response.
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

        # Set up the mock model to return our mock response
        mock_model_instance = MockGenerativeModel.return_value
        mock_model_instance.generate_content.return_value = mock_api_response

        parser = LLMParser()
        natural_language_input = "A simple scenario with one battery state."

        # --- Act ---
        system_model = parser.parse(natural_language_input)

        # --- Assert ---
        # Check that the model was called with a prompt containing our input
        mock_model_instance.generate_content.assert_called_once()
        call_args = mock_model_instance.generate_content.call_args
        prompt = call_args[0][0]
        self.assertIn(natural_language_input, prompt)

        # Check that the parsed model is correct
        self.assertIsInstance(system_model, SystemModel)
        self.assertEqual(system_model.name, "LLM Test Scenario")
        self.assertEqual(len(system_model.states), 1)
        self.assertEqual(system_model.states[0].name, "battery")

    @patch('google.generativeai.GenerativeModel')
    def test_parse_api_error(self, MockGenerativeModel):
        """
        Tests that the parser handles an API error gracefully.
        """
        # --- Arrange ---
        # Configure the mock to raise an exception
        mock_model_instance = MockGenerativeModel.return_value
        mock_model_instance.generate_content.side_effect = Exception("API Failure")

        parser = LLMParser()

        # --- Act ---
        system_model = parser.parse("Some input")

        # --- Assert ---
        # The parser should catch the exception and return a default, empty model
        self.assertEqual(system_model.name, "Failed LLM Parsing")
        self.assertEqual(len(system_model.states), 0)

if __name__ == '__main__':
    unittest.main()
