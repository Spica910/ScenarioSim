"""
Simulation Engine Core.
"""
import random
import networkx as nx
from typing import Dict, Any, List, Tuple
from src.core.models import SystemModel
from src.utils import get_logger
import re

logger = get_logger(__name__)

class SimulationEngine:
    def __init__(self, model: SystemModel):
        self.model = model
        self.graph = nx.DiGraph()
        self.initial_state = self._get_initial_state()

    # ... [Helper methods _get_initial_state, _dict_to_state_tuple, _state_tuple_to_dict remain the same] ...
    def _get_initial_state(self) -> Tuple:
        state_dict = {s.name: s.initial_value for s in self.model.states}
        return self._dict_to_state_tuple(state_dict)

    def _dict_to_state_tuple(self, state_dict: Dict[str, Any]) -> Tuple:
        return tuple(sorted(state_dict.items()))

    def _state_tuple_to_dict(self, state_tuple: Tuple) -> Dict[str, Any]:
        return dict(state_tuple)


    def get_applicable_events(self, state_dict: Dict[str, Any]) -> List[str]:
        # ... [Unchanged] ...
        applicable = []
        for event in self.model.events:
            if self._evaluate_condition(event.condition, state_dict):
                applicable.append(event.name)
        return applicable

    def _evaluate_condition(self, expression: str, context: Dict[str, Any]) -> bool:
        # ... [Unchanged] ...
        try:
            return eval(expression, {}, context)
        except SyntaxError as e:
            logger.warning("Syntax error in condition '%s': %s", expression, e)
            return False
        except Exception:
            return False

    def apply_event(self, state_dict: Dict[str, Any], event_name: str) -> Dict[str, Any]:
        # ... [Unchanged] ...
        event = next((e for e in self.model.events if e.name == event_name), None)
        if not event: return state_dict
        new_state = state_dict.copy()
        try:
            exec(event.effect, {}, new_state)
        except SyntaxError as e:
            logger.warning("Syntax error in effect for event '%s': %s", event_name, e)
        except Exception as e:
            logger.warning("Error applying effect for event '%s': %s", event_name, e)
        if '__builtins__' in new_state: del new_state['__builtins__']
        return new_state

    def run_bfs_explorer(self):
        # ... [Unchanged] ...
        queue = [(self.initial_state, [])]; visited = {self.initial_state}
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
                    queue.append((next_state_tuple, path + [event_name]))
                    self.graph.add_edge(current_state_tuple, next_state_tuple, event=event_name)
        return self.graph

    def run_solver_explorer(self, goal_expression: str, max_steps: int):
        try:
            from z3 import Solver, Int, Bool, And, Not, Or, If, Implies, sat, AtMost, PbEq
        except ImportError:
            logger.error("Z3 solver is not installed. Please run 'pip install z3-solver'.")
            return "Z3 solver not found."

        s = Solver()

        # 1. Create variables
        states_over_time = [{v.name: (Int(f"{v.name}_{t}") if v.type == 'int' else Bool(f"{v.name}_{t}")) for v in self.model.states} for t in range(max_steps + 1)]
        events_over_time = [{e.name: Bool(f"{e.name}_fired_{t}") for e in self.model.events} for t in range(max_steps)]

        # 2. Initial state constraints
        s.add(And([states_over_time[0][v.name] == v.initial_value for v in self.model.states]))

        # 3. Transition logic
        for t in range(max_steps):
            # Constraint: At most one event fires at each step
            s.add(AtMost(*[events_over_time[t][e.name] for e in self.model.events], 1))

            for event in self.model.events:
                event_fired = events_over_time[t][event.name]

                # An event can only fire if its condition is met at time t
                try:
                    condition_z3 = eval(event.condition, {}, states_over_time[t])
                    s.add(Implies(event_fired, condition_z3))
                except Exception as e:
                    logger.warning(f"Could not parse event condition for Z3: {event.condition}. Error: {e}")
                    s.add(Not(event_fired)) # Prevent event from ever firing if condition is invalid

                # Define the effect of the event on the next state
                for var in self.model.states:
                    var_at_t = states_over_time[t][var.name]
                    var_at_t1 = states_over_time[t+1][var.name]

                    effect_on_var = var_at_t # Default: state doesn't change
                    if var.name in event.effect:
                        try:
                            # This is a simplified parser for "var = new_value" or "var += value"
                            # A full implementation would need a proper Python AST parser.
                            effect_expr = self._parse_simple_effect(event.effect, var.name, states_over_time[t])
                            effect_on_var = effect_expr if effect_expr is not None else var_at_t
                        except Exception as e:
                            logger.warning(f"Could not parse event effect for Z3: {event.effect}. Error: {e}")

                    s.add(Implies(event_fired, var_at_t1 == effect_on_var))

            # If no event fires, the state remains the same
            no_event_fired = Not(Or([events_over_time[t][e.name] for e in self.model.events]))
            for var in self.model.states:
                s.add(Implies(no_event_fired, states_over_time[t+1][var.name] == states_over_time[t][var.name]))

        # 4. Goal violation constraint
        # We are looking for a path where the goal is violated at least once.
        violation_at_any_step = []
        for t in range(max_steps + 1):
            try:
                goal_z3 = eval(goal_expression, {}, states_over_time[t])
                violation_at_any_step.append(Not(goal_z3))
            except Exception as e:
                logger.warning(f"Could not parse goal expression for Z3: {goal_expression}. Error: {e}")

        s.add(Or(violation_at_any_step))

        # 5. Check solver and parse result
        if s.check() == sat:
            model = s.model()
            path = []
            for t in range(max_steps):
                for event in self.model.events:
                    event_fired_var = events_over_time[t][event.name]
                    if model.evaluate(event_fired_var):
                        path.append(event.name)
                        break # Move to next step once event is found
            return path
        else:
            return f"No violation path found within {max_steps} steps."

    def _parse_simple_effect(self, effect_str: str, var_name: str, z3_vars: Dict):
        """A simplified parser for event effects to translate them to Z3."""
        # Handles "var = ..."
        match = re.search(f"{var_name}\\s*=\\s*(.*)", effect_str)
        if match:
            expr = match.group(1)
            return eval(expr, {}, z3_vars)

        # Handles "var += ..."
        match = re.search(f"{var_name}\\s*\\+=\\s*(.*)", effect_str)
        if match:
            expr = match.group(1)
            return z3_vars[var_name] + eval(expr, {}, z3_vars)

        # Handles "var -= ..."
        match = re.search(f"{var_name}\\s*\\-=\\s*(.*)", effect_str)
        if match:
            expr = match.group(1)
            return z3_vars[var_name] - eval(expr, {}, z3_vars)

        return None # Variable not affected by this effect string

    def run_monte_carlo_explorer(self, num_steps: int):
        # ... [Unchanged] ...
        current_state_tuple = self.initial_state
        for _ in range(num_steps):
            current_state_dict = self._state_tuple_to_dict(current_state_tuple)
            self.graph.add_node(current_state_tuple, **current_state_dict)
            applicable_events = self.get_applicable_events(current_state_dict)
            if not applicable_events: break
            random_event_name = random.choice(applicable_events)
            next_state_dict = self.apply_event(current_state_dict, random_event_name)
            next_state_tuple = self._dict_to_state_tuple(next_state_dict)
            self.graph.add_node(next_state_tuple, **next_state_dict)
            self.graph.add_edge(current_state_tuple, next_state_tuple, event=random_event_name)
            current_state_tuple = next_state_tuple
        return self.graph
