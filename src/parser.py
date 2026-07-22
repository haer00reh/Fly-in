from pydantic import BaseModel, FilePath
from pathlib import Path
import sys


class Parser(BaseModel):
    path: FilePath
    config_as_text: str = ""
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

    def do_your_job(self) -> None:
        try:
            self.extract()
            if not self.inspect():
                sys.exit(1)
        except Exception as e:
            print(f"WATCH OUT!!\nthere was an error that occurred: {e}", file=sys.stderr)
            sys.exit(1)

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
    parser = Parser(path=Path("/home/hayta/Fly-in/src/test.txt"))
    parser.do_your_job()

test_parser()