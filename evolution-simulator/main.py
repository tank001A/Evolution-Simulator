import pygame
import time

from classes import World


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

status_font = pygame.font.Font(None, 24)

world_surface = pygame.Surface(
    (GRID_WIDTH, GRID_HEIGHT)
).convert()

world = World(
    name="Test World",
    grid_height=GRID_HEIGHT,
    grid_width=GRID_WIDTH
)

clock = pygame.time.Clock()

simulation_timer = 0
simulation_interval = 1 / SIMULATION_TICKS_PER_SECOND

running = True


def draw_status_panel(screen, world, font):
    if world.paused:
        state_text = "State: Paused"
        state_colour = (255, 180, 80)
    else:
        state_text = "State: Running"
        state_colour = (120, 255, 120)

    status_lines = [
        (state_text, state_colour),
        (
            f"Simulation ticks: {world.simulation_time}",
            (255, 255, 255)
        ),
        (
            f"Real time: {world.get_elapsed_time():.2f} seconds",
            (255, 255, 255)
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

    panel_width = 270
    panel_height = 140

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

    display_width = max(1, int(world_width * scale))
    display_height = max(1, int(world_height * scale))

    display_x = (window_width - display_width) // 2
    display_y = (window_height - display_height) // 2

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

    window_width, window_height = screen.get_size()


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.VIDEORESIZE:
            if not fullscreen:
                window_width = event.w
                window_height = event.h

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if world.paused:
                    world.continue_world()
                else:
                    world.pause_world()

            elif event.key == pygame.K_F11:
                toggle_fullscreen()

    delta_time = clock.tick(TARGET_FPS) / 1000

    if not world.paused:
        simulation_timer += delta_time

        while simulation_timer >= simulation_interval:
            world.update()
            simulation_timer -= simulation_interval
    else:
        simulation_timer = 0

    world_surface.fill((0, 0, 0))
    world.draw(world_surface)

    world_rect = get_world_display_rect(
        window_width,
        window_height,
        GRID_WIDTH,
        GRID_HEIGHT
    )

    scaled_world = pygame.transform.scale(
        world_surface,
        world_rect.size
    )

    screen.fill((20, 20, 20))
    screen.blit(
        scaled_world,
        world_rect
    )

    draw_status_panel(
        screen,
        world,
        status_font
    )

    pygame.display.flip()


pygame.quit()