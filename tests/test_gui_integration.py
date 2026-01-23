"""
Integration tests for the GUI logic.
"""
import unittest
import os
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication, QTableWidgetItem
from src.ui.main_window import MainWindow
from src.core.models import SystemModel

class TestGuiIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        """Create a new MainWindow instance for each test."""
        self.window = MainWindow()
        # Load initial data for testing editor functions
        with patch('PySide6.QtWidgets.QFileDialog.getOpenFileName', return_value=("examples/airpods_charging.json", '')):
            self.window.open_file()

    def test_open_run_save_workflow(self):
        """Tests the full open -> run -> save workflow."""
        # Verification of open is in setUp
        self.assertEqual(self.window.current_model.name, "AirPods Charging Scenario")

        # Test run
        self.window.run_simulation()
        results_text = self.window.results_browser.toPlainText()
        self.assertIn("Simulation Complete", results_text)

        # Test save
        save_path = "test_output.json"
        with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName', return_value=(save_path, '')):
            self.window.save_file()
        self.assertTrue(os.path.exists(save_path))
        os.remove(save_path)

    def test_state_editing(self):
        """Tests adding, editing, and removing states via UI methods."""
        initial_state_count = len(self.window.current_model.states)

        # Test Add State
        self.window.add_state_row()
        self.assertEqual(len(self.window.current_model.states), initial_state_count + 1)
        self.assertEqual(self.window.table_states.rowCount(), initial_state_count + 1)
        self.assertEqual(self.window.current_model.states[-1].name, f"new_state_{initial_state_count}")

        # Test Edit State (programmatically trigger the signal)
        new_name = "test_battery"
        new_range = "(0, 100)"
        self.window.table_states.setItem(initial_state_count, 0, QTableWidgetItem(""))
        self.window.table_states.item(initial_state_count, 0).setText(new_name)

        self.window.table_states.setItem(initial_state_count, 3, QTableWidgetItem(""))
        self.window.table_states.item(initial_state_count, 3).setText(new_range)

        self.assertEqual(self.window.current_model.states[-1].name, new_name)
        self.assertEqual(self.window.current_model.states[-1].range, (0, 100))

        # Test Remove State
        self.window.table_states.setCurrentCell(initial_state_count, 0) # Select the new row
        self.window.remove_selected_state()
        self.assertEqual(len(self.window.current_model.states), initial_state_count)
        self.assertEqual(self.window.table_states.rowCount(), initial_state_count)

    def test_event_editing(self):
        """Tests adding, editing, and removing events via UI methods."""
        initial_event_count = len(self.window.current_model.events)

        # Test Add Event
        self.window.add_event()
        self.assertEqual(len(self.window.current_model.events), initial_event_count + 1)
        self.assertEqual(self.window.list_events.count(), initial_event_count + 1)

        # Test Edit Event (select and modify text)
        self.window.list_events.setCurrentRow(initial_event_count)
        new_condition = "case_battery > 50"
        self.window.edit_event_condition.setPlainText(new_condition)
        self.assertEqual(self.window.current_model.events[-1].condition, new_condition)

        # Test Remove Event
        self.window.remove_selected_event()
        self.assertEqual(len(self.window.current_model.events), initial_event_count)
        self.assertEqual(self.window.list_events.count(), initial_event_count)


if __name__ == '__main__':
    unittest.main()
