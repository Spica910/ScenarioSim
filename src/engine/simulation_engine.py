"""
Core simulation engine for running scenario explorations.
"""
import ast
import networkx as nx
import random
from z3 import Solver, Bool, Int, Real, And, Or, Not, sat, Implies, If

from src.core.models import SystemModel
from src.core.expressions import safe_eval, safe_exec

# --- AST to Z3 Converter ---
class PyToZ3Converter(ast.NodeVisitor):
    """
    Converts a Python AST expression into a Z3 symbolic expression.
    """
    def __init__(self, z3_state_vars):
        self.state = z3_state_vars

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add): return left + right
        if isinstance(node.op, ast.Sub): return left - right
        if isinstance(node.op, ast.Mult): return left * right
        if isinstance(node.op, ast.Div): return left / right
        raise NotImplementedError(f"Unsupported binary operator: {type(node.op)}")

    def visit_Compare(self, node):
        left = self.visit(node.left)
        right = self.visit(node.comparators[0]) # Assume single comparator
        op = node.ops[0]
        if isinstance(op, ast.Eq): return left == right
        if isinstance(op, ast.NotEq): return left != right
        if isinstance(op, ast.Lt): return left < right
        if isinstance(op, ast.LtE): return left <= right
        if isinstance(op, ast.Gt): return left > right
        if isinstance(op, ast.GtE): return left >= right
        raise NotImplementedError(f"Unsupported comparison operator: {type(op)}")

    def visit_IfExp(self, node):
        test = self.visit(node.test)
        body = self.visit(node.body)
        orelse = self.visit(node.orelse)
        return If(test, body, orelse)

    def visit_Call(self, node):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Unsupported function call type")

        func_name = node.func.id
        args = [self.visit(arg) for arg in node.args]

        if func_name == 'min':
            return If(args[0] < args[1], args[0], args[1])
        if func_name == 'max':
            return If(args[0] > args[1], args[0], args[1])
        raise ValueError(f"Unsupported function: {func_name}")

    def visit_Name(self, node):
        return self.state[node.id]

    def visit_Constant(self, node):
        return node.value

def _parse_z3_model_to_path(model, events, z3_event_vars, max_steps, goal_expr, state_vars, z3_state_vars):
    """Helper to reconstruct the event path from a satisfied Z3 model."""
    for k_check in range(1, max_steps + 1):
        # Build a dictionary of the state variables at step k_check from the model
        state_k_dict_model = {}
        for var in state_vars:
            z3_var = z3_state_vars.get(f"{var.name}_{k_check}")
            if z3_var is not None:
                model_val = model.eval(z3_var)
                # Convert Z3 literals to Python types
                if hasattr(model_val, 'as_long'):
                    state_k_dict_model[var.name] = model_val.as_long()
                elif hasattr(model_val, 'is_true'):
                    state_k_dict_model[var.name] = model_val.is_true()
                else:
                    state_k_dict_model[var.name] = model_val

        # Check if the goal expression is false in this state
        try:
            is_violated = not eval(goal_expr, {}, state_k_dict_model)
            if is_violated:
                # If violated, reconstruct the path of events up to this step
                path = []
                for k in range(k_check):
                    for event in events:
                        event_var = z3_event_vars.get(f"{event.name}_{k}")
                        if event_var is not None and model.eval(event_var):
                            path.append(event.name)
                            break # Found event for step k, move to next step
                return path
        except Exception:
            continue # Could fail if a variable is not in the state dict

    return "Violation found but failed to reconstruct path."

