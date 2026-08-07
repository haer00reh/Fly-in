"""Run the parser, simulation, and visualization pipeline."""

from pathlib import Path

from config_maker import Config
from parser import Parser
from simulation_engine import simulation_engine
from visualizer import MapVisualizer


def test_parser() -> None:
    """Run the parser, simulation, and visualization pipeline."""
    parser = Parser(path=Path("/home/hayta/Fly-in/src/test.txt"))
    parser.do_your_job()
    config = Config()
    config.init(parser.config_table)
    sim_engine = simulation_engine(config=config)
    sim_engine.path_finder()
    vis = MapVisualizer(config)
    vis.run_visualizer(config, sim_engine.turn_scheduler())


test_parser()
