from pydantic import BaseModel
from .parser_helpers import hub_parser, link_parser
import sys


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
    max_link_capacity: int = 1
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
