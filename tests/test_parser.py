"""
Unit tests for the JSON parser.
"""
import unittest
import json
from src.parsers.json_parser import JSONParser
from src.core.models import SystemModel

class TestJSONParser(unittest.TestCase):

    def test_parse_valid_json(self):
        """
        Tests that a valid JSON input is correctly parsed into a SystemModel.
        """
        json_string = """
        {
          "name": "Test Scenario",
          "states": [
            {"name": "var1", "type": "int", "initial_value": 10}
          ],
          "events": [
            {"name": "event1", "effect": "var1 = 20"}
          ]
        }
        """
        parser = JSONParser()
        model = parser.parse(json_string)

        self.assertIsInstance(model, SystemModel)
        self.assertEqual(model.name, "Test Scenario")
        self.assertEqual(len(model.states), 1)
        self.assertEqual(model.states[0].name, "var1")
        self.assertEqual(model.events[0].name, "event1")

    def test_parse_invalid_json(self):
        """
        Tests that the parser raises an error for malformed JSON.
        """
        json_string = "{"
        parser = JSONParser()
        with self.assertRaises(json.JSONDecodeError):
            parser.parse(json_string)

if __name__ == '__main__':
    unittest.main()
