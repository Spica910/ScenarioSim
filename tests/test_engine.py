"""
Unit tests for the Simulation Engine.
"""
import unittest
from src.core.models import SystemModel, StateVariable, Event
from src.engine.simulation_engine import SimulationEngine

class TestSimulationEngine(unittest.TestCase):

    def setUp(self):
        """Set up a simple model for testing."""
        self.model = SystemModel(
            name="Test Engine Model",
            states=[
                StateVariable(name="x", type="int", initial_value=0),
                StateVariable(name="y", type="bool", initial_value=False)
            ],
            events=[
                Event(name="increment_x", condition="x < 5", effect="x += 1"),
                Event(name="toggle_y", condition="True", effect="y = not y")
            ]
        )
        self.engine = SimulationEngine(self.model)

    def test_initial_state(self):
        """Tests that the initial state is correctly set up."""
        expected_initial_state = (('x', 0), ('y', False))
        self.assertEqual(self.engine.initial_state, expected_initial_state)

    def test_applicable_events(self):
        """Tests the logic for finding applicable events."""
        state_dict = {'x': 0, 'y': False}
        applicable = self.engine.get_applicable_events(state_dict)
        self.assertIn("increment_x", applicable)
        self.assertIn("toggle_y", applicable)

        state_dict_x_max = {'x': 5, 'y': False}
        applicable = self.engine.get_applicable_events(state_dict_x_max)
        self.assertNotIn("increment_x", applicable)
        self.assertIn("toggle_y", applicable)

    def test_apply_event(self):
        """Tests that an event correctly modifies the state."""
        state_dict = {'x': 0, 'y': False}
        new_state = self.engine.apply_event(state_dict, "increment_x")
        self.assertEqual(new_state['x'], 1)
        self.assertEqual(new_state['y'], False)

    def test_bfs_explorer(self):
        """
        Tests the BFS explorer to ensure it explores the state space correctly.
        For the simple model, we expect 12 states (6 for x * 2 for y).
        """
        graph = self.engine.run_bfs_explorer()
        # States are x from 0 to 5 (6 values), y is bool (2 values) -> 6 * 2 = 12
        self.assertEqual(graph.number_of_nodes(), 12)
        # Check a specific transition
        start_state = (('x', 0), ('y', False))
        next_state = (('x', 1), ('y', False))
        self.assertTrue(graph.has_edge(start_state, next_state))

    def test_monte_carlo_explorer(self):
        """
        Tests the Monte Carlo explorer to ensure it runs and explores states.
        """
        # We expect the graph to have at least one node (initial state)
        # and at most num_steps+1 nodes.
        num_steps = 10
        graph = self.engine.run_monte_carlo_explorer(num_steps)
        self.assertGreater(graph.number_of_nodes(), 0)
        self.assertLessEqual(graph.number_of_nodes(), num_steps + 1)


if __name__ == '__main__':
    unittest.main()
