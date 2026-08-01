from pydantic import BaseModel
import sys

class hub(BaseModel):
    name: str | None = None
    x: int | None = None
    y: int | None = None
    meta_data_as_text: str | None = None
    color: str | None = None
    max_drones: int = 1
    zone_type: str | None = None
    line_nb: int | None = None

    def init_metadata(self):
        try:
            if self.meta_data_as_text:
                self.color, self.max_drones, self.zone_type = hub_parser(self.meta_data_as_text, self.line_nb)
        except ValueError:
            pass



class connection(BaseModel):
    hub1: hub | None = None
    hub2: hub | None = None
    link_cap: int | None = None
    meta_data_as_text: str | None = None
    max_link_capacity: int | None = None
    line_nb: int | None = None

    def init_metadata(self):
        self.max_link_capacity = link_parser(self.meta_data_as_text, self.line_nb)



class end_hub(hub):
    pass


class start_hub(hub):
    pass


class drone(BaseModel):
    id: int | None = None
    start_hub: hub | None = None
    end_hub: hub | None = None


def link_parser(line: str, line_nb: int):
    if "max_link_capacity" in line:
        max_link_capacity = line.split("max_link_capacity=")[1].split()[0]
        try:
            if int(max_link_capacity) < 0:
                print(f"WATCH OUT!!\nError in line {line_nb}: invalid max_link_capacity '{max_link_capacity}'", file=sys.stderr)
                sys.exit(1)
        except ValueError:
            print(f"WATCH OUT!!\nError in line {line_nb}: invalid max_link_capacity '{max_link_capacity}'", file=sys.stderr)
            sys.exit(1)
        return int(max_link_capacity)

def hub_parser(line: str, line_nb: int):
    package = []
    meta_prefixes = ("color=", "max_drones=", "zone=")
    zone_prefixes = ("normal", "restricter", "blocked", "priority")
    if "color=" in line:
        color = line.split("color=")[1].split()[0]
        package.append(color)
    elif not "color=" in line:
        package.append(None)
    if "max_drones=" in line:
        max_drones = line.split("max_drones=")[1].split()[0].split("]")[0]
        if int(max_drones) <= 0:
            print(f"WATCH OUT!!\nError in line {line_nb}: invalid max_drones '{max_drones}'", file=sys.stderr)
            sys.exit(1)
        package.append(int(max_drones))
    elif not "max_drones=" in line:
        package.append(None)
    if "zone=" in line:
        zone_type = line.split("zone=")[1].split()[0].split("]")[0]
        if zone_type not in zone_prefixes:
            print(f"WATCH OUT!!\nError in line {line_nb}: invalid zone type '{zone_type}'", file=sys.stderr)
            sys.exit(1)
        package.append(zone_type)
    elif not "zone=" in line:
        package.append(None)
    elif not any(prefix in line for prefix in meta_prefixes):
        print(f"WATCH OUT!!\nError in line {line_nb}: invalid meta data '{line}'", file=sys.stderr)
        sys.exit(1)
    return tuple(package)

