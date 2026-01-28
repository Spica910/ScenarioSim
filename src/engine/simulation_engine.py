"""
Core simulation engine for running scenario explorations.
"""
import networkx as nx
import random
import re
from z3 import Solver, Bool, Int, Real, And, Or, Not, sat, Implies, If

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
        """
        Uses the Z3 SMT solver to find a path to a goal violation using Bounded Model Checking.
        This version has been refactored for correctness.
        """
        solver = Solver()

        # --- Variable Definitions ---
        states_t = []
        for t in range(max_steps + 1):
            step_vars = {}
            for var in self.model.states:
                if var.type == 'int':
                    step_vars[var.name] = Int(f"{var.name}_{t}")
                elif var.type == 'bool':
                    step_vars[var.name] = Bool(f"{var.name}_{t}")
                # Extend with float (Real) and other types as necessary
            states_t.append(step_vars)

        event_choices_t = [
            {event.name: Bool(f"{event.name}_{t}") for event in self.model.events}
            for t in range(max_steps)
        ]

        # --- Initial State Constraint ---
        for var in self.model.states:
            solver.add(states_t[0][var.name] == var.initial_value)

        # --- Transition and Frame Axiom Constraints ---
        for t in range(max_steps):
            current_vars = states_t[t]
            next_vars = states_t[t+1]
            events_this_step = event_choices_t[t]

            possible_events_this_step = []
            for event in self.model.events:
                event_var = events_this_step[event.name]
                possible_events_this_step.append(event_var)

                # 1. An event can only be chosen if its condition is true
                try:
                    condition_holds = eval(event.condition, {"__builtins__": {}}, current_vars)
                    solver.add(Implies(event_var, condition_holds))
                except Exception:
                    solver.add(Not(event_var))

                # 2. If an event is chosen, its effect is applied (and non-affected vars are unchanged)
                try:
                    touched_vars = re.findall(r"(\w+)\s*(\+)?=", event.effect)
                    touched_vars = [match[0] for match in touched_vars] # Extract the variable name

                    for var in self.model.states:
                        var_name = var.name
                        if var.name in touched_vars:
                            # If this event modifies the variable, calculate the next state's value
                            # This uses a trick where we pass Z3's If to eval to handle conditionals
                            eval_context = {**current_vars, "If": If, "min": lambda a, b: If(a < b, a, b), "max": lambda a, b: If(a > b, a, b)}

                            next_val_expr_str = event.effect.split('=', 1)[1].strip()

                            # Handle incremental assignment `x += 1` by converting to `x = x + 1`
                            if '+=' in event.effect:
                                var_in_effect, rhs = [p.strip() for p in event.effect.split('+=', 1)]
                                if var_in_effect == var_name:
                                    next_val_expr_str = f"{var_name} + {rhs}"

                            # Rewrite Python ternary `A if C else B` to Z3 `If(C, A, B)`
                            ternary_match = re.match(r"(.+)\s+if\s+(.+)\s+else\s+(.+)", next_val_expr_str)
                            if ternary_match:
                                true_val, cond, false_val = ternary_match.groups()
                                z3_expr_str = f"If({cond}, {true_val}, {false_val})"
                                next_val = eval(z3_expr_str, {}, eval_context)
                            else: # Handle direct assignment and functions like min/max
                                next_val = eval(next_val_expr_str, {}, eval_context)

                            solver.add(Implies(event_var, next_vars[var_name] == next_val))
                        else:
                            # FRAME AXIOM: If this event is chosen, this variable is unchanged
                            solver.add(Implies(event_var, next_vars[var_name] == current_vars[var_name]))
                except Exception as e:
                    solver.add(Not(event_var)) # If effect is unparsable, this event cannot be chosen
                    print(f"Warning: Could not create solver constraint for event '{event.name}' effect: {e}")

            # 3. Exactly one event is chosen per time step
            solver.add(Or(possible_events_this_step))
            for i in range(len(possible_events_this_step)):
                for j in range(i + 1, len(possible_events_this_step)):
                    solver.add(Or(Not(possible_events_this_step[i]), Not(possible_events_this_step[j])))

        # --- Goal Violation Constraint ---
        goal_is_violated = Or([Not(eval(goal_expression, {}, states_t[t])) for t in range(max_steps + 1)])
        solver.add(goal_is_violated)

        # --- Solve and Reconstruct Path ---
        if solver.check() == sat:
            model = solver.model()
            path = []

            violation_step = next((t for t in range(max_steps + 1) if model.evaluate(Not(eval(goal_expression, {}, states_t[t])))), -1)

            if violation_step == -1: return "Error: Solver found a model but couldn't identify the violation step."

            for t in range(violation_step):
                path.append(next(name for name, var in event_choices_t[t].items() if model.evaluate(var)))
            return path
        else:
            return f"No violation path found within {max_steps} steps."
