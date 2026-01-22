"""
Analysis Module.

This module is responsible for analyzing the results of a simulation run
(e.g., the state graph) to find violations, deadlocks, and other issues.
"""
import networkx as nx
from typing import List, Dict, Any, Tuple
from src.core.models import SystemModel

class Analyzer:
    """
    Analyzes a simulation graph to find violations of goals and constraints.
    """
    def __init__(self, model: SystemModel, graph: nx.DiGraph):
        self.model = model
        self.graph = graph

    def _evaluate_expression(self, expression: str, context: Dict[str, Any]) -> bool:
        """
        Safely evaluates a Python expression.

        WARNING: This method uses eval(), which can execute arbitrary code.
        Only run scenarios from trusted sources.
        """
        try:
            return eval(expression, {}, context)
        except SyntaxError as e:
            print(f"Warning: Syntax error in expression '{expression}': {e}")
            return False
        except Exception as e:
            # print(f"Warning: Error evaluating expression '{expression}': {e}")
            return False

    def find_constraint_violations(self) -> List[Tuple]:
        """
        Finds all states where constraints are violated.
        """
        violations = []
        for node in self.graph.nodes(data=True):
            state_dict = node[1]
            for constraint in self.model.constraints:
                if not self._evaluate_expression(constraint.expression, state_dict):
                    path = self.get_path_to_state(tuple(sorted(state_dict.items())))
                    violations.append({
                        "state": state_dict,
                        "constraint": constraint.description,
                        "path": path
                    })
        return violations

    def find_goal_violations(self) -> List[Tuple]:
        """
        Finds all states where goals are violated.
        """
        violations = []
        for node in self.graph.nodes(data=True):
            state_dict = node[1]
            for goal in self.model.goals:
                if not self._evaluate_expression(goal.expression, state_dict):
                    path = self.get_path_to_state(tuple(sorted(state_dict.items())))
                    violations.append({
                        "state": state_dict,
                        "goal": goal.description,
                        "path": path
                    })
        return violations

    def find_deadlocks(self) -> List[Dict[str, Any]]:
        """Finds states with no outgoing transitions (deadlocks)."""
        deadlocks = []
        for node in self.graph.nodes:
            if self.graph.out_degree(node) == 0:
                state_dict = dict(node)
                # Check if it's a terminal state that's not a violation
                is_violation = False
                for v in self.find_constraint_violations() + self.find_goal_violations():
                    if tuple(sorted(v['state'].items())) == node:
                        is_violation = True
                        break
                if not is_violation:
                    path = self.get_path_to_state(node)
                    deadlocks.append({
                        "state": state_dict,
                        "path": path,
                    })
        return deadlocks

    def get_path_to_state(self, target_state_tuple: Tuple) -> List[str]:
        """
        Finds the shortest path of events from the initial state to a target state.
        """
        try:
            initial_state = tuple(sorted({s.name: s.initial_value for s in self.model.states}.items()))
            path_nodes = nx.shortest_path(self.graph, source=initial_state, target=target_state_tuple)

            path_events = []
            for i in range(len(path_nodes) - 1):
                edge_data = self.graph.get_edge_data(path_nodes[i], path_nodes[i+1])
                path_events.append(edge_data['event'])
            return path_events
        except nx.NetworkXNoPath:
            return []
