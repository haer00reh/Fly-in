from tkinter import font

from config_maker import Config, hub, connection, start_hub, end_hub, drone
from parser import Parser
from pathlib import Path
import pygame
from pydantic import BaseModel

pygame.init()
WIDTH, HEIGHT = 1000, 700
MARGIN = 80
SCALE = 60

DEFAULT_ZONE_COLOR = {
    "normal": (100, 150, 255),
    "blocked": (80, 80, 80),
    "restricted": (220, 60, 60),
    "priority": (60, 200, 100),
}

NAMED_COLORS = {
    "red": (220, 50, 50), "blue": (60, 120, 220), "green": (60, 200, 100),
    "yellow": (230, 210, 60), "orange": (240, 140, 40), "purple": (160, 80, 200),
    "gray": (130, 130, 130), "cyan": (80, 220, 220), "magenta": (220, 80, 200),
    "brown": (150, 100, 60), "lime": (170, 230, 60), "gold": (230, 190, 60),
}

def get_hub_color(h) -> tuple[int, int, int]:
    if h.color and h.color in NAMED_COLORS:
        return NAMED_COLORS[h.color]
    return DEFAULT_ZONE_COLOR.get(h.zone_type or "normal", (200, 200, 200))

class DroneIcon:
    def __init__(self, id: int, start_pos: tuple[int, int]):
        self.id = id
        self.pos = list(start_pos)
        self.target = list(start_pos)
        self.drone_img = pygame.image.load("assets/drone.png").convert_alpha()
        self.drone_img = pygame.transform.smoothscale(self.drone_img, (24, 24))

        self.background_img = pygame.image.load("assets/background.png").convert()
        self.background_img = pygame.transform.smoothscale(self.background_img, (WIDTH, HEIGHT))

        self.font = pygame.font.Font(None, 24)

    def set_target(self, pos: tuple[int, int]) -> None:
        self.target = list(pos)

    def update(self, speed: float = 6.0) -> None:
        dx = self.target[0] - self.pos[0]
        dy = self.target[1] - self.pos[1]
        dist = (dx**2 + dy**2) ** 0.5
        if dist > speed:
            self.pos[0] += dx / dist * speed
            self.pos[1] += dy / dist * speed
        else:
            self.pos[0], self.pos[1] = self.target

    def draw(self, screen) -> None:
        rect = self.drone_img.get_rect(center=(int(self.pos[0]), int(self.pos[1])))
        screen.blit(self.drone_img, rect)
        label = self.font.render(f"D{self.id}", True, (255, 255, 255))
        screen.blit(label, (self.pos[0] - 8, self.pos[1] - 26))

class map_visualizer(BaseModel):
    config: Config | None = None

    def run_visualizer(self, config, sim_output: list[tuple]):
        all_hubs = self.get_all_hubs(config)
        start_pos = self.to_screen(config.start.x, config.start.y)

        drones = {d.id: DroneIcon(d.id, start_pos) for d in config.drones}

        turn_index = 0
        clock = pygame.time.Clock()
        frame_in_turn = 0
        FRAMES_PER_TURN = 45

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            if frame_in_turn == 0 and turn_index < len(sim_output):
                for drone_id, target_name in sim_output[turn_index]:
                    target_hub = all_hubs[target_name]
                    self.drones[drone_id].set_target(self.to_screen(target_hub.x, target_hub.y))

            for drone in self.drones.values():
                drone.update()

            self.draw_static_map(config, all_hubs)
            for drone in self.drones.values():
                drone.draw(self.screen)
            pygame.display.flip()

            frame_in_turn += 1
            if frame_in_turn >= FRAMES_PER_TURN:
                frame_in_turn = 0
                turn_index += 1

            clock.tick(60)

        pygame.quit()

    def to_screen(self, x: int, y: int) -> tuple[int, int]:
        return (self.MARGIN + x * self.SCALE, self.MARGIN + y * self.SCALE)

    def get_all_hubs(self, config) -> dict[str, object]:
        hubs = {config.start.name: config.start, config.end.name: config.end}
        for h in config.hubs:
            hubs[h.name] = h
        return hubs

    def draw_static_map(self, config, all_hubs) -> None:
        self.screen.blit(self.background_img, (0, 0))

        for conn in config.connections:
            p1 = self.to_screen(conn.hub1.x, conn.hub1.y)
            p2 = self.to_screen(conn.hub2.x, conn.hub2.y)
            pygame.draw.line(self.screen, (120, 120, 120), p1, p2, 2)

        for h in all_hubs.values():
            pos = self.to_screen(h.x, h.y)
            if h.name == config.start.name:
                color = (0, 220, 0)
            elif h.name == config.end.name:
                color = (255, 215, 0)
            else:
                color = self.ZONE_COLORS.get(h.zone_type or "normal", (200, 200, 200))
            pygame.draw.circle(self.screen, color, pos, 16)
            label = self.font.render(h.name, True, (255, 255, 255))
            self.screen.blit(label, (pos[0] - label.get_width() // 2, pos[1] - 28))