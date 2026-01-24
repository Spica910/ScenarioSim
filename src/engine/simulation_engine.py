"""
Core simulation engine for running scenario explorations.
"""
import networkx as nx
import random
from z3 import Solver, Bool, Int, Real, And, Or, Not, sat, Implies

from src.core.models import SystemModel

class SimulationEngine:
    def __init__(self, model: SystemModel):
        self.model = model
        self.initial_state = tuple(sorted([(var.name, var.initial_value) for var in self.model.states]))

    def get_applicable_events(self, state_dict):
        """Returns a dict of event names that can be triggered in the given state."""
        applicable = {}
        for event in self.model.events:
            try:
                # Use a restricted globals dict for safety, but allow min/max
                if eval(event.condition, {"__builtins__": {"min": min, "max": max}}, state_dict):
                    applicable[event.name] = event
            except Exception:
                continue # Event condition fails or is invalid
        return applicable

    def apply_event(self, state_dict, event_name):
        """Applies an event's effect to a state and returns the new state."""
        event = next((e for e in self.model.events if e.name == event_name), None)
        if not event: return state_dict

        new_state = state_dict.copy()
        try:
            # Use a restricted globals dict for safety, but allow min/max
            exec(event.effect, {"__builtins__": {"min": min, "max": max}}, new_state)
            # Remove special exec variables from the state
            if '__builtins__' in new_state: del new_state['__builtins__']
        except Exception:
            return state_dict # Revert state if effect fails
        return new_state

    def run_bfs_explorer(self):
        """Explores the state space using Breadth-First Search."""
        graph = nx.DiGraph()
        queue = [self.initial_state]
        visited = {self.initial_state}
        graph.add_node(self.initial_state)

        while queue:
            current_state_tuple = queue.pop(0)
            current_state_dict = dict(current_state_tuple)

            for event_name in self.get_applicable_events(current_state_dict):
                next_state_dict = self.apply_event(current_state_dict, event_name)
                next_state_tuple = tuple(sorted(next_state_dict.items()))

                if next_state_tuple not in visited:
                    visited.add(next_state_tuple)
                    queue.append(next_state_tuple)
                    graph.add_node(next_state_tuple)

                graph.add_edge(current_state_tuple, next_state_tuple, event=event_name)

        return graph

    def run_monte_carlo_explorer(self, num_steps):
        """Explores the state space using random event selection."""
        graph = nx.DiGraph()
        graph.add_node(self.initial_state)
        current_state_tuple = self.initial_state

        for _ in range(num_steps):
            applicable_events = list(self.get_applicable_events(dict(current_state_tuple)))
            if not applicable_events: break # Deadlock

            event_to_fire = random.choice(applicable_events)
            next_state_dict = self.apply_event(dict(current_state_tuple), event_to_fire)
            next_state_tuple = tuple(sorted(next_state_dict.items()))

            if next_state_tuple not in graph: graph.add_node(next_state_tuple)
            graph.add_edge(current_state_tuple, next_state_tuple, event=event_to_fire)
            current_state_tuple = next_state_tuple

        return graph

    def run_solver_explorer(self, goal_expression, max_steps):
        """Uses the Z3 SMT solver to find a path to a goal violation."""
        # This is a simplified placeholder as the AST implementation was reverted.
        return f"Solver feature is complex and was reverted for this diagnosis."