class Config(BaseModel):
    drones: list[drone] = []
    start: start_hub = start_hub()
    end: end_hub = end_hub()
    hubs: list[hub] = []
    connections: list[connection] = []

    def error_teller(self, additional_message: str, line_nb: int) -> None:
        if line_nb > 0:
            print(f"WATCH OUT!!\nError on line {line_nb}: {additional_message}", file=sys.stderr)
        else:
            print(f"WATCH OUT!!\nError: {additional_message}", file=sys.stderr)
        sys.exit(1)



    def if_disconnected_graph(self) -> bool:
        visited = set()
        def dfs(hub):
            if hub.name in visited:
                return
            visited.add(hub.name)
            for connection in self.connections:
                if connection.hub1.name == hub.name and connection.hub2.zone_type != "blocked":
                    dfs(connection.hub2)
                elif connection.hub2.name == hub.name and connection.hub1.zone_type != "blocked":
                    dfs(connection.hub1)

        dfs(self.start)
        for hub in self.hubs + [self.end]:
            if hub.name not in visited:
                self.error_teller(f"hub '{hub.name}' causing disconnection in the graph", hub.line_nb)

    def init(self, config_table: dict[int, str]) -> bool:
        for key, line in config_table.items():
            self.search_line(line, key)
        for hub in self.hubs:
            hub.init_metadata()
        for connection in self.connections:
            connection.init_metadata()
        self.if_disconnected_graph()

    def duplicate_connections(self, line_nb: int) -> bool:
        for i in range(len(self.connections)):
            for j in range(i+1, len(self.connections)):
                if (self.connections[i].hub1.name == self.connections[j].hub1.name and
                    self.connections[i].hub2.name == self.connections[j].hub2.name) or \
                   (self.connections[i].hub1.name == self.connections[j].hub2.name and
                    self.connections[i].hub2.name == self.connections[j].hub1.name):
                    self.error_teller(f"duplicate connection '{self.connections[i].hub1.name}-{self.connections[i].hub2.name}'", line_nb)

    def duplicate_hubs(self, line_nb: int) -> bool:
        for i in range(len(self.hubs)):
            for j in range(i+1, len(self.hubs)):
                if self.hubs[i].name == self.hubs[j].name:
                    self.error_teller(f"duplicate hub '{self.hubs[i].name}'", line_nb)

    def hub_exists(self, hub_name: str, line_nb: int) -> bool:
        for hub in self.hubs:
            if hub.name == hub_name:
                return True
        if self.start.name == hub_name or self.end.name == hub_name:
            return True
        self.error_teller(f"hub '{hub_name}' does not exist", line_nb)

    def valid_name(self, name: str, line_nb: int) -> bool:
        if '-' in name:
            self.error_teller(f"invalid name '{name}'", line_nb)

    def search_for_hub(self, hub_name: str) -> hub | None:
        for hub in self.hubs:
            if hub.name == hub_name:
                return hub
        if self.start.name == hub_name:
            return self.start
        if self.end.name == hub_name:
            return self.end
        return None

    def search_line(self, line: str, line_nb: int) -> bool:
        if line.startswith("nb_drones:"):
            nb_drones = int(line.split(":")[1].strip())
            if nb_drones <= 0:
                self.error_teller(f"invalid number of drones '{nb_drones}'", line_nb)
            for i in range(nb_drones):
                self.drones.append(drone(id=i+1, start_hub=self.start, end_hub=self.end))
        elif line.startswith("start_hub:"):
            self.start.name = line.split()[1].strip()
            self.valid_name(self.start.name, line_nb)
            self.start.x = int(line.split()[2].strip())
            self.start.y = int(line.split()[3].strip())
            self.start.line_nb = line_nb
            if len(line.split()) == 5:
                self.start.meta_data_as_text = line.split()[4].strip()
            else:
                self.start.meta_data_as_text = None
        elif line.startswith("end_hub:"):
            self.end.name = line.split()[1].strip()
            self.valid_name(self.end.name, line_nb)
            self.end.x = int(line.split()[2].strip())
            self.end.y = int(line.split()[3].strip())
            self.end.line_nb = line_nb
            if len(line.split()) == 5:
                self.end.meta_data_as_text = line.split()[4].strip()
            else:
                self.end.meta_data_as_text = None
        elif line.startswith("hub:"):
            hub_name = line.split()[1].strip()
            self.valid_name(hub_name, line_nb)
            try:
                hub_x = int(line.split()[2].strip())
                hub_y = int(line.split()[3].strip())
            except ValueError:
                self.error_teller(f"invalid coordinates for hub '{hub_name}'", line_nb)
            hub_meta_data = " ".join(line.split()[4:])
            self.hubs.append(hub(name=hub_name, x=hub_x, y=hub_y, meta_data_as_text=hub_meta_data, line_nb=line_nb))
            self.duplicate_hubs(line_nb)
        elif line.startswith("connection:"):
            hub1_name = line.split("-")[0].split()[1].strip()
            hub2_name = line.split("-")[1].split()[0].strip()
            meta_data = ""
            if len(line.split('[')) == 2:
                meta_data = line.split('[')[1].split(']')[0].strip()
            if hub1_name == hub2_name:
                self.error_teller(f"invalid connection '{hub1_name}-{hub2_name}'", line_nb)
            self.hub_exists(hub1_name, line_nb)
            self.hub_exists(hub2_name, line_nb)
            self.connections.append(connection(hub1=self.search_for_hub(hub1_name), hub2=self.search_for_hub(hub2_name), meta_data_as_text=meta_data, line_nb=line_nb))
            self.duplicate_connections(line_nb)
