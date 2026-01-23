"""
Main window for the Scenario Simulator GUI.
"""
import sys
import json
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QListWidget, QTextEdit,
    QLineEdit, QFormLayout, QHeaderView, QLabel, QComboBox, QTextBrowser,
    QFileDialog, QSpinBox, QMessageBox, QSplitter
)
from src.core.models import SystemModel, StateVariable, Event, Constraint, Goal
from src.engine.simulation_engine import SimulationEngine
from src.engine.analyzer import Analyzer
from src.parsers.json_parser import JSONParser
# from src.ui.llm_dialog import LlmImportDialog # Temporarily disabled
from src.ui.visualizer import generate_graph_visualization

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scenario Editor & Simulator")
        self.setGeometry(100, 100, 1200, 800)
        self.current_model = SystemModel(name="New Scenario")
        self.active_list_widget = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.create_menu_bar()
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs, 3)

        sim_control_layout = QHBoxLayout()
        self.combo_sim_mode = QComboBox()
        self.combo_sim_mode.addItems(["BFS", "Monte Carlo"])
        self.spin_mc_steps = QSpinBox()
        self.spin_mc_steps.setRange(10, 100000); self.spin_mc_steps.setValue(100)
        self.btn_run_simulation = QPushButton("Run Simulation")
        sim_control_layout.addWidget(QLabel("Simulation Mode:"))
        sim_control_layout.addWidget(self.combo_sim_mode)
        sim_control_layout.addWidget(QLabel("MC Steps:"))
        sim_control_layout.addWidget(self.spin_mc_steps)
        sim_control_layout.addWidget(self.btn_run_simulation)
        main_layout.addLayout(sim_control_layout)

        results_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(results_splitter, 1)

        self.results_browser = QTextBrowser()
        self.results_browser.setPlaceholderText("Simulation results will be displayed here.")
        self.graph_display_label = QLabel("Graph visualization will appear here.")
        self.graph_display_label.setObjectName("graph_display_label")
        self.graph_display_label.setAlignment(Qt.AlignCenter)
        results_splitter.addWidget(self.results_browser)
        results_splitter.addWidget(self.graph_display_label)
        results_splitter.setSizes([400, 600])

        self.create_states_tab()
        self.create_events_tab()
        self.create_constraints_goals_tab()

        self.btn_run_simulation.clicked.connect(self.run_simulation)

    def create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        open_action = file_menu.addAction("Open...")
        save_action = file_menu.addAction("Save As...")
        # import_text_action = file_menu.addAction("Import from Text...") # Temporarily disabled
        open_action.triggered.connect(self.open_file)
        save_action.triggered.connect(self.save_file)
        # import_text_action.triggered.connect(self.show_llm_import_dialog)

    def create_states_tab(self):
        tab_states = QWidget()
        layout = QVBoxLayout(tab_states)
        self.table_states = QTableWidget()
        self.table_states.setColumnCount(4)
        self.table_states.setHorizontalHeaderLabels(["Name", "Type", "Initial Value", "Range/Enum"])
        self.table_states.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_states)
        button_layout = QHBoxLayout()
        btn_add_state = QPushButton("Add State"); btn_remove_state = QPushButton("Remove State")
        btn_add_state.clicked.connect(self.add_state_row)
        btn_remove_state.clicked.connect(self.remove_selected_state)
        button_layout.addWidget(btn_add_state); button_layout.addWidget(btn_remove_state)
        layout.addLayout(button_layout)
        self.tabs.addTab(tab_states, "States")
        self.table_states.cellChanged.connect(self.update_state_in_model)

    def add_state_row(self):
        row_position = self.table_states.rowCount()
        self.table_states.insertRow(row_position)
        new_state = StateVariable(name=f"new_state_{row_position}", type="int", initial_value=0)
        self.current_model.states.append(new_state)

    def remove_selected_state(self):
        current_row = self.table_states.currentRow()
        if current_row >= 0:
            self.table_states.removeRow(current_row)
            del self.current_model.states[current_row]

    def update_state_in_model(self, row, column):
        if not self.current_model or row >= len(self.current_model.states): return
        state_var = self.current_model.states[row]
        item_text = self.table_states.item(row, column).text()
        self.table_states.cellChanged.disconnect(self.update_state_in_model)
        try:
            if column == 0: state_var.name = item_text
            elif column == 1: state_var.type = item_text
            elif column == 2:
                if state_var.type == 'int': state_var.initial_value = int(item_text)
                elif state_var.type == 'bool': state_var.initial_value = item_text.lower() in ['true', '1']
                else: state_var.initial_value = item_text
            elif column == 3:
                try:
                    parsed_val = eval(item_text)
                    if isinstance(parsed_val, tuple) and len(parsed_val) == 2:
                        state_var.range = parsed_val; state_var.enum_values = None
                    elif isinstance(parsed_val, list):
                        state_var.enum_values = [str(v) for v in parsed_val]; state_var.range = None
                except: pass
        except (ValueError, TypeError) as e: print(f"Error: {e}")
        self.table_states.cellChanged.connect(self.update_state_in_model)

    def create_events_tab(self):
        tab_events = QWidget()
        layout = QHBoxLayout(tab_events)
        left_widget = QWidget(); left_layout = QVBoxLayout(left_widget); left_widget.setMaximumWidth(300)
        self.list_events = QListWidget(); left_layout.addWidget(self.list_events)
        event_button_layout = QHBoxLayout()
        btn_add_event = QPushButton("Add"); btn_remove_event = QPushButton("Remove")
        event_button_layout.addWidget(btn_add_event); event_button_layout.addWidget(btn_remove_event)
        left_layout.addLayout(event_button_layout)
        editor_widget = QWidget(); editor_layout = QFormLayout(editor_widget)
        self.edit_event_name = QLineEdit(); self.edit_event_condition = QTextEdit(); self.edit_event_effect = QTextEdit()
        editor_layout.addRow("Name:", self.edit_event_name)
        editor_layout.addRow("Condition (Python):", self.edit_event_condition)
        editor_layout.addRow("Effect (Python):", self.edit_event_effect)
        layout.addWidget(left_widget); layout.addWidget(editor_widget, 2)
        self.tabs.addTab(tab_events, "Events")
        btn_add_event.clicked.connect(self.add_event)
        btn_remove_event.clicked.connect(self.remove_selected_event)
        self.list_events.currentItemChanged.connect(self.display_selected_event)
        self.edit_event_name.textChanged.connect(self.update_event_in_model)
        self.edit_event_condition.textChanged.connect(self.update_event_in_model)
        self.edit_event_effect.textChanged.connect(self.update_event_in_model)

    def add_event(self):
        new_event = Event(name=f"new_event_{len(self.current_model.events)}", effect="# Enter Python code")
        self.current_model.events.append(new_event)
        self.refresh_event_list(); self.list_events.setCurrentRow(self.list_events.count() - 1)

    def remove_selected_event(self):
        current_row = self.list_events.currentRow()
        if current_row >= 0:
            del self.current_model.events[current_row]
            self.refresh_event_list()

    def display_selected_event(self, current, prev):
        if not current:
            self.edit_event_name.clear(); self.edit_event_condition.clear(); self.edit_event_effect.clear()
            return
        row = self.list_events.currentRow()
        if 0 <= row < len(self.current_model.events):
            event = self.current_model.events[row]
            self.edit_event_name.blockSignals(True); self.edit_event_condition.blockSignals(True); self.edit_event_effect.blockSignals(True)
            self.edit_event_name.setText(event.name)
            self.edit_event_condition.setPlainText(event.condition)
            self.edit_event_effect.setPlainText(event.effect)
            self.edit_event_name.blockSignals(False); self.edit_event_condition.blockSignals(False); self.edit_event_effect.blockSignals(False)

    def update_event_in_model(self):
        row = self.list_events.currentRow()
        if 0 <= row < len(self.current_model.events):
            event = self.current_model.events[row]
            event.name = self.edit_event_name.text()
            event.condition = self.edit_event_condition.toPlainText()
            event.effect = self.edit_event_effect.toPlainText()
            self.list_events.item(row).setText(event.name)

    def create_constraints_goals_tab(self):
        tab_cg = QWidget(); layout = QHBoxLayout(tab_cg)
        constraints_col = QVBoxLayout(); constraints_col.addWidget(QLabel("<b>Constraints</b>"))
        self.list_constraints = QListWidget(); constraints_col.addWidget(self.list_constraints)
        constraint_btns = QHBoxLayout()
        btn_add_constraint = QPushButton("Add"); btn_remove_constraint = QPushButton("Remove")
        constraint_btns.addWidget(btn_add_constraint); constraint_btns.addWidget(btn_remove_constraint)
        constraints_col.addLayout(constraint_btns)
        goals_col = QVBoxLayout(); goals_col.addWidget(QLabel("<b>Goals</b>"))
        self.list_goals = QListWidget(); goals_col.addWidget(self.list_goals)
        goal_btns = QHBoxLayout()
        btn_add_goal = QPushButton("Add"); btn_remove_goal = QPushButton("Remove")
        goal_btns.addWidget(btn_add_goal); goal_btns.addWidget(btn_remove_goal)
        goals_col.addLayout(goal_btns)
        editor_widget = QWidget(); editor_layout = QFormLayout(editor_widget)
        self.edit_cg_description = QLineEdit()
        self.edit_cg_expression = QTextEdit()
        solver_layout = QHBoxLayout()
        self.spin_solver_steps = QSpinBox(); self.spin_solver_steps.setRange(1, 100); self.spin_solver_steps.setValue(5)
        self.btn_run_solver = QPushButton("Find Violation with Solver")
        solver_layout.addWidget(QLabel("Max Steps:")); solver_layout.addWidget(self.spin_solver_steps)
        solver_layout.addWidget(self.btn_run_solver)
        editor_layout.addRow("Description:", self.edit_cg_description)
        editor_layout.addRow("Expression (Python):", self.edit_cg_expression)
        editor_layout.addRow(solver_layout)
        layout.addLayout(constraints_col, 1); layout.addLayout(goals_col, 1)
        layout.addWidget(editor_widget, 2)
        self.tabs.addTab(tab_cg, "Constraints & Goals")
        btn_add_constraint.clicked.connect(self.add_constraint)
        btn_remove_constraint.clicked.connect(self.remove_constraint)
        btn_add_goal.clicked.connect(self.add_goal)
        btn_remove_goal.clicked.connect(self.remove_goal)
        self.list_constraints.currentItemChanged.connect(self.display_selected_cg)
        self.list_goals.currentItemChanged.connect(self.display_selected_cg)
        self.edit_cg_description.textChanged.connect(self.update_cg_in_model)
        self.edit_cg_expression.textChanged.connect(self.update_cg_in_model)
        self.btn_run_solver.clicked.connect(self.run_solver_simulation)

    def add_constraint(self):
        new_c = Constraint(description=f"New Constraint {len(self.current_model.constraints)}", expression="True")
        self.current_model.constraints.append(new_c); self.refresh_cg_lists()
        self.list_constraints.setCurrentRow(self.list_constraints.count() - 1)

    def remove_constraint(self):
        row = self.list_constraints.currentRow()
        if row >= 0: del self.current_model.constraints[row]; self.refresh_cg_lists()

    def add_goal(self):
        new_g = Goal(description=f"New Goal {len(self.current_model.goals)}", expression="True")
        self.current_model.goals.append(new_g); self.refresh_cg_lists()
        self.list_goals.setCurrentRow(self.list_goals.count() - 1)

    def remove_goal(self):
        row = self.list_goals.currentRow()
        if row >= 0: del self.current_model.goals[row]; self.refresh_cg_lists()

    def display_selected_cg(self, current, previous):
        sender = self.sender()
        if sender == self.list_constraints:
            if self.active_list_widget != self.list_constraints: self.list_goals.clearSelection()
            self.active_list_widget = self.list_constraints
        elif sender == self.list_goals:
            if self.active_list_widget != self.list_goals: self.list_constraints.clearSelection()
            self.active_list_widget = self.list_goals
        if not current:
            self.edit_cg_description.clear(); self.edit_cg_expression.clear()
            return
        row = self.active_list_widget.currentRow()
        item_list = self.current_model.constraints if self.active_list_widget == self.list_constraints else self.current_model.goals
        if 0 <= row < len(item_list):
            item = item_list[row]
            self.edit_cg_description.blockSignals(True); self.edit_cg_expression.blockSignals(True)
            self.edit_cg_description.setText(item.description)
            self.edit_cg_expression.setPlainText(item.expression)
            self.edit_cg_description.blockSignals(False); self.edit_cg_expression.blockSignals(False)

    def update_cg_in_model(self):
        if not self.active_list_widget: return
        row = self.active_list_widget.currentRow()
        item_list = self.current_model.constraints if self.active_list_widget == self.list_constraints else self.current_model.goals
        if 0 <= row < len(item_list):
            item = item_list[row]
            item.description = self.edit_cg_description.text()
            item.expression = self.edit_cg_expression.toPlainText()
            self.active_list_widget.item(row).setText(item.description)

    def load_model_to_ui(self, model: SystemModel):
        self.current_model = model; self.setWindowTitle(f"Scenario Editor & Simulator - {model.name}")
        self.table_states.cellChanged.disconnect(self.update_state_in_model)
        self.table_states.setRowCount(0)
        for state_var in model.states:
            row = self.table_states.rowCount(); self.table_states.insertRow(row)
            self.table_states.setItem(row, 0, QTableWidgetItem(state_var.name))
            self.table_states.setItem(row, 1, QTableWidgetItem(state_var.type))
            self.table_states.setItem(row, 2, QTableWidgetItem(str(state_var.initial_value)))
            range_enum_str = "";
            if state_var.range: range_enum_str = str(state_var.range)
            elif state_var.enum_values: range_enum_str = str(state_var.enum_values)
            self.table_states.setItem(row, 3, QTableWidgetItem(range_enum_str))
        self.table_states.cellChanged.connect(self.update_state_in_model)
        self.refresh_event_list(); self.refresh_cg_lists()

    def refresh_event_list(self):
        self.list_events.currentItemChanged.disconnect(self.display_selected_event)
        self.list_events.clear()
        for event in self.current_model.events: self.list_events.addItem(event.name)
        self.list_events.currentItemChanged.connect(self.display_selected_event)

    def refresh_cg_lists(self):
        self.list_constraints.currentItemChanged.disconnect(self.display_selected_cg)
        self.list_goals.currentItemChanged.disconnect(self.display_selected_cg)
        self.list_constraints.clear(); self.list_goals.clear()
        for c in self.current_model.constraints: self.list_constraints.addItem(c.description)
        for g in self.current_model.goals: self.list_goals.addItem(g.description)
        self.list_constraints.currentItemChanged.connect(self.display_selected_cg)
        self.list_goals.currentItemChanged.connect(self.display_selected_cg)

    def run_simulation(self):
        self.results_browser.clear(); self.graph_display_label.clear()
        self.results_browser.setText("Updating model and running simulation...")
        model = self.current_model
        if not model.states: self.results_browser.setText("Error: No states defined."); return
        engine = SimulationEngine(model)
        mode = self.combo_sim_mode.currentText()
        if mode == "BFS": state_graph = engine.run_bfs_explorer()
        else: state_graph = engine.run_monte_carlo_explorer(self.spin_mc_steps.value())
        analyzer = Analyzer(model, state_graph)
        constraint_v = analyzer.find_constraint_violations(); goal_v = analyzer.find_goal_violations(); deadlocks = analyzer.find_deadlocks()
        report = [f"<b>--- Simulation Complete ---</b>", f"Mode: {mode}", f"Found {state_graph.number_of_nodes()} states and {state_graph.number_of_edges()} transitions."]
        if not any([constraint_v, goal_v, deadlocks]): report.append("<br><b><font color='green'>✅ No issues found!</font></b>")
        else:
            if constraint_v:
                report.append("<br><b><font color='red'>Constraint Violations:</font></b>")
                for v in constraint_v: report.append(f"- <b>{v['constraint']}</b> violated...<br>  Path: {' -> '.join(v['path'])}")
            if goal_v:
                report.append("<br><b><font color='orange'>Goal Violations:</font></b>")
                for v in goal_v: report.append(f"- <b>{v['goal']}</b> violated...<br>  Path: {' -> '.join(v['path'])}")
            if deadlocks:
                report.append("<br><b><font color='blue'>Deadlocks Found:</font></b>")
                for d in deadlocks: report.append(f"- Deadlock at state: {d['state']}")
        self.results_browser.setHtml("<br>".join(report))
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp: temp_graph_path = tmp.name
        generate_graph_visualization(state_graph, temp_graph_path)
        pixmap = QPixmap(temp_graph_path)
        self.graph_display_label.setPixmap(pixmap.scaled(self.graph_display_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        os.remove(temp_graph_path)

    def run_solver_simulation(self):
        if self.active_list_widget != self.list_goals or self.list_goals.currentRow() < 0:
            self.results_browser.setText("Please select a goal to check for violations.")
            return
        goal = self.current_model.goals[self.list_goals.currentRow()]
        max_steps = self.spin_solver_steps.value()
        self.results_browser.setText(f"Running Z3 Solver to find a violation for goal: '{goal.description}' within {max_steps} steps...")
        engine = SimulationEngine(self.current_model)
        result = engine.run_solver_explorer(goal.expression, max_steps)

        if isinstance(result, list):
            path_str = " -> ".join(result)
            display_text = f"<b>--- Solver Result ---</b><br>Found a violation path:<br>{path_str}"
        else:
            display_text = f"<b>--- Solver Result ---</b><br>{result}"

        self.results_browser.setHtml(display_text)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Scenario", "", "JSON Files (*.json)")
        if file_path:
            msg_box = QMessageBox(self); msg_box.setIcon(QMessageBox.Warning); msg_box.setText("Security Warning")
            msg_box.setInformativeText("Loading a scenario file will execute Python code embedded within it.\n\nOnly open files from sources you trust.")
            msg_box.setStandardButtons(QMessageBox.Open | QMessageBox.Cancel); msg_box.setDefaultButton(QMessageBox.Cancel)
            if msg_box.exec() == QMessageBox.Cancel: return
            try:
                with open(file_path, 'r', encoding='utf-8') as f: model = JSONParser().parse(f.read())
                self.load_model_to_ui(model)
            except Exception as e: self.results_browser.setText(f"Error opening file: {e}")

    def save_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Scenario As", "", "JSON Files (*.json)")
        if file_path:
            try:
                json_data = self.current_model.model_dump_json(indent=2)
                with open(file_path, 'w', encoding='utf-8') as f: f.write(json_data)
                self.results_browser.setText(f"Scenario saved to {file_path}")
            except Exception as e: self.results_browser.setText(f"Error saving file: {e}")

    # def show_llm_import_dialog(self):
    #     from src.ui.llm_dialog import LlmImportDialog
    #     dialog = LlmImportDialog(self); dialog.model_parsed.connect(self.load_model_to_ui); dialog.exec()

def start_gui():
    app = QApplication(sys.argv)
    window = MainWindow()
    try:
        with open("examples/airpods_charging.json", 'r') as f: model = JSONParser().parse(f.read())
        window.load_model_to_ui(model)
    except FileNotFoundError: pass
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    start_gui()
