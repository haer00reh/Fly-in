"""Run the parser, simulation, and visualization pipeline."""

from pathlib import Path

from .config_maker import Config
from .parser import Parser
from .simulation_engine import simulation_engine
from .visualizer import MapVisualizer
import sys


def main() -> None:
    """Run the parser, simulation, and visualization pipeline."""
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("src/map.txt")
    parser = Parser(path=path)
    parser.do_your_job()
    config = Config()
    config.init(parser.config_table)
    sim_engine = simulation_engine(config=config)
    sim_engine.path_finder()
    vis = MapVisualizer(config)
    vis.run_visualizer(config, sim_engine.turn_scheduler())


if __name__ == "__main__":
    main()
