from pydantic import BaseModel
import sys

class hub(BaseModel):
    name: str
    x: int
    y: int
    meta_data: str


class connection(BaseModel):
    hub1: hub
    hub2: hub
    meta_data: str


class end_hub(hub):
    pass


class start_hub(hub):
    pass


class drone(BaseModel):
    id: int
    start_hub: hub
    end_hub: hub



class Config(BaseModel):
    drones: list[drone] = []
    start: start_hub = start_hub(name="", x=0, y=0, meta_data="")
    end: end_hub = end_hub(name="", x=0, y=0, meta_data="")
    hubs: list[hub] = []
    connections: list[connection] = []
    config_table: list[str] 

    def init(self) -> bool:
        for line in self.config_table:
            self.search_line(line)

    def valid_name(self, name: str) -> bool:
        if '-' in name:
            print(f"WATCH OUT!!\ninvalid name: {name}\nname cannot contain '-' character", file=sys.stderr)
            sys.exit(1)

    def search_line(self, line: str) -> bool:
        if line.startswith("nb_drones:"):
            nb_drones = int(line.split(":")[1].strip())
            for i in range(nb_drones):
                self.drones.append(drone(id=i+1, start_hub=self.start, end_hub=self.end))
        elif line.startswith("start_hub:"):
            self.start.name = line.split()[1].strip()
            self.valid_name(self.start.name)
            self.start.x = int(line.split()[2].strip())
            self.start.y = int(line.split()[3].strip())
            self.start.meta_data = line.split()[4].strip()
        elif line.startswith("end_hub:"):
            self.end.name = line.split()[1].strip()
            self.valid_name(self.end.name)
            self.end.x = int(line.split()[2].strip())
            self.end.y = int(line.split()[3].strip())
            self.end.meta_data = line.split()[4].strip()
        elif line.startswith("hub:"):
            hub_name = line.split()[1].strip()
            self.valid_name(hub_name)
            hub_x = int(line.split()[2].strip())
            hub_y = int(line.split()[3].strip())
            hub_meta_data = line.split()[4].strip()
            self.hubs.append(hub(name=hub_name, x=hub_x, y=hub_y, meta_data=hub_meta_data))
        elif line.startswith("connection:"):
            hub1_name = line.split("-")[0].split()[1].strip()
            print(f"hub1_name: {hub1_name}")
            hub2_name = line.split("-")[1].strip()
            print(f"hub2_name: {hub2_name}")
