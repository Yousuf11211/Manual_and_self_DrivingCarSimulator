import neat
import os
import sys
import argparse
from simulation import run_car

def main() -> None:
    parser = argparse.ArgumentParser(description="NEAT Car Simulation")
    parser.add_argument('--generations', type=int, default=1000, help="Number of generations to run")
    args = parser.parse_args()

    project_folder = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(project_folder, 'config.txt')

    if not os.path.exists(config_path):
        print(f"Error: Configuration file '{config_path}' not found.")
        sys.exit(1)

    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path
    )

    population = neat.Population(config)
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)
    # Save checkpoints every 10 generations.
    population.add_reporter(neat.Checkpointer(10, filename_prefix="neat-checkpoint-"))

    population.run(run_car, args.generations)

if __name__ == "__main__":
    main()
