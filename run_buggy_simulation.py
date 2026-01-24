import json
from src.core.models import SystemModel
from src.engine.simulation_engine import SimulationEngine
from src.engine.analyzer import Analyzer
from src.parsers.json_parser import JSONParser

# Load the buggy model
with open('examples/airpods_charging_buggy.json', 'r') as f:
    model_json = f.read()
model = JSONParser().parse(model_json)

# Instantiate Engine
engine = SimulationEngine(model)

# Run BFS Explorer
print("Starting BFS simulation with the buggy scenario...")
state_graph = engine.run_bfs_explorer()
print(f"BFS simulation complete. Found {state_graph.number_of_nodes()} states.")

# Instantiate Analyzer
analyzer = Analyzer(model, state_graph)

# Find violations
print("Analyzing results for constraint violations...")
violations = analyzer.find_constraint_violations()

# Report findings
if not violations:
    print("❌ UNEXPECTED: No constraint violations found. The bug was not detected.")
else:
    print("🔥 SUCCESS: The simulator found the corner case!")
    for v in violations:
        print("\n--- VIOLATION DETECTED ---")
        print(f"  Constraint: '{v['constraint']}'")
        print(f"  Violated State: {v['state']}")
        print(f"  Path to violation (how to reproduce):")

        path_str = " -> ".join(v['path']) if v['path'] else "[Initial State]"
        print(f"    Initial State -> {path_str}")
