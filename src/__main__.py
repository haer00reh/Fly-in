"""Run the parser, simulation, and visualization pipeline."""

from pathlib import Path

from .config_maker import Config
from .parser import Parser
from .simulation_engine import simulation_engine
from .visualizer import MapVisualizer
import sys


def main() -> None:
    """Run the parser, simulation, and visualization pipeline."""
    try:
        path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("src/map.txt")
        parser = Parser(path=path)
        parser.init()
        config = Config()
        config.init(parser.config_table)
        sim_engine = simulation_engine(config=config)
        sim_engine.path_finder()
        sim_output, connection_occupancy = sim_engine.turn_scheduler()
        visualizer = MapVisualizer(config=config)

        visualizer.run_visualizer(config=config, sim_output=sim_output,
                                  connection_occupancy=connection_occupancy)
    except BaseException as e:
        print(e)
        pass


if __name__ == "__main__":
    main()