def _parse_effect_to_z3(effect_str: str, state_k: dict, state_k_plus_1: dict):
    """
    Parses an effect string (e.g., "x = x + 1; y = min(100, x)") into
    a Z3 constraint using the PyToZ3Converter.
    """
    assignments = []
    modified_vars = set()
    converter = PyToZ3Converter(state_k)

    # Parse the entire effect string as a module
    try:
        effect_tree = ast.parse(effect_str.strip(), mode='exec')
    except SyntaxError:
        return And(True) # Ignore invalid syntax

    for stmt in effect_tree.body:
        # Handle simple assignments: var = expr
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            var_name = stmt.targets[0].id
            z3_expr = converter.visit(stmt.value)
            assignments.append(state_k_plus_1[var_name] == z3_expr)
            modified_vars.add(var_name)
        # Handle augmented assignments: var += expr
        elif isinstance(stmt, ast.AugAssign) and isinstance(stmt.target, ast.Name):
            var_name = stmt.target.id
            z3_expr = converter.visit(stmt.value)
            op = stmt.op
            if isinstance(op, ast.Add):
                assignments.append(state_k_plus_1[var_name] == state_k[var_name] + z3_expr)
            elif isinstance(op, ast.Sub):
                assignments.append(state_k_plus_1[var_name] == state_k[var_name] - z3_expr)
            else:
                raise NotImplementedError(f"Unsupported augmented assignment op: {type(op)}")
            modified_vars.add(var_name)

    # Frame axiom: variables not modified by the effect remain unchanged
    for var_name in state_k:
        if var_name not in modified_vars:
            assignments.append(state_k_plus_1[var_name] == state_k[var_name])

    return And(assignments) if assignments else And(True)


class SimulationEngine:
    def __init__(self, model: SystemModel):
        self.model = model
        self.initial_state = tuple(sorted([(var.name, var.initial_value) for var in self.model.states]))

    def get_applicable_events(self, state_dict):
        """Returns a dict of event names that can be triggered in the given state."""
        applicable = {}
        for event in self.model.events:
            try:
                if safe_eval(event.condition, state_dict):
                    applicable[event.name] = event
            except Exception:
                continue # Event condition fails, is invalid, or unsafe
        return applicable

    def apply_event(self, state_dict, event_name):
        """Applies an event's effect to a state and returns the new state."""
        event = next((e for e in self.model.events if e.name == event_name), None)
        if not event: return state_dict

        new_state = state_dict.copy()
        try:
            safe_exec(event.effect, new_state)
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
        s = Solver()

        # Define state variables for each step k
        z3_state_vars = {}
        for k in range(max_steps + 1):
            for var in self.model.states:
                var_name = f"{var.name}_{k}"
                if var.type == 'bool': z3_state_vars[var_name] = Bool(var_name)
                elif var.type == 'int': z3_state_vars[var_name] = Int(var_name)
                elif var.type == 'float': z3_state_vars[var_name] = Real(var_name)

        # Define event trigger variables for each step k
        z3_event_vars = {f"{e.name}_{k}": Bool(f"{e.name}_{k}") for k in range(max_steps) for e in self.model.events}

        # Initial state constraint
        s.add(And([z3_state_vars[f"{v.name}_0"] == v.initial_value for v in self.model.states]))

        # Transition logic for each step
        for k in range(max_steps):
            state_k = {var.name: z3_state_vars[f"{var.name}_{k}"] for var in self.model.states}
            state_k_plus_1 = {var.name: z3_state_vars[f"{var.name}_{k+1}"] for var in self.model.states}

            # Constraint: exactly one event fires at each step
            active_events_k = [z3_event_vars[f"{e.name}_{k}"] for e in self.model.events]
            s.add(Or(active_events_k))
            for i in range(len(active_events_k)):
                for j in range(i + 1, len(active_events_k)):
                    s.add(Or(Not(active_events_k[i]), Not(active_events_k[j])))

            # Transition Relation: if an event fires, its pre-condition must hold and its effect is applied
            for event in self.model.events:
                event_fires = z3_event_vars[f"{event.name}_{k}"]
                try:
                    pre_cond = eval(event.condition, {}, state_k)
                except (NameError, TypeError): pre_cond = True

                effect_logic = _parse_effect_to_z3(event.effect, state_k, state_k_plus_1)
                s.add(Implies(event_fires, And(pre_cond, effect_logic)))

        # Goal Violation: assert that the goal is false at some step
        goal_violations = []
        for k in range(1, max_steps + 1):
            state_k = {var.name: z3_state_vars[f"{var.name}_{k}"] for var in self.model.states}
            try:
                goal_cond = eval(goal_expression, {}, state_k)
                goal_violations.append(Not(goal_cond))
            except (NameError, TypeError): continue
        s.add(Or(goal_violations))

        # Check for solution and reconstruct path
        if s.check() == sat:
            return _parse_z3_model_to_path(s.model(), self.model.events, z3_event_vars, max_steps, goal_expression, self.model.states, z3_state_vars)
        else:
            return f"No violation path found within {max_steps} steps."
