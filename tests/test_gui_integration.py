"""
Integration tests for the GUI logic.
"""
import unittest
import os
from unittest.mock import patch
from PySide6.QtWidgets import QApplication, QTableWidgetItem

# This import will be problematic in the test env, but is needed for the test
# See AGENTS.md for more details on the pathing issue.
from src.ui.main_window import MainWindow
from src.core.models import SystemModel

class TestGuiIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        """Create a new MainWindow instance for each test."""
        self.window = MainWindow()

    @patch('PySide6.QtWidgets.QMessageBox.exec', return_value=True) # Auto-accept security warnings
    @patch('PySide6.QtWidgets.QFileDialog.getOpenFileName')
    def test_open_file_loads_data(self, mock_get_open_file_name, mock_msg_box):
        """Tests that opening a file correctly loads the model into the UI."""
        # Arrange
        mock_get_open_file_name.return_value = ("examples/airpods_charging.json", "JSON Files (*.json)")

        # Act
        self.window.open_file()

        # Assert
        self.assertEqual(self.window.current_model.name, "AirPods Charging Scenario")
        self.assertGreater(self.window.table_states.rowCount(), 0)
        self.assertEqual(self.window.table_states.item(0, 0).text(), "case_battery")

    @patch('PySide6.QtWidgets.QMessageBox.information')
    @patch('PySide6.QtWidgets.QFileDialog.getSaveFileName')
    def test_save_file_workflow(self, mock_get_save_file_name, mock_msg_box):
        """Tests the file saving functionality."""
        # Arrange
        save_path = "test_output.json"
        mock_get_save_file_name.return_value = (save_path, "JSON Files (*.json)")
        self.window.load_model_to_ui(SystemModel(name="Save Test"))

        # Act
        self.window.save_file()

        # Assert
        self.assertTrue(os.path.exists(save_path))
        mock_msg_box.assert_called_with(self.window, "Success", "File saved successfully.")

        # Clean up
        os.remove(save_path)

    def test_state_editing_ui(self):
        """Tests adding, editing, and removing states via UI methods."""
        # Arrange
        self.window.load_model_to_ui(SystemModel(name="State Edit Test"))
        initial_count = self.window.table_states.rowCount()

        # Act (Add)
        self.window.add_state_row()

        # Assert (Add)
        self.assertEqual(self.window.table_states.rowCount(), initial_count + 1)

        # Act (Edit)
        self.window.table_states.setItem(initial_count, 0, QTableWidgetItem("new_name"))
        self.window.update_state_in_model(initial_count, 0)

        # Assert (Edit)
        self.assertEqual(self.window.current_model.states[initial_count].name, "new_name")

        # Act (Remove)
        self.window.table_states.setCurrentCell(initial_count, 0)
        self.window.remove_selected_state()

        # Assert (Remove)
        self.assertEqual(self.window.table_states.rowCount(), initial_count)

if __name__ == '__main__':
    # Add src to path to allow running this test file directly
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    unittest.main()
