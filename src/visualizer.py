"""Visualization helpers for rendering the drone simulation."""

from pathlib import Path
from typing import Any
import sys
import pygame
import pygame.gfxdraw

from .config_maker import Config, hub
from .vis_utils import BACKGROUND_COLOR, CAMERA_SPEED
from .vis_utils import CONNECTION_COLOR, DEFAULT_HUB_RADIUS, HUB_BORDER_COLOR
from .vis_utils import MAX_SCALE, OCCUPANCY_BG, OCCUPANCY_TEXT, MIN_SCALE
from .vis_utils import TEXT_COLOR, WIDTH, HEIGHT, ZOOM_STEP, render_text
from .vis_utils import SMOOTHING, calculate_view_params, get_hub_color
from .objects import DroneIcon

pygame.init()


class MapVisualizer:
    """Render the simulation map and drones in a pygame window."""

    def __init__(self, config: Config):
        """Initialize the visualizer and its assets."""
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Fly-in Drone Simulator")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 22)
        self.hud_font = pygame.font.Font(None, 24)

        base_scale, margin_x, margin_y, _ = calculate_view_params(config)
        self.scale: float = float(base_scale)
        self.target_scale: float = float(base_scale)
        self.camera_x: float = float(margin_x)
        self.camera_y: float = float(margin_y)
        self.target_camera_x: float = float(margin_x)
        self.target_camera_y: float = float(margin_y)

        asset_dir = Path(__file__).resolve().parent / "assets"
        drone_path = asset_dir / "Drone.png"
        if drone_path.exists():
            self.drone_img = pygame.image.load(drone_path).convert_alpha()
        else:
            print("drone image was not found", file=sys.stderr)
            sys.exit(1)
        self.drone_img = pygame.transform.smoothscale(self.drone_img, (44, 44))

        background_path = asset_dir / "Background.png"
        if background_path.exists():
            background_img = pygame.image.load(background_path).convert()
            background_img = pygame.transform.smoothscale(
                background_img,
                (WIDTH, HEIGHT),
            )
        else:
            background_img = None
        self.background_img: pygame.Surface | None = background_img

    def screen_to_world(
        self,
        screen_x: int,
        screen_y: int,
    ) -> tuple[float, float]:
        """Convert on-screen coordinates to world coordinates."""
        return (
            (screen_x - self.camera_x) / self.scale,
            (screen_y - self.camera_y) / self.scale,
        )

    def world_to_screen(
        self,
        world_x: float,
        world_y: float,
    ) -> tuple[int, int]:
        """Convert world coordinates to on-screen coordinates."""
        return (
            int(self.camera_x + world_x * self.scale),
            int(self.camera_y + world_y * self.scale),
        )

    def get_all_hubs(self, config: Config) -> dict[str, hub]:
        """Return all hubs in a lookup table keyed by their names."""
        hubs: dict[str, hub] = {}
        assert config.start.name is not None
        assert config.end.name is not None
        hubs[config.start.name] = config.start
        hubs[config.end.name] = config.end
        for hub_item in config.hubs:
            if hub_item.name is not None:
                hubs[hub_item.name] = hub_item
        return hubs

    def clamp_zoom(self, new_scale: float) -> Any:
        """Clamp the zoom level within the supported range."""
        return max(MIN_SCALE, min(MAX_SCALE, new_scale))

    def update_camera(self) -> None:
        """Update the camera position smoothly toward its target."""
        self.scale += (self.target_scale - self.scale) * SMOOTHING
        self.camera_x += (self.target_camera_x - self.camera_x) * SMOOTHING
        self.camera_y += (self.target_camera_y - self.camera_y) * SMOOTHING

    def draw_hud(self, turns_left: int) -> None:
        """Draw the heads-up display with the remaining turn count."""
        hud = pygame.Surface((WIDTH, 38), pygame.SRCALPHA)
        hud.fill((14, 20, 30, 220))
        self.screen.blit(hud, (0, 0))
        render_text(
            self.screen,
            self.hud_font,
            f"Turns left: {turns_left}",
            (18, 8),
            color=TEXT_COLOR,
        )

    def draw_static_map(
        self,
        config: Config,
        all_hubs: dict[str, hub],
        hub_occupancy: dict[str, int],
    ) -> None:
        """Draw the static background map and hub overlays."""
        if self.background_img is not None:
            self.screen.blit(self.background_img, (0, 0))
        else:
            self.screen.fill(BACKGROUND_COLOR)

        for conn in config.connections:
            p1 = self.world_to_screen(conn.hub1.x, conn.hub1.y)
            p2 = self.world_to_screen(conn.hub2.x, conn.hub2.y)
            pygame.draw.line(self.screen, CONNECTION_COLOR, p1, p2, 4)

        for hub_item in all_hubs.values():
            pos = self.world_to_screen(hub_item.x, hub_item.y)
            hub_color = get_hub_color(hub_item)
            pygame.gfxdraw.filled_circle(
                self.screen,
                pos[0],
                pos[1],
                DEFAULT_HUB_RADIUS + 1,
                hub_color,
            )
            pygame.gfxdraw.aacircle(
                self.screen,
                pos[0],
                pos[1],
                DEFAULT_HUB_RADIUS + 1,
                HUB_BORDER_COLOR,
            )
            pygame.gfxdraw.aacircle(
                self.screen,
                pos[0],
                pos[1],
                DEFAULT_HUB_RADIUS,
                (255, 255, 255),
            )

            assert hub_item.name is not None
            occupancy = hub_occupancy.get(hub_item.name, 0)
            if hub_item.name not in {config.start.name, config.end.name}:
                capacity = hub_item.max_drones or 1
                badge_width = max(
                    34,
                    self.font.size(f"{occupancy}/{capacity}")[0] + 10,
                )
                badge_rect = pygame.Rect(0, 0, badge_width, 22)
                badge_rect.center = (
                    pos[0],
                    pos[1] + DEFAULT_HUB_RADIUS + 16,
                )
                pygame.draw.rect(
                    self.screen,
                    OCCUPANCY_BG,
                    badge_rect,
                    border_radius=10,
                )
                pygame.draw.rect(
                    self.screen,
                    HUB_BORDER_COLOR,
                    badge_rect,
                    width=1,
                    border_radius=10,
                )
                render_text(
                    self.screen,
                    self.font,
                    f"{occupancy}/{capacity}",
                    (badge_rect.x + 8, badge_rect.y + 2),
                    color=OCCUPANCY_TEXT,
                )

    def process_turn_targets(
        self,
        sim_output: list[tuple[tuple[int, str], ...]],
        turn_index: int,
        all_hubs: dict[str, hub],
        drones: dict[int, DroneIcon],
        hub_occupancy: dict[str, int],
    ) -> None:
        """Update drone targets for the current simulation turn."""
        if turn_index >= len(sim_output):
            return
        for drone_id, target_name in sim_output[turn_index]:
            target_hub = all_hubs.get(target_name)
            if target_hub is None:
                continue
            assert target_hub.x is not None
            assert target_hub.y is not None
            drones[drone_id].set_target((float(target_hub.x),
                                         float(target_hub.y)))
            drones[drone_id].next_hub_name = target_name

    def run_visualizer(
        self,
        config: Config,
        sim_output: list[tuple[tuple[int, str], ...]],
        connection_occupancy: dict[str, int],
    ) -> None:
        """Run the main visualization loop for the simulation."""
        all_hubs = self.get_all_hubs(config)
        assert config.start.x is not None
        assert config.start.y is not None
        assert config.start.name is not None
        start_world = (float(config.start.x), float(config.start.y))
        drones: dict[int, DroneIcon] = {}
        hub_occupancy = {name: 0 for name in all_hubs}
        for drone_item in config.drones:
            assert drone_item.id is not None
            drones[drone_item.id] = DroneIcon(
                drone_item.id,
                start_world,
                self.drone_img,
            )
            drones[drone_item.id].current_hub_name = config.start.name
            drones[drone_item.id].next_hub_name = config.start.name
            hub_occupancy[config.start.name] += 1

        turn_index = 0
        frame_in_turn = 0
        total_turns = len(sim_output)

        self.target_camera_x = self.camera_x
        self.target_camera_y = self.camera_y
        running = True
        while running:
            if frame_in_turn == 0 and turn_index < total_turns:
                turn = sim_output[turn_index]
                formatted_moves = " ".join(f"D{drone_id}-{target_name}"
                                           for drone_id, target_name in turn)
                print(formatted_moves)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_a]:
                self.target_camera_x += CAMERA_SPEED
            if keys[pygame.K_d]:
                self.target_camera_x -= CAMERA_SPEED
            if keys[pygame.K_w]:
                self.target_camera_y += CAMERA_SPEED
            if keys[pygame.K_s]:
                self.target_camera_y -= CAMERA_SPEED
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEWHEEL:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    world_at_mouse = self.screen_to_world(mouse_x, mouse_y)
                    new_scale = self.clamp_zoom(
                        self.target_scale
                        * (ZOOM_STEP if event.y > 0 else 1 / ZOOM_STEP)
                    )
                    self.target_scale = new_scale
                    self.target_camera_x = (
                        mouse_x - world_at_mouse[0] * self.target_scale
                    )
                    self.target_camera_y = (
                        mouse_y - world_at_mouse[1] * self.target_scale
                    )

            if frame_in_turn == 0 and turn_index < total_turns:
                self.process_turn_targets(
                    sim_output,
                    turn_index,
                    all_hubs,
                    drones,
                    hub_occupancy,
                )

            for drone in drones.values():
                drone.update()
                if (
                    drone.pos == drone.target
                    and drone.current_hub_name
                    != getattr(drone, "next_hub_name", drone.current_hub_name)
                ):
                    old_hub = drone.current_hub_name
                    new_hub = drone.next_hub_name
                    if old_hub is not None:
                        hub_occupancy[old_hub] = max(
                            0,
                            hub_occupancy.get(old_hub, 1) - 1,
                        )
                    if new_hub is not None:
                        hub_occupancy[new_hub] = hub_occupancy.get(
                                                 new_hub, 0) + 1
                        drone.current_hub_name = new_hub

            self.update_camera()
            self.draw_static_map(config, all_hubs, hub_occupancy)
            for drone in drones.values():
                drone.draw(self.screen, self.world_to_screen)
            self.draw_hud(max(total_turns - turn_index, 0))
            pygame.display.flip()

            frame_in_turn += 1
            if frame_in_turn >= 120:
                frame_in_turn = 0
                if turn_index < total_turns:
                    turn_index += 1

            self.clock.tick(120)

        pygame.quit()
