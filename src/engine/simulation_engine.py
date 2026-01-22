"""
Simulation Engine Core.

This is the heart of the system, responsible for executing the simulation
based on the SystemModel. It supports different exploration strategies.
"""
import random
import networkx as nx
from typing import Dict, Any, List, Tuple
from src.core.models import SystemModel

class SimulationEngine:
    """
    Manages the state-space exploration and simulation of the system model.
    """
    def __init__(self, model: SystemModel):
        self.model = model
        self.graph = nx.DiGraph()
        self.initial_state = self._get_initial_state()

    def _get_initial_state(self) -> Tuple:
        """Constructs the initial state from the model."""
        # State is represented as a tuple of sorted values to be hashable
        state_dict = {s.name: s.initial_value for s in self.model.states}
        return self._dict_to_state_tuple(state_dict)

    def _dict_to_state_tuple(self, state_dict: Dict[str, Any]) -> Tuple:
        """Converts a state dictionary to a sorted tuple for hashing."""
        return tuple(sorted(state_dict.items()))

    def _state_tuple_to_dict(self, state_tuple: Tuple) -> Dict[str, Any]:
        """Converts a state tuple back to a dictionary."""
        return dict(state_tuple)

    def get_applicable_events(self, state_dict: Dict[str, Any]) -> List[str]:
        """
        Determines which events can be triggered from the current state.
        """
        applicable = []
        for event in self.model.events:
            if self._evaluate_condition(event.condition, state_dict):
                applicable.append(event.name)
        return applicable

    def _evaluate_condition(self, expression: str, context: Dict[str, Any]) -> bool:
        """
        Safely evaluates a Python expression within a given context.

        WARNING: This method uses eval(), which can execute arbitrary code.
        Only run scenarios from trusted sources.
        """
        try:
            return eval(expression, {}, context)
        except SyntaxError as e:
            print(f"Warning: Syntax error in condition '{expression}': {e}")
            return False
        except Exception as e:
            # Catch other potential runtime errors during evaluation
            # print(f"Warning: Error evaluating condition '{expression}': {e}")
            return False

    def apply_event(self, state_dict: Dict[str, Any], event_name: str) -> Dict[str, Any]:
        """
        Applies an event's effect to a state to produce a new state.

        WARNING: This method uses exec(), which can execute arbitrary code.
        Only run scenarios from trusted sources.
        """
        event = next((e for e in self.model.events if e.name == event_name), None)
        if not event:
            return state_dict

        new_state = state_dict.copy()
        try:
            # The exec function is used here to apply the state change.
            exec(event.effect, {}, new_state)
        except SyntaxError as e:
            print(f"Warning: Syntax error in effect for event '{event_name}': {e}")
        except Exception as e:
            print(f"Warning: Error applying effect for event '{event_name}': {e}")

        # Clean up internal variables created by exec
        if '__builtins__' in new_state:
            del new_state['__builtins__']
        return new_state

    def run_bfs_explorer(self):
        """
        Performs a full Breadth-First Search (BFS) of the state space.
        This is ideal for finding violations in the smallest number of steps.
        """
        queue = [(self.initial_state, [])]  # (state, path_of_events)
        visited = {self.initial_state}

        while queue:
            current_state_tuple, path = queue.pop(0)
            current_state_dict = self._state_tuple_to_dict(current_state_tuple)

            self.graph.add_node(current_state_tuple, **current_state_dict)

            applicable_events = self.get_applicable_events(current_state_dict)

            for event_name in applicable_events:
                next_state_dict = self.apply_event(current_state_dict, event_name)
                next_state_tuple = self._dict_to_state_tuple(next_state_dict)

                if next_state_tuple not in visited:
                    visited.add(next_state_tuple)
                    new_path = path + [event_name]
                    queue.append((next_state_tuple, new_path))
                    self.graph.add_edge(current_state_tuple, next_state_tuple, event=event_name)

        return self.graph

    def run_solver_explorer(self):
        """
        (Placeholder) Uses a constraint solver (Z3) to find paths to states
        that violate a specific goal.
        """
        raise NotImplementedError("Solver-based exploration is not yet implemented.")

    def run_monte_carlo_explorer(self, num_steps: int):
        """
        Performs a random walk through the state space using Monte Carlo simulation.
        This is useful for exploring large state spaces where BFS is not feasible.
        """
        current_state_tuple = self.initial_state

        for _ in range(num_steps):
            current_state_dict = self._state_tuple_to_dict(current_state_tuple)
            self.graph.add_node(current_state_tuple, **current_state_dict)

            applicable_events = self.get_applicable_events(current_state_dict)
            if not applicable_events:
                # Deadlock or terminal state
                break

            # Choose a random event to fire
            random_event_name = random.choice(applicable_events)

            next_state_dict = self.apply_event(current_state_dict, random_event_name)
            next_state_tuple = self._dict_to_state_tuple(next_state_dict)

            # Add the new state and the transition to the graph
            self.graph.add_node(next_state_tuple, **next_state_dict)
            self.graph.add_edge(current_state_tuple, next_state_tuple, event=random_event_name)

            current_state_tuple = next_state_tuple

        return self.graph
