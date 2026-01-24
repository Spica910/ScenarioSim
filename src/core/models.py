"""
Core data models for the simulation system.

Based on the System Design Specification (SDS), these models represent
the structured representation (AST) of a scenario.
Pydantic is used for data validation and clear schema definition.
"""
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field

class StateVariable(BaseModel):
    """Defines a single state variable in the system."""
    name: str
    type: str  # 'int', 'bool', 'float', 'enum'
    initial_value: Any
    range: Tuple[float, float] = None  # For numeric types
    enum_values: List[str] = None      # For enum type

class Event(BaseModel):
    """Defines an event that can change the system's state."""
    name: str
    condition: str = "True"  # A Python expression to determine if the event can trigger
    effect: str              # A Python expression describing the state change

class Constraint(BaseModel):
    """Defines a constraint that must always be true."""
    description: str
    expression: str  # A Python expression that must evaluate to True

class Goal(BaseModel):
    """Defines a goal or property to be verified."""
    description: str
    expression: str  # A Python expression that must be met

class SystemModel(BaseModel):
    """
    The root model representing the entire system scenario.
    This is the structured output from the parser.
    """
    name: str
    states: List[StateVariable] = Field(default_factory=list)
    events: List[Event] = Field(default_factory=list)
    constraints: List[Constraint] = Field(default_factory=list)
    goals: List[Goal] = Field(default_factory=list)

    # Concurrency rules
    simultaneous_events: List[Tuple[str, str]] = Field(default_factory=list)
    mutually_exclusive_events: List[Tuple[str, str]] = Field(default_factory=list)
