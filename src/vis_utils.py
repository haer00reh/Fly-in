from .config_maker import Config, hub
import pygame

WIDTH, HEIGHT = 1000, 700
DEFAULT_HUB_RADIUS = 22
MIN_SCALE = 40
MAX_SCALE = 260
ZOOM_STEP = 1.12
SMOOTHING = 0.12
CAMERA_SPEED = 6

DEFAULT_ZONE_COLOR = {
    "normal": (90, 160, 255),
    "blocked": (90, 90, 90),
    "restricted": (220, 70, 70),
    "priority": (80, 210, 110),
}

NAMED_COLORS = {
    "red": (220, 50, 50),
    "blue": (60, 120, 220),
    "green": (60, 200, 100),
    "yellow": (230, 210, 60),
    "orange": (240, 140, 40),
    "purple": (160, 80, 200),
    "gray": (130, 130, 130),
    "cyan": (80, 220, 220),
    "magenta": (220, 80, 200),
    "brown": (150, 100, 60),
    "lime": (170, 230, 60),
    "gold": (230, 190, 60),
}

BACKGROUND_COLOR = (18, 24, 38)
CONNECTION_COLOR = (120, 140, 180)
HUB_BORDER_COLOR = (240, 240, 245)
TEXT_COLOR = (245, 245, 245)
OCCUPANCY_BG = (30, 32, 38)
OCCUPANCY_TEXT = (240, 240, 240)


def calculate_view_params(config: Config) -> tuple[int, int, int, int]:
    """Calculate the initial camera scale and offset for the map."""
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


def get_hub_color(hub_item: hub) -> tuple[int, int, int]:
    """Return the color used to draw a hub based on its metadata."""
    if hub_item.color and hub_item.color in NAMED_COLORS:
        return NAMED_COLORS[hub_item.color]
    return DEFAULT_ZONE_COLOR.get(
        hub_item.zone_type or "normal",
        (200, 200, 200),
    )


def render_text(
    screen: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    pos: tuple[int, int],
    color: tuple[int, int, int] = TEXT_COLOR,
) -> None:
    """Render a text label."""
    screen.blit(font.render(text, True, color), pos)
