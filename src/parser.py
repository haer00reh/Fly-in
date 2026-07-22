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
    config_table: list[str] = []

    def extract(self) -> None:
        with open(self.path, "r") as file:
            self.config_as_text = file.read()

    def garbage_remover(self) -> None:
        prefixes = ["nb_drones:", "start_hub:", "end_hub:", "hub:", "connection:"]
        self.config_table = self.config_as_text.splitlines()
        self.config_table[:] = (line.strip() for line in self.config_table)
        for line in self.config_table[:]:
            if not line.startswith(tuple(prefixes)):
                self.config_table.remove(line)

    def inspect(self) -> bool:
        prefixes = ["nb_drones:", "start_hub:", "end_hub:", "hub:", "connection:"]
        start_count = 0
        end_count = 0
        nb_drones_count = 0
        self.garbage_remover()
        for line in self.config_table:
            if line.startswith("start_hub:"):
                start_count += 1
            elif line.startswith("end_hub:"):
                end_count += 1
            elif line.startswith("nb_drones:"):
                nb_drones_count += 1
        if start_count != 1 or end_count != 1 or nb_drones_count != 1:
            print(f"WATCH OUT!!\ninvalid count for either of these fields start_hub: {start_count}, end_hub: {end_count}, nb_drones: {nb_drones_count}\nall need to be one!!", file=sys.stderr)
            return False
        for line in self.config_table:
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