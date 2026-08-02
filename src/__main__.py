from config_maker import Config, hub, connection, start_hub, end_hub, drone
from parser import Parser
from pathlib import Path
from simulation_engine import simulation_engine

def test_parser():
    parser = Parser(path=Path("/home/hayta/Fly-in/src/test.txt"))
    parser.do_your_job()
    config = Config()
    config.init(parser.config_table)
    sim_engine = simulation_engine(config=config)
    sim_engine.path_finder()

test_parser()