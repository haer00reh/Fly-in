from pydantic import BaseModel
import sys

class hub(BaseModel):
    name: str
    x: int
    y: int
    meta_data_as_text: str
    color: str
    max_drones: int

    def init_metadata(self):
        self.color, self.max_drones = hub_parser(self.meta_data_as_text)




class connection(BaseModel):
    hub1: hub
    hub2: hub
    link_cap: int
    meta_data_as_text: str
    max_link_capacity: int

    def init_metadata(self):
        self.max_link_capacity = link_parser(self.meta_data_as_text)


class end_hub(hub):
    pass


class start_hub(hub):
    pass


class drone(BaseModel):
    id: int
    start_hub: hub
    end_hub: hub


def link_parser(line: str):
    if "max_link_capacity" in line:
        max_link_capacity = line.split("max_link_capacity=")[1].split()[0]
        if int(max_link_capacity) < 0:
            print(f"WATCH OUT!!\nError: invalid max_link_capacity '{max_link_capacity}'", file=sys.stderr)
            sys.exit(1)
        return int(max_link_capacity)

def hub_parser(line: str):
    package = []
    if "color" in line:
        color = line.split("color=")[1].split()[0]
        package.append(color)
    if "max_drones" in line:
        max_drones = line.split("max_drones=")[1].split()[0]
        if int(max_drones) < 0:
            print(f"WATCH OUT!!\nError: invalid max_drones '{max_drones}'", file=sys.stderr)
            sys.exit(1)
        package.append(int(max_drones))
    return tuple(package)

class Config(BaseModel):
    drones: list[drone] = []
    start: start_hub = start_hub(name="", x=0, y=0, meta_data="")
    end: end_hub = end_hub(name="", x=0, y=0, meta_data="")
    hubs: list[hub] = []
    connections: list[connection] = []

    def error_teller(self, additional_message: str, line_nb: int) -> None:
        if line_nb > 0:
            print(f"WATCH OUT!!\nError on line {line_nb}: {additional_message}", file=sys.stderr)
        else:
            print(f"WATCH OUT!!\nError: {additional_message}", file=sys.stderr)
        sys.exit(1)

    def init(self, config_table: dict[int, str]) -> bool:
        for key, line in config_table.items():
            self.search_line(line, key)

    def valid_name(self, name: str, line_nb: int) -> bool:
        if '-' in name:
            self.error_teller(f"invalid name '{name}'", line_nb)
            sys.exit(1)

    def search_line(self, line: str, line_nb: int) -> bool:
        if line.startswith("nb_drones:"):
            nb_drones = int(line.split(":")[1].strip())
            for i in range(nb_drones):
                self.drones.append(drone(id=i+1, start_hub=self.start, end_hub=self.end))
        elif line.startswith("start_hub:"):
            self.start.name = line.split()[1].strip()
            self.valid_name(self.start.name, line_nb)
            self.start.x = int(line.split()[2].strip())
            self.start.y = int(line.split()[3].strip())
            self.start.meta_data = line.split()[4].strip()
        elif line.startswith("end_hub:"):
            self.end.name = line.split()[1].strip()
            self.valid_name(self.end.name, line_nb)
            self.end.x = int(line.split()[2].strip())
            self.end.y = int(line.split()[3].strip())
            self.end.meta_data = line.split()[4].strip()
        elif line.startswith("hub:"):
            hub_name = line.split()[1].strip()
            self.valid_name(hub_name, line_nb)
            hub_x = int(line.split()[2].strip())
            hub_y = int(line.split()[3].strip())
            hub_meta_data = line.split()[4].strip()
            self.hubs.append(hub(name=hub_name, x=hub_x, y=hub_y, meta_data_as_text=hub_meta_data))
        elif line.startswith("connection:"):
            hub1_name = line.split("-")[0].split()[1].strip()
            hub2_name = line.split("-")[1].strip()

