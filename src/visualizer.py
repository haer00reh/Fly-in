import pygame
import pygame.gfxdraw
from pathlib import Path

from config_maker import Config

pygame.init()

WIDTH, HEIGHT = 1000, 700
DEFAULT_HUB_RADIUS = 22
MIN_SCALE = 40
MAX_SCALE = 260
ZOOM_STEP = 1.12
SMOOTHING = 0.12
CAMERA_SPEED = 18

DEFAULT_ZONE_COLOR = {
    "normal": (90, 160, 255),
    "blocked": (90, 90, 90),
    "restricted": (220, 70, 70),
    "priority": (80, 210, 110),
}

NAMED_COLORS = {
    "red": (220, 50, 50), "blue": (60, 120, 220), "green": (60, 200, 100),
    "yellow": (230, 210, 60), "orange": (240, 140, 40), "purple": (160, 80, 200),
    "gray": (130, 130, 130), "cyan": (80, 220, 220), "magenta": (220, 80, 200),
    "brown": (150, 100, 60), "lime": (170, 230, 60), "gold": (230, 190, 60),
}

BACKGROUND_COLOR = (18, 24, 38)
CONNECTION_COLOR = (120, 140, 180)
HUB_BORDER_COLOR = (240, 240, 245)
TEXT_COLOR = (245, 245, 245)
OCCUPANCY_BG = (30, 32, 38)
OCCUPANCY_TEXT = (240, 240, 240)


def calculate_view_params(config) -> tuple[int, int, int, int]:
    all_hubs = [config.start, config.end] + config.hubs
    xs = [h.x for h in all_hubs]
    ys = [h.y for h in all_hubs]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    width_needed = max(max_x - min_x, 1)
    height_needed = max(max_y - min_y, 1)

    padding = 80
    scale_x = (WIDTH - 2 * padding) / width_needed
    scale_y = (HEIGHT - 2 * padding) / height_needed
    scale = int(max(min(scale_x, scale_y), MIN_SCALE))

    total_width = width_needed * scale
    total_height = height_needed * scale
    margin_x = int((WIDTH - total_width) / 2 - min_x * scale)
    margin_y = int((HEIGHT - total_height) / 2 - min_y * scale)

    return scale, margin_x, margin_y, width_needed


def get_hub_color(h) -> tuple[int, int, int]:
    if h.color and h.color in NAMED_COLORS:
        return NAMED_COLORS[h.color]
    return DEFAULT_ZONE_COLOR.get(h.zone_type or "normal", (200, 200, 200))


def render_text(screen, font, text, pos, color=TEXT_COLOR, shadow=True):
    if shadow:
        shadow_surf = font.render(text, True, (12, 16, 22))
        screen.blit(shadow_surf, (pos[0] + 1, pos[1] + 1))
    screen.blit(font.render(text, True, color), pos)


