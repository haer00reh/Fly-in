from config_maker import Config, hub, connection, start_hub, end_hub, drone
from parser import Parser
from pathlib import Path


def test_parser():
    parser = Parser(path=Path("/home/hayta/Fly-in/src/test.txt"))
    parser.do_your_job()
    config = Config(config_table=parser.config_table)
    config.init()

test_parser()