import pygame

from classes import Moss, World


pygame.init()
pygame.font.init()


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Evolution Simulator"

GRID_WIDTH = 400
GRID_HEIGHT = 300

SIMULATION_TICKS_PER_SECOND = 10
TARGET_FPS = 60

WINDOWED_FLAGS = pygame.RESIZABLE


screen = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT),
    WINDOWED_FLAGS
)

pygame.display.set_caption(SCREEN_TITLE)


window_width = SCREEN_WIDTH
window_height = SCREEN_HEIGHT
fullscreen = False


status_font = pygame.font.Font(
    None,
    24
)


world_surface = pygame.Surface(
    (GRID_WIDTH, GRID_HEIGHT)
).convert()


world = World(
    name="Test World",
    grid_height=GRID_HEIGHT,
    grid_width=GRID_WIDTH
)


clock = pygame.time.Clock()

simulation_timer = 0.0
simulation_interval = (
    1 / SIMULATION_TICKS_PER_SECOND
)

scaled_world = None
last_world_rect = None

running = True


def draw_status_panel(screen, world, font, fps):
    if world.paused:
        state_text = "State: Paused"
        state_colour = (255, 180, 80)
    else:
        state_text = "State: Running"
        state_colour = (120, 255, 120)

    status_lines = [
        (state_text, state_colour),
        (
            f"Simulation ticks: "
            f"{world.simulation_time}",
            (255, 255, 255)
        ),
        (
            f"Real time: "
            f"{world.get_elapsed_time():.2f} seconds",
            (255, 255, 255)
        ),
        (
            f"Average water: "
            f"{world.get_average_water():.2f}",
            (120, 200, 255)
        ),
        (
            f"Organism density: "
            f"{world.get_total_organism_density():.2f}",
            (180, 255, 180)
        ),
        (
            f"FPS: {fps:.1f}",
            (200, 200, 200)
        ),
        (
            "SPACE: Pause/Resume",
            (200, 200, 200)
        ),
        (
            "F11: Fullscreen",
            (200, 200, 200)
        )
    ]

    panel_width = 310
    panel_height = 215

    pygame.draw.rect(
        screen,
        (25, 25, 25),
        pygame.Rect(
            0,
            0,
            panel_width,
            panel_height
        )
    )

    y_position = 8

    for text, colour in status_lines:
        text_surface = font.render(
            text,
            True,
            colour
        )

        screen.blit(
            text_surface,
            (10, y_position)
        )

        y_position += 25


def get_world_display_rect(
    window_width,
    window_height,
    world_width,
    world_height
):
    scale = min(
        window_width / world_width,
        window_height / world_height
    )

    display_width = max(
        1,
        int(world_width * scale)
    )

    display_height = max(
        1,
        int(world_height * scale)
    )

    display_x = (
        window_width - display_width
    ) // 2

    display_y = (
        window_height - display_height
    ) // 2

    return pygame.Rect(
        display_x,
        display_y,
        display_width,
        display_height
    )


def toggle_fullscreen():
    global screen
    global fullscreen
    global window_width
    global window_height
    global scaled_world
    global last_world_rect

    fullscreen = not fullscreen

    if fullscreen:
        screen = pygame.display.set_mode(
            (0, 0),
            pygame.FULLSCREEN
        )
    else:
        screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            WINDOWED_FLAGS
        )

    window_width, window_height = (
        screen.get_size()
    )

    scaled_world = None
    last_world_rect = None


def create_demo_organism(world):
    row = world.grid_height // 2
    column = world.grid_width // 2

    tile = world.get_tile_at(
        row,
        column
    )

    tile.water_content = 20.0
    tile.nutrient_content = 10.0

    moss = Moss(
        organism_position=(row, column),
        density=500.0,
        mortality_rate=0.05
    )

    world.add_organism(moss)


create_demo_organism(world)


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.VIDEORESIZE:
            if not fullscreen:
                window_width = event.w
                window_height = event.h

                scaled_world = None
                last_world_rect = None

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if world.paused:
                    world.continue_world()
                else:
                    world.pause_world()

            elif event.key == pygame.K_F11:
                toggle_fullscreen()

    delta_time = (
        clock.tick(TARGET_FPS) / 1000
    )

    if not world.paused:
        simulation_timer += delta_time

        while simulation_timer >= simulation_interval:
            world.update()
            simulation_timer -= simulation_interval
    else:
        simulation_timer = 0.0

    world_rect = get_world_display_rect(
        window_width,
        window_height,
        GRID_WIDTH,
        GRID_HEIGHT
    )

    if (
        scaled_world is None
        or last_world_rect != world_rect
        or world.display_changed
    ):
        world.draw(world_surface)

        scaled_world = pygame.transform.scale(
            world_surface,
            world_rect.size
        )

        last_world_rect = world_rect.copy()

    screen.fill(
        (20, 20, 20)
    )

    screen.blit(
        scaled_world,
        world_rect
    )

    draw_status_panel(
        screen,
        world,
        status_font,
        clock.get_fps()
    )

    pygame.display.flip()


pygame.quit()