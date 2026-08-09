"""Configuration parsing and validation helpers for the simulator."""

import sys

from pydantic import BaseModel
from .objects import drone, end_hub, hub, start_hub, connection


class Config(BaseModel):
    """Holds the parsed simulator configuration and helpers."""

    drones: list[drone] = []
    start: start_hub = start_hub()
    end: end_hub = end_hub()
    hubs: list[hub] = []
    connections: list[connection] = []

    def error_teller(self, additional_message: str, line_nb: int) -> None:
        """Report a configuration error and exit."""
        if line_nb > 0:
            print(
                f"WATCH OUT!!\nError on line {line_nb}: {additional_message}",
                file=sys.stderr,
            )
        else:
            print(f"WATCH OUT!!\nError: {additional_message}", file=sys.stderr)
        sys.exit(1)

    def if_disconnected_graph(self) -> None:
        """Ensure the graph remains connected after parsing."""
        visited = set()

        def dfs(hub_name: hub) -> None:
            if hub_name.name in visited:
                return
            visited.add(hub_name.name)
            for connection_item in self.connections:
                if (
                    connection_item.hub1 is not None
                    and connection_item.hub2 is not None
                    and connection_item.hub1.name == hub_name.name
                    and connection_item.hub2.zone_type != "blocked"
                ):
                    dfs(connection_item.hub2)
                elif (
                    connection_item.hub1 is not None
                    and connection_item.hub2 is not None
                    and connection_item.hub2.name == hub_name.name
                    and connection_item.hub1.zone_type != "blocked"
                ):
                    dfs(connection_item.hub1)

        dfs(self.start)
        for hub_name in self.hubs + [self.end]:
            if hub_name.name not in visited:
                if hub_name.line_nb is not None:
                    line_nb = hub_name.line_nb
                else:
                    line_nb = 0
                self.error_teller(
                    (
                        "hub '"
                        f"{hub_name.name}' causing disconnection in the graph"
                    ),
                    line_nb,
                )

    def init(self, config_table: dict[int, str]) -> None:
        """Initialize the configuration from the parsed config table."""
        for key, line in config_table.items():
            self.search_line(line, key)
        for hub_name in self.hubs:
            hub_name.init_metadata()
        for connection_name in self.connections:
            connection_name.init_metadata()
        self.start.init_metadata()
        self.end.init_metadata()
        self.if_disconnected_graph()

    def duplicate_connections(self, line_nb: int) -> None:
        """Ensure no connection is duplicated in the config."""
        for i in range(len(self.connections)):
            for j in range(i + 1, len(self.connections)):
                left_one = self.connections[i].hub1
                right_one = self.connections[i].hub2
                left_two = self.connections[j].hub1
                right_two = self.connections[j].hub2
                if (
                    left_one is not None
                    and right_one is not None
                    and left_two is not None
                    and right_two is not None
                    and left_one.name == left_two.name
                    and right_one.name == right_two.name
                ) or (
                    left_one is not None
                    and right_one is not None
                    and left_two is not None
                    and right_two is not None
                    and left_one.name == right_two.name
                    and right_one.name == left_two.name
                ):
                    self.error_teller(
                        (
                            "duplicate connection "
                            f"'{left_one.name}-{right_one.name}'"
                        ),
                        line_nb,
                    )

    def duplicate_hubs(self, line_nb: int) -> None:
        """Ensure no hub is duplicated in the config."""
        for i in range(len(self.hubs)):
            for j in range(i + 1, len(self.hubs)):
                if self.hubs[i].name == self.hubs[j].name:
                    self.error_teller(
                        f"duplicate hub '{self.hubs[i].name}'",
                        line_nb,
                    )

    def hub_exists(self, hub_name: str, line_nb: int) -> bool:
        """Check whether a hub exists in the config."""
        for hub_name_item in self.hubs:
            if hub_name_item.name == hub_name:
                return True
        if self.start.name == hub_name or self.end.name == hub_name:
            return True
        self.error_teller(f"hub '{hub_name}' does not exist", line_nb)
        return False

    def valid_name(self, name: str, line_nb: int) -> None:
        """Ensure the given hub name is valid."""
        if "-" in name:
            self.error_teller(f"invalid name '{name}'", line_nb)

    def search_for_hub(self, hub_name: str) -> hub | None:
        """Find a hub by its name in the config."""
        for hub_name_item in self.hubs:
            if hub_name_item.name == hub_name:
                return hub_name_item
        if self.start.name == hub_name:
            return self.start
        if self.end.name == hub_name:
            return self.end
        return None

    def assign_drone_attributes(self, path: list[hub]) -> None:
        """Assign the path and state fields for all drones."""
        for drone_item in self.drones:
            drone_item.path = list(path)
            drone_item.current_hub = self.start
            drone_item.path_index = 0
            drone_item.finished = False
            drone_item.in_queue = False
            drone_item.transit_turns_left = 0
            drone_item.transit_target = None

    def search_line(self, line: str, line_nb: int) -> None:
        """Parse a single line from the config table."""
        if line.startswith("nb_drones:"):
            nb_drones = int(line.split(":")[1].strip())
            if nb_drones <= 0:
                self.error_teller(
                    f"invalid number of drones '{nb_drones}'",
                    line_nb,
                )
            for i in range(nb_drones):
                self.drones.append(drone(id=i + 1))
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
                self.error_teller(
                    f"invalid coordinates for hub '{hub_name}'",
                    line_nb,
                )
                return
            hub_meta_data = " ".join(line.split()[4:])
            self.hubs.append(
                hub(
                    name=hub_name,
                    x=hub_x,
                    y=hub_y,
                    meta_data_as_text=hub_meta_data,
                    line_nb=line_nb,
                )
            )
            self.duplicate_hubs(line_nb)
        elif line.startswith("connection:"):
            hub1_name = line.split("-")[0].split()[1].strip()
            hub2_name = line.split("-")[1].split()[0].strip()
            meta_data = ""
            if len(line.split('[')) == 2:
                meta_data = line.split('[')[1].split(']')[0].strip()
            if hub1_name == hub2_name:
                self.error_teller(
                    f"invalid connection '{hub1_name}-{hub2_name}'",
                    line_nb,
                )
            self.hub_exists(hub1_name, line_nb)
            self.hub_exists(hub2_name, line_nb)
            self.connections.append(
                connection(
                    hub1=self.search_for_hub(hub1_name),
                    hub2=self.search_for_hub(hub2_name),
                    meta_data_as_text=meta_data,
                    line_nb=line_nb,
                )
            )
            self.duplicate_connections(line_nb)
