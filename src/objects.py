from pydantic import BaseModel
from .parser_helpers import hub_parser, link_parser
import sys
import pygame
from typing import Callable


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


class DroneIcon:
    """Represents an animated drone icon in the visualizer."""

    def __init__(
        self,
        id: int,
        start_pos: tuple[float, float],
        drone_img: pygame.Surface,
    ):
        """Initialize the drone icon state."""
        self.id = id
        self.pos = list(start_pos)
        self.target = list(start_pos)
        self.start_pos = list(start_pos)
        self.progress = 1.0
        self.drone_img = drone_img
        self.current_hub_name: str | None = None
        self.next_hub_name: str | None = None

    def set_target(self, pos: tuple[float, float]) -> None:
        """Set the drone icon's movement target."""
        self.start_pos = list(self.pos)
        self.target = list(pos)
        self.progress = 0.0

    def update(self, step: float = 1 / 60) -> None:
        """Move the drone icon toward its target over one turn."""
        if self.progress >= 1.0:
            self.pos[0], self.pos[1] = self.target
            return
        self.progress = min(1.0, self.progress + step)
        self.pos[0] = self.start_pos[0] + (
            self.target[0] - self.start_pos[0]
        ) * self.progress
        self.pos[1] = self.start_pos[1] + (
            self.target[1] - self.start_pos[1]
        ) * self.progress

    def draw(
        self,
        screen: pygame.Surface,
        world_to_screen: Callable[[float, float], tuple[int, int]],
    ) -> None:
        """Draw the drone icon to the screen."""
        screen_pos = world_to_screen(self.pos[0], self.pos[1])
        rect = self.drone_img.get_rect(center=screen_pos)
        screen.blit(self.drone_img, rect)
        label = pygame.font.Font(None, 20).render(
            "",
            True,
            (255, 255, 255),
        )
        screen.blit(
            label,
            (rect.centerx - label.get_width() // 2, rect.top - 20),
        )
