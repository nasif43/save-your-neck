import argparse
import random
import json
import time
import os
from concurrent.futures import ProcessPoolExecutor
from simulator.engine import GameEngine
from simulator.analysis import generate_report

STRATEGIES = [
    "Random", "Coward", "Aggressive", "Conservative", 
    "Opportunist", "ProtectionHoarder", "Chaos", "Adaptive"
]

def simulate_single_game(args) -> dict:
    seed, num_players = args
    random.seed(seed)
    # assign random strategies
    strats = random.choices(STRATEGIES, k=num_players)
    engine = GameEngine(num_players, strats)
    metrics = engine.run()
    
    alive = engine.state.get_alive_players()
    if len(alive) == 1:
        metrics["winner_strategy"] = alive[0].strategy_name
    else:
        metrics["winner_strategy"] = "None"
        
    metrics["num_players"] = num_players
    return metrics

def main():
    parser = argparse.ArgumentParser(description="Save Your Neck Simulator")
    parser.add_argument("--games", type=int, default=1000, help="Number of games to simulate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--workers", type=int, default=4, help="Number of worker processes")
    args = parser.parse_args()

    print(f"Simulating {args.games} games...")
    start_time = time.time()

    # Generate tasks for random player counts 3-8
    random.seed(args.seed)
    tasks = []
    for i in range(args.games):
        tasks.append((args.seed + i, random.randint(3, 8)))

    results = []
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        for res in executor.map(simulate_single_game, tasks):
            results.append(res)
            
    end_time = time.time()
    print(f"Simulation completed in {end_time - start_time:.2f} seconds.")

    out_dir = "simulation_results"
    os.makedirs(out_dir, exist_ok=True)
    
    results_file = os.path.join(out_dir, "results.json")
    with open(results_file, "w") as f:
        json.dump(results, f)
        
    print(f"Results saved to {results_file}")
    
    print("Generating report and plots...")
    generate_report(results_file, os.path.join(out_dir, "plots"))
    print(f"Report generated at {os.path.join(out_dir, 'REPORT.html')}")

if __name__ == "__main__":
    main()
