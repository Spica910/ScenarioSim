"""
JSON Parser for scenario files.
"""
import json
from src.core.models import SystemModel
from src.parsers.base_parser import BaseParser

class JSONParser(BaseParser):
    """
    Parses a JSON string to create a SystemModel instance.
    This provides the concrete implementation for reading the structured
    JSON format defined in the SDS.
    """
    def parse(self, json_string: str) -> SystemModel:
        """
        Parses a JSON string into a SystemModel.

        Args:
            json_string: The JSON data as a string.

        Returns:
            A SystemModel object.
        """
        data = json.loads(json_string)
        return SystemModel(**data)