class DroneIcon:
    def __init__(self, id: int, start_pos: tuple[float, float], drone_img):
        self.id = id
        self.pos = list(start_pos)
        self.target = list(start_pos)
        self.drone_img = drone_img
        self.current_hub_name = None

    def set_target(self, pos: tuple[float, float]) -> None:
        self.target = list(pos)

    def update(self, speed: float = 0.12) -> None:
        dx = self.target[0] - self.pos[0]
        dy = self.target[1] - self.pos[1]
        dist = (dx**2 + dy**2) ** 0.5
        if dist > speed:
            self.pos[0] += dx / dist * speed
            self.pos[1] += dy / dist * speed
        else:
            self.pos[0], self.pos[1] = self.target

    def draw(self, screen, world_to_screen) -> None:
        screen_pos = world_to_screen(self.pos[0], self.pos[1])
        rect = self.drone_img.get_rect(center=screen_pos)
        screen.blit(self.drone_img, rect)
        label = pygame.font.Font(None, 20).render("", True, (255, 255, 255))
        screen.blit(label, (rect.centerx - label.get_width() // 2, rect.top - 20))


class MapVisualizer:
    def __init__(self, config: Config):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Fly-in Drone Simulator")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 22)
        self.hud_font = pygame.font.Font(None, 24)

        base_scale, margin_x, margin_y, _ = calculate_view_params(config)
        self.scale = base_scale
        self.target_scale = base_scale
        self.camera_x = margin_x
        self.camera_y = margin_y
        self.target_camera_x = margin_x
        self.target_camera_y = margin_y

        asset_dir = Path(__file__).resolve().parent / "assets"
        drone_path = asset_dir / "Drone.png"
        if drone_path.exists():
            self.drone_img = pygame.image.load(drone_path).convert_alpha()
        else:
            self.drone_img = pygame.Surface((44, 44), pygame.SRCALPHA)
            pygame.gfxdraw.filled_circle(self.drone_img, 22, 22, 22, (90, 190, 255))
            pygame.gfxdraw.aacircle(self.drone_img, 22, 22, 22, (255, 255, 255))
        self.drone_img = pygame.transform.smoothscale(self.drone_img, (44, 44))

        background_path = asset_dir / "Background.png"
        if background_path.exists():
            self.background_img = pygame.image.load(background_path).convert()
            self.background_img = pygame.transform.smoothscale(self.background_img, (WIDTH, HEIGHT))
        else:
            self.background_img = None

    def screen_to_world(self, screen_x: int, screen_y: int) -> tuple[float, float]:
        return ((screen_x - self.camera_x) / self.scale, (screen_y - self.camera_y) / self.scale)

    def world_to_screen(self, world_x: float, world_y: float) -> tuple[int, int]:
        return (int(self.camera_x + world_x * self.scale), int(self.camera_y + world_y * self.scale))

    def get_all_hubs(self, config) -> dict[str, object]:
        hubs = {config.start.name: config.start, config.end.name: config.end}
        for h in config.hubs:
            hubs[h.name] = h
        return hubs

    def clamp_zoom(self, new_scale: float) -> float:
        return max(MIN_SCALE, min(MAX_SCALE, new_scale))

    def update_camera(self) -> None:
        self.scale += (self.target_scale - self.scale) * SMOOTHING
        self.camera_x += (self.target_camera_x - self.camera_x) * SMOOTHING
        self.camera_y += (self.target_camera_y - self.camera_y) * SMOOTHING

    def draw_hud(self, turns_left: int) -> None:
        hud = pygame.Surface((WIDTH, 38), pygame.SRCALPHA)
        hud.fill((14, 20, 30, 220))
        self.screen.blit(hud, (0, 0))
        render_text(self.screen, self.hud_font, f"Turns left: {turns_left}", (18, 8), color=TEXT_COLOR)

    def draw_static_map(self, config, all_hubs, hub_occupancy) -> None:
        self.screen.fill(BACKGROUND_COLOR)

        for conn in config.connections:
            p1 = self.world_to_screen(conn.hub1.x, conn.hub1.y)
            p2 = self.world_to_screen(conn.hub2.x, conn.hub2.y)
            pygame.draw.line(self.screen, CONNECTION_COLOR, p1, p2, 4)

        for h in all_hubs.values():
            pos = self.world_to_screen(h.x, h.y)
            hub_color = get_hub_color(h)
            shadow_pos = (pos[0] + 3, pos[1] + 3)
            pygame.gfxdraw.filled_circle(self.screen, shadow_pos[0], shadow_pos[1], DEFAULT_HUB_RADIUS + 6, (10, 14, 24))
            pygame.gfxdraw.filled_circle(self.screen, pos[0], pos[1], DEFAULT_HUB_RADIUS + 4, (18, 24, 38))
            pygame.gfxdraw.filled_circle(self.screen, pos[0], pos[1], DEFAULT_HUB_RADIUS + 1, hub_color)
            pygame.gfxdraw.aacircle(self.screen, pos[0], pos[1], DEFAULT_HUB_RADIUS + 1, HUB_BORDER_COLOR)
            pygame.gfxdraw.aacircle(self.screen, pos[0], pos[1], DEFAULT_HUB_RADIUS, (255, 255, 255))

            occupancy = hub_occupancy.get(h.name, 0)
            if h.name not in {config.start.name, config.end.name}:
                capacity = h.max_drones or 1
                badge_width = max(34, self.font.size(f"{occupancy}/{capacity}")[0] + 10)
                badge_rect = pygame.Rect(0, 0, badge_width, 22)
                badge_rect.center = (pos[0], pos[1] + DEFAULT_HUB_RADIUS + 16)
                pygame.draw.rect(self.screen, OCCUPANCY_BG, badge_rect, border_radius=10)
                pygame.draw.rect(self.screen, HUB_BORDER_COLOR, badge_rect, width=1, border_radius=10)
                render_text(self.screen, self.font, f"{occupancy}/{capacity}", (badge_rect.x + 8, badge_rect.y + 2), color=OCCUPANCY_TEXT, shadow=False)

    def process_turn_targets(self, sim_output, turn_index, all_hubs, drones, hub_occupancy) -> None:
        if turn_index >= len(sim_output):
            return
        for drone_id, target_name in sim_output[turn_index]:
            next_hub_name = target_name.split("-")[-1]
            target_hub = all_hubs.get(next_hub_name)
            if target_hub is None:
                continue
            drones[drone_id].set_target((target_hub.x, target_hub.y))
            drones[drone_id].next_hub_name = next_hub_name

    def run_visualizer(self, config: Config, sim_output: list[tuple]) -> None:
        all_hubs = self.get_all_hubs(config)
        start_world = (config.start.x, config.start.y)
        drones = {}
        hub_occupancy = {name: 0 for name in all_hubs}

        for d in config.drones:
            drones[d.id] = DroneIcon(d.id, start_world, self.drone_img)
            drones[d.id].current_hub_name = config.start.name
            drones[d.id].next_hub_name = config.start.name
            hub_occupancy[config.start.name] += 1

        turn_index = 0
        frame_in_turn = 0
        total_turns = len(sim_output)
        turns_left = total_turns

        self.target_camera_x = self.camera_x
        self.target_camera_y = self.camera_y

        running = True
        while running:
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
                    new_scale = self.clamp_zoom(self.target_scale * (ZOOM_STEP if event.y > 0 else 1 / ZOOM_STEP))
                    self.target_scale = new_scale
                    self.target_camera_x = mouse_x - world_at_mouse[0] * self.target_scale
                    self.target_camera_y = mouse_y - world_at_mouse[1] * self.target_scale

            if frame_in_turn == 0 and turn_index < total_turns:
                self.process_turn_targets(sim_output, turn_index, all_hubs, drones, hub_occupancy)

            for drone in drones.values():
                old_pos = tuple(int(v) for v in drone.pos)
                drone.update()
                if drone.pos == drone.target and drone.current_hub_name != getattr(drone, "next_hub_name", drone.current_hub_name):
                    old_hub = drone.current_hub_name
                    new_hub = drone.next_hub_name
                    if old_hub:
                        hub_occupancy[old_hub] = max(0, hub_occupancy.get(old_hub, 1) - 1)
                    hub_occupancy[new_hub] = hub_occupancy.get(new_hub, 0) + 1
                    drone.current_hub_name = new_hub

            self.update_camera()
            self.draw_static_map(config, all_hubs, hub_occupancy)
            for drone in drones.values():
                drone.draw(self.screen, self.world_to_screen)
            self.draw_hud(max(total_turns - turn_index, 0))
            pygame.display.flip()

            frame_in_turn += 1
            if frame_in_turn >= 60:
                frame_in_turn = 0
                if turn_index < total_turns:
                    turn_index += 1

            self.clock.tick(60)

        pygame.quit()
