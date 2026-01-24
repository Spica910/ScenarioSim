"""
Dialog for configuring the Gemini API Key.
"""
import json
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox

CONFIG_FILE = "config.json"

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.label = QLabel("Enter your Google Gemini API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Paste your API key here")
        self.api_key_input.setEchoMode(QLineEdit.Password)

        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.api_key_input)
        self.layout.addWidget(self.save_button)
        self.layout.addWidget(self.cancel_button)

        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button.clicked.connect(self.reject)

        self.load_settings()

    def load_settings(self):
        """Loads the API key from the config file."""
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                self.api_key_input.setText(config.get("api_key", ""))
        except FileNotFoundError:
            # Config file doesn't exist yet, do nothing.
            pass
        except json.JSONDecodeError:
            QMessageBox.warning(self, "Error", f"Could not parse {CONFIG_FILE}. It may be corrupted.")


    def save_settings(self):
        """Saves the API key to the config file."""
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Warning", "API Key cannot be empty.")
            return

        config = {"api_key": api_key}
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=2)
            QMessageBox.information(self, "Success", "API Key saved successfully.")
            self.accept()
        except IOError as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

def get_api_key():
    """Utility function to read the API key from the config file."""
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            return config.get("api_key")
    except (FileNotFoundError, json.JSONDecodeError):
        return None
