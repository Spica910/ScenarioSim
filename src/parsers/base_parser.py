"""
Abstract Base Class for all parsers.
"""
from abc import ABC, abstractmethod
from src.core.models import SystemModel

class BaseParser(ABC):
    """
    Abstract base class for parsers. All parsers should inherit from this class
    and implement the 'parse' method.
    """
    @abstractmethod
    def parse(self, input_data: str) -> SystemModel:
        """
        Parses the input data and returns a SystemModel object.

        Args:
            input_data: The raw data to parse (e.g., file content).

        Returns:
            A SystemModel object representing the parsed scenario.
        """
        pass
