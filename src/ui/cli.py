"""
Command-Line Interface (CLI) for the simulator.
"""
import json
import argparse
from src.core.models import SystemModel
from src.parsers.json_parser import JSONParser
from src.parsers.llm_parser import LLMParser
from src.engine.simulation_engine import SimulationEngine
from src.engine.analyzer import Analyzer
from src.ui.visualizer import generate_graph_visualization

def main_cli():
    """
    Main function for the CLI.
    """
    parser = argparse.ArgumentParser(description="Battery Scenario Simulator CLI")
    parser.add_argument(
        "scenario_input",
        help="Path to the scenario file or the natural language scenario as a string."
    )
    parser.add_argument(
        "--parser",
        choices=['json', 'llm'],
        default='json',
        help="The parser to use for the scenario input."
    )
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

    system_model: SystemModel = None

    # 1. Parsing
    if args.parser == 'json':
        print(f"Loading JSON scenario from: {args.scenario_input}\n")
        try:
            with open(args.scenario_input, 'r', encoding='utf-8') as f:
                input_data = f.read()
            parser = JSONParser()
            system_model = parser.parse(input_data)
        except FileNotFoundError:
            print(f"Error: Scenario file not found at '{args.scenario_input}'")
            return
    elif args.parser == 'llm':
        print("Parsing natural language scenario with LLM...")
        # Check for API key
        import os
        if not os.environ.get("GOOGLE_API_KEY"):
            print("\nError: The GOOGLE_API_KEY environment variable is not set.")
            print("Please set it to your Gemini API key to use the LLM parser.")
            return

        parser = LLMParser()
        system_model = parser.parse(args.scenario_input)

    if not system_model or not system_model.name:
        print("Failed to parse the model. Exiting.")
        return
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
