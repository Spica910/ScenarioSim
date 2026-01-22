"""
Command-Line Interface (CLI) for the simulator.
"""
import json
import argparse
from src.parsers.json_parser import JSONParser
from src.engine.simulation_engine import SimulationEngine
from src.engine.analyzer import Analyzer
from src.ui.visualizer import generate_graph_visualization

def main_cli():
    """
    Main function for the CLI.
    """
    parser = argparse.ArgumentParser(description="Battery Scenario Simulator CLI")
    parser.add_argument("scenario_file", help="Path to the scenario JSON file.")
    parser.add_argument(
        "--mode",
        choices=['bfs', 'monte_carlo'],
        default='bfs',
        help="The simulation mode to use."
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=100,
        help="Number of steps for Monte Carlo simulation."
    )
    parser.add_argument(
        "--output-graph",
        help="Path to save the graph visualization image (e.g., 'graph.png')."
    )

    args = parser.parse_args()

    print("--- Battery Scenario Simulator CLI ---")
    print(f"Loading scenario from: {args.scenario_file}\n")

    try:
        with open(args.scenario_file, 'r', encoding='utf-8') as f:
            json_data = f.read()
    except FileNotFoundError:
        print(f"Error: Example file not found at '{args.scenario_file}'")
        return

    # 1. Parsing
    json_parser = JSONParser()
    system_model = json_parser.parse(json_data)
    print(f"Successfully parsed model: '{system_model.name}'")
    print(f" - States: {len(system_model.states)}")
    print(f" - Events: {len(system_model.events)}\n")

    # 2. Simulation
    engine = SimulationEngine(system_model)

    if args.mode == 'bfs':
        print("Running BFS State Space Explorer...")
        state_graph = engine.run_bfs_explorer()
    elif args.mode == 'monte_carlo':
        print(f"Running Monte Carlo Explorer for {args.steps} steps...")
        state_graph = engine.run_monte_carlo_explorer(args.steps)

    print(f"Exploration complete. Found {state_graph.number_of_nodes()} states and {state_graph.number_of_edges()} transitions.\n")

    # 3. Optional Visualization
    if args.output_graph:
        generate_graph_visualization(state_graph, args.output_graph)

    # 4. Analysis
    print("Analyzing for violations...")
    analyzer = Analyzer(system_model, state_graph)

    constraint_violations = analyzer.find_constraint_violations()
    goal_violations = analyzer.find_goal_violations()
    deadlocks = analyzer.find_deadlocks()

    if not constraint_violations and not goal_violations and not deadlocks:
        print("✅ Analysis complete. No issues found!")
    else:
        print("❌ Analysis complete. Issues found:")
        if constraint_violations:
            print("\n--- Constraint Violations ---")
            for v in constraint_violations:
                print(f"  - Constraint: '{v['constraint']}' violated.")
                print(f"    State: {v['state']}")
                print(f"    Path: {' -> '.join(v['path'])}")

        if goal_violations:
            print("\n--- Goal Violations ---")
            for v in goal_violations:
                print(f"  - Goal: '{v['goal']}' violated.")
                print(f"    State: {v['state']}")
                print(f"    Path: {' -> '.join(v['path'])}")

        if deadlocks:
            print("\n--- Deadlocks Found ---")
            for d in deadlocks:
                print(f"  - Deadlock detected at state: {d['state']}")
                print(f"    Path: {' -> '.join(d['path'])}")

if __name__ == '__main__':
    main_cli()
