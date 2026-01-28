"""
Dialog for importing a scenario from a natural language text description.
"""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPlainTextEdit, QPushButton, QDialogButtonBox

class LlmImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Scenario from Text")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setMinimumSize(400, 300)

        self.label = QLabel("Paste or type your scenario description below:")
        self.text_edit = QPlainTextEdit()

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Rename the "OK" button to "Import" for clarity
        self.button_box.button(QDialogButtonBox.Ok).setText("Import")

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.text_edit)
        self.layout.addWidget(self.button_box)

    def get_text(self):
        """Returns the text entered by the user."""
        return self.text_edit.toPlainText()
