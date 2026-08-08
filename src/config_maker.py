"""Configuration parsing and validation helpers for the simulator."""

import sys

from pydantic import BaseModel


class hub(BaseModel):
    """Represents a single hub in the simulation."""

    name: str | None = None
    x: int | None = None
    y: int | None = None
    meta_data_as_text: str | None = None
    color: str | None = None
    max_drones: int = 1
    zone_type: str | None = None
    line_nb: int | None = None

    def init_metadata(self) -> None:
        """Initialize the hub metadata from the parsed text."""
        try:
            if self.meta_data_as_text:
                color_value, max_drones_value, zone_value = hub_parser(
                    self.meta_data_as_text,
                    self.line_nb,
                )
                self.color = color_value
                self.max_drones = (
                    max_drones_value if max_drones_value is not None else 1
                )
                self.zone_type = zone_value
        except ValueError:
            pass


class connection(BaseModel):
    """Represents a connection between two hubs."""

    hub1: hub | None = None
    hub2: hub | None = None
    occupied: bool = False
    meta_data_as_text: str | None = None
    max_link_capacity: int | None = None
    line_nb: int | None = None

    def init_metadata(self) -> None:
        """Initialize the connection metadata from the parsed text."""
        self.max_link_capacity = link_parser(
            self.meta_data_as_text,
            self.line_nb,
        )


class end_hub(hub):
    """Represents the end hub in the simulation."""

    def init_metadata(self) -> None:
        """Initialize the end hub metadata."""
        color_value, _max_drones_value, zone_value = hub_parser(
            self.meta_data_as_text,
            self.line_nb,
        )
        self.color = color_value
        self.max_drones = sys.maxsize
        self.zone_type = zone_value if zone_value is not None else "normal"


class start_hub(hub):
    """Represents the start hub in the simulation."""

    def init_metadata(self) -> None:
        """Initialize the start hub metadata."""
        color_value, _max_drones_value, zone_value = hub_parser(
            self.meta_data_as_text,
            self.line_nb,
        )
        self.color = color_value
        self.max_drones = sys.maxsize
        self.zone_type = zone_value if zone_value is not None else "normal"


class drone(BaseModel):
    """Represents a drone in the simulation."""

    id: int | None = None
    finished: bool = False
    in_queue: bool = False
    current_hub: hub | None = None
    zone_occupancy: dict[str, int] | None = None
    connection_occupancy: dict[str, int] | None = None
    transit_turns_left: int = 0
    transit_target: hub | None = None
    transit_conn_key: str | None = None
    path: list[hub] = []
    path_index: int = 0


def link_parser(line: str | None, line_nb: int | None) -> int | None:
    """Parse and validate the link capacity metadata."""
    if line is None or line_nb is None:
        return None
    if "max_link_capacity" in line:
        max_link_capacity = line.split("max_link_capacity=")[1].split()[0]
        try:
            if int(max_link_capacity) < 0:
                print(
                    (
                        "WATCH OUT!!\n"
                        f"Error in line {line_nb}: invalid "
                        f"max_link_capacity '{max_link_capacity}'"
                    ),
                    file=sys.stderr,
                )
                sys.exit(1)
        except ValueError:
            print(
                (
                    "WATCH OUT!!\n"
                    f"Error in line {line_nb}: invalid "
                    f"max_link_capacity '{max_link_capacity}'"
                ),
                file=sys.stderr,
            )
            sys.exit(1)
        return int(max_link_capacity)
    return None


def hub_parser(
    line: str | None,
    line_nb: int | None,
) -> tuple[str | None, int | None, str | None]:
    """Parse and validate hub metadata from a config line."""
    if line is None or line_nb is None:
        return (None, None, None)

    color_value: str | None = None
    max_drones_value: int | None = None
    zone_value: str | None = None
    meta_prefixes = ("color=", "max_drones=", "zone=")
    zone_prefixes = ("normal", "restricted", "blocked", "priority")
    if "color=" in line:
        color = line.split("color=")[1].split()[0]
        color_value = color.replace(']', '')
    if "max_drones=" in line:
        max_drones = line.split("max_drones=")[1].split()[0].split("]")[0]
        if int(max_drones) <= 0:
            print(
                (
                    "WATCH OUT!!\n"
                    f"Error in line {line_nb}: invalid "
                    f"max_drones '{max_drones}'"
                ),
                file=sys.stderr,
            )
            sys.exit(1)
        max_drones_value = int(max_drones)
    if "zone=" in line:
        zone_type = line.split("zone=")[1].split()[0].split("]")[0]
        if zone_type not in zone_prefixes:
            print(
                (
                    "WATCH OUT!!\n"
                    f"Error in line {line_nb}: invalid zone type "
                    f"'{zone_type}'"
                ),
                file=sys.stderr,
            )
            sys.exit(1)
        zone_value = zone_type
    elif not any(prefix in line for prefix in meta_prefixes):
        print(
            (
                "WATCH OUT!!\n"
                f"Error in line {line_nb}: invalid meta data '{line}'"
            ),
            file=sys.stderr,
        )
        sys.exit(1)
    return (color_value, max_drones_value, zone_value)


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
            drone_item.path = path
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
