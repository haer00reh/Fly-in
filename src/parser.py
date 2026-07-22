from pydantic import BaseModel, FilePath
from pathlib import Path
import sys

class Config(BaseModel):
    nb_drones: int
    start_hub: str
    end_hub: str
    hubs: list[str]
    connections: list[tuple[str, str]]

class Parser(BaseModel):
    path: FilePath
    config_as_text: str
    config: Config

    def extract(self) -> None:
        with open(self.path, "r") as file:
            self.config_as_text = file.read()

    def inspect(self) -> bool:
        prefixes = ["nb_drones:", "start_hub:", "end_hub:", "hub:", "connection:"]
        config_table = self.config_as_text.splitlines()
        config_table[:] = (line.strip() for line in config_table)
        start_count = 0
        end_count = 0
        nb_drones_count = 0
        for line in config_table:
            if line.startswith("start_hub:"):
                start_count += 1
            elif line.startswith("end_hub:"):
                end_count += 1
            elif line.startswith("nb_drones:"):
                nb_drones_count += 1
        if start_count != 1 or end_count != 1 or nb_drones_count != 1:
            print(f"WATCH OUT!!\ninvalid count for either of these fields start_hub: {start_count}, end_hub: {end_count}, nb_drones: {nb_drones_count}\nall need to be one!!", file=sys.stderr)
            return False
        for line in config_table:
            if line.startswith(tuple(prefixes)):
                prefixes.remove(line.split(":", 1)[0] + ":")
        if not prefixes:
            return True
        else:
            print(f"WATCH OUT!!\nMissing prefixes: {prefixes}", file=sys.stderr)
            return False

def test_parser():
    parser = Parser(path=Path("/home/hayta/Fly-in/src/test.txt"), config_as_text="", config=Config(nb_drones=0, start_hub="", end_hub="", hubs=[], connections=[]))
    parser.extract()
    print(parser.inspect())

test_parser()