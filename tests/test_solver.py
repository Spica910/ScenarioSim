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

    def test_finds_path_with_conditional_assignment(self):
        """
        Tests that the solver can handle a conditional (ternary) assignment in an event effect.
        """
        # --- Arrange ---
        model = SystemModel(
            name="Conditional Assignment Test",
            states=[
                StateVariable(name="x", type="int", initial_value=0),
                StateVariable(name="y", type="int", initial_value=0),
            ],
            events=[
                Event(name="increment_y", condition="True", effect="y += 1"),
                # This event uses a conditional assignment that the solver must parse
                Event(name="set_x_conditionally", condition="True", effect="x = 1 if y >= 10 else 0"),
            ],
            goals=[Goal(description="x should always be 0 or less", expression="x <= 0")]
        )

        engine = SimulationEngine(model)
        goal_to_violate = "x <= 0"
        max_steps = 11 # Needs 10 steps to increment y, then 1 step to set x

        # --- Act ---
        result = engine.run_solver_explorer(goal_to_violate, max_steps)

        # --- Assert ---
        # The solver should find a path where y is incremented 10 times,
        # and then set_x_conditionally is called to set x to 1.
        expected_path = ['increment_y'] * 10 + ['set_x_conditionally']
        self.assertIsInstance(result, list)
        self.assertEqual(result, expected_path)

    def test_solver_with_min_function(self):
        """
        Tests that the Z3 solver can correctly reason about an effect
        containing the min() function, as used in the example scenario.
        """
        # --- Arrange ---
        model = SystemModel(
            name="Min Function Test",
            states=[
                StateVariable(name="x", type="int", initial_value=95)
            ],
            events=[
                Event(name="charge", condition="True", effect="x = min(100, x + 10)"),
            ],
            # This goal can never be violated because of the min() in the event.
            goals=[Goal(description="x should never exceed 100", expression="x <= 100")]
        )
        engine = SimulationEngine(model)
        goal_to_violate = "x <= 100"
        max_steps = 2 # Should be enough to find a violation if one existed

        # --- Act ---
        result = engine.run_solver_explorer(goal_to_violate, max_steps)

        # --- Assert ---
        # The solver should correctly prove that the goal cannot be violated.
        self.assertIsInstance(result, str)
        self.assertIn("No violation path found", result)


if __name__ == '__main__':
    unittest.main()
