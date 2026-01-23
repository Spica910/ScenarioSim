"""
Unit tests for the Z3 Solver integration in the Simulation Engine.
"""
import unittest
from src.core.models import SystemModel, StateVariable, Event, Goal
from src.engine.simulation_engine import SimulationEngine

class TestSolverIntegration(unittest.TestCase):

    def test_finds_simple_path(self):
        """
        Tests that the solver can find a simple, guaranteed violation path.
        """
        # --- Arrange ---
        # A simple model where 'x' must be incremented twice to violate the goal.
        simple_model = SystemModel(
            name="Simple Solver Test",
            states=[
                StateVariable(name="x", type="int", initial_value=0)
            ],
            events=[
                Event(name="increment", condition="x < 5", effect="x += 1")
            ],
            goals=[
                Goal(description="x should be less than 2", expression="x < 2")
            ]
        )

        engine = SimulationEngine(simple_model)
        goal_to_violate = "x < 2"
        max_steps = 3

        # --- Act ---
        result = engine.run_solver_explorer(goal_to_violate, max_steps)

        # --- Assert ---
        # The solver should find that firing 'increment' twice violates the goal.
        expected_path = ['increment', 'increment']
        self.assertIsInstance(result, list)
        self.assertEqual(result, expected_path)

    def test_no_path_found(self):
        """
        Tests that the solver correctly reports when no path is found.
        """
        # --- Arrange ---
        # A model where the goal can never be violated.
        model = SystemModel(
            name="No Violation Test",
            states=[StateVariable(name="x", type="int", initial_value=0)],
            events=[Event(name="increment", condition="x < 5", effect="x += 1")],
            goals=[Goal(description="x should be less than 10", expression="x < 10")]
        )

        engine = SimulationEngine(model)
        goal_to_violate = "x < 10"
        max_steps = 5

        # --- Act ---
        result = engine.run_solver_explorer(goal_to_violate, max_steps)

        # --- Assert ---
        self.assertIsInstance(result, str)
        self.assertIn("No violation path found", result)


if __name__ == '__main__':
    unittest.main()
