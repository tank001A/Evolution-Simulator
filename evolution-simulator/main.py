import pygame

from classes import Moss, World


pygame.init()
pygame.font.init()


SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
SCREEN_TITLE = "Evolution Simulator"

GRID_WIDTH = 100
GRID_HEIGHT = 100

MAP_WIDTH = 720
PANEL_WIDTH = SCREEN_WIDTH - MAP_WIDTH

SIMULATION_TICKS_PER_SECOND = 10
TARGET_FPS = 60

MIN_ZOOM = 1
MAX_ZOOM = 32
ZOOM_LEVELS = [
    1,
    2,
    4,
    8,
    16,
    24,
    32
]

PAN_SPEED = 300.0


screen = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT),
    pygame.RESIZABLE
)

pygame.display.set_caption(
    SCREEN_TITLE
)


status_font = pygame.font.Font(
    None,
    20
)

small_font = pygame.font.Font(
    None,
    16
)


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

statistics_timer = 0.0
statistics_interval = 0.5

camera_x = 0.0
camera_y = 0.0
zoom = 2

selected_position = None
species_scroll = 0

fullscreen = False
running = True


def get_map_viewport():
    return pygame.Rect(
        0,
        0,
        max(1, screen.get_width() - PANEL_WIDTH),
        screen.get_height()
    )


def get_panel_rect():
    return pygame.Rect(
        screen.get_width() - PANEL_WIDTH,
        0,
        PANEL_WIDTH,
        screen.get_height()
    )


def get_visible_tile_size(viewport):
    visible_columns = max(
        1,
        viewport.width // zoom
    )

    visible_rows = max(
        1,
        viewport.height // zoom
    )

    return visible_columns, visible_rows


def clamp_camera():
    global camera_x
    global camera_y

    viewport = get_map_viewport()

    visible_columns, visible_rows = (
        get_visible_tile_size(viewport)
    )

    max_camera_x = max(
        0,
        GRID_WIDTH - visible_columns
    )

    max_camera_y = max(
        0,
        GRID_HEIGHT - visible_rows
    )

    camera_x = max(
        0.0,
        min(camera_x, max_camera_x)
    )

    camera_y = max(
        0.0,
        min(camera_y, max_camera_y)
    )


def get_next_zoom(current_zoom, direction):
    current_index = ZOOM_LEVELS.index(
        current_zoom
    )

    new_index = max(
        0,
        min(
            len(ZOOM_LEVELS) - 1,
            current_index + direction
        )
    )

    return ZOOM_LEVELS[new_index]


def change_zoom(direction):
    global zoom
    global camera_x
    global camera_y

    old_zoom = zoom
    new_zoom = get_next_zoom(
        zoom,
        direction
    )
    if new_zoom == old_zoom:
        return

    viewport = get_map_viewport()

    centre_x = (
        camera_x
        + viewport.width / (2 * old_zoom)
    )

    centre_y = (
        camera_y
        + viewport.height / (2 * old_zoom)
    )

    zoom = new_zoom

    camera_x = (
        centre_x
        - viewport.width / (2 * zoom)
    )

    camera_y = (
        centre_y
        - viewport.height / (2 * zoom)
    )

    clamp_camera()


def reset_camera():
    global camera_x
    global camera_y
    global zoom

    camera_x = 0.0
    camera_y = 0.0
    zoom = 2

    clamp_camera()


def pan_camera(delta_time):
    global camera_x
    global camera_y

    keys = pygame.key.get_pressed()

    horizontal = 0
    vertical = 0

    if (
        keys[pygame.K_a]
        or keys[pygame.K_LEFT]
    ):
        horizontal -= 1

    if (
        keys[pygame.K_d]
        or keys[pygame.K_RIGHT]
    ):
        horizontal += 1

    if (
        keys[pygame.K_w]
        or keys[pygame.K_UP]
    ):
        vertical -= 1

    if (
        keys[pygame.K_s]
        or keys[pygame.K_DOWN]
    ):
        vertical += 1

    pan_amount = (
        PAN_SPEED
        * delta_time
        / zoom
    )

    camera_x += horizontal * pan_amount
    camera_y += vertical * pan_amount

    clamp_camera()


def screen_to_tile(screen_position):
    viewport = get_map_viewport()

    mouse_x, mouse_y = screen_position

    if not viewport.collidepoint(
        mouse_x,
        mouse_y
    ):
        return None

    column = int(
        camera_x
        + (mouse_x - viewport.x) / zoom
    )

    row = int(
        camera_y
        + (mouse_y - viewport.y) / zoom
    )

    if not (
        0 <= row < GRID_HEIGHT
        and 0 <= column < GRID_WIDTH
    ):
        return None

    return row, column


def tile_to_screen(row, column):
    viewport = get_map_viewport()

    screen_x = (
        viewport.x
        + int((column - camera_x) * zoom)
    )

    screen_y = (
        viewport.y
        + int((row - camera_y) * zoom)
    )

    return screen_x, screen_y


def get_selected_tile():
    if selected_position is None:
        return None

    row, column = selected_position

    return world.get_tile_at(
        row,
        column
    )


def get_species_rows(tile):
    if tile is None:
        return []

    species_rows = [
        (
            species_name,
            biomass
        )
        for species_name, biomass
        in tile.species_biomass.items()
        if biomass > 0.01
    ]

    species_rows.sort(
        key=lambda item: item[1],
        reverse=True
    )

    return species_rows


def draw_map():
    viewport = get_map_viewport()

    world.draw_visible(
        screen,
        camera_x,
        camera_y,
        zoom,
        viewport,
        selected_position
    )


def draw_panel():
    panel = get_panel_rect()

    pygame.draw.rect(
        screen,
        (25, 25, 25),
        panel
    )

    tile = get_selected_tile()

    x = panel.x + 12
    y = 12

    title = status_font.render(
        "Tile information",
        True,
        (255, 255, 255)
    )

    screen.blit(
        title,
        (x, y)
    )

    y += 30

    if tile is None:
        lines = [
            "Click a tile to inspect it.",
            "",
            "P: Zoom in",
            "O: Zoom out",
            "WASD/Arrows: Pan",
            "Home: Reset view"
        ]

        for line in lines:
            text_surface = small_font.render(
                line,
                True,
                (210, 210, 210)
            )

            screen.blit(
                text_surface,
                (x, y)
            )

            y += 22

        return

    information = [
        (
            f"Position: "
            f"({tile.row}, {tile.column})"
        ),
        f"Lithology: {tile.lithology}",
        f"UCS: {tile.ucs_mpa:.1f} MPa",
        (
            f"Weathering: "
            f"{tile.weathering_progress:.2f}"
        ),
        f"Soil: {tile.soil_depth:.2f}",
        f"Water: {tile.water_content:.2f}",
        f"Nutrients: {tile.nutrient_content:.2f}",
        (
            f"Organic matter: "
            f"{tile.organic_matter:.2f}"
        ),
        (
            f"Stage: "
            f"{tile.get_succession_stage()}"
        )
    ]

    for line in information:
        text_surface = small_font.render(
            line,
            True,
            (220, 220, 220)
        )

        screen.blit(
            text_surface,
            (x, y)
        )

        y += 21

    y += 10

    species_title = status_font.render(
        "Species populations",
        True,
        (180, 255, 180)
    )

    screen.blit(
        species_title,
        (x, y)
    )

    y += 30

    species_rows = get_species_rows(tile)

    if not species_rows:
        text_surface = small_font.render(
            "No species present.",
            True,
            (200, 200, 200)
        )

        screen.blit(
            text_surface,
            (x, y)
        )

        return

    visible_species = species_rows[
        species_scroll:
        species_scroll + 15
    ]

    for species_name, biomass in visible_species:
        line = (
            f"{species_name}: "
            f"{biomass:.2f}"
        )

        text_surface = small_font.render(
            line,
            True,
            (210, 255, 210)
        )

        screen.blit(
            text_surface,
            (x, y)
        )

        y += 20


def draw_controls():
    panel = get_panel_rect()

    controls = [
        "Controls:",
        "P: Zoom in",
        "O: Zoom out",
        "WASD/Arrows: Move",
        "Left click: Select",
        "Mouse wheel: Zoom",
        "Space: Pause",
        "F11: Fullscreen"
    ]

    y = screen.get_height() - (
        len(controls) * 20
    ) - 10

    for line in controls:
        text_surface = small_font.render(
            line,
            True,
            (180, 180, 180)
        )

        screen.blit(
            text_surface,
            (panel.x + 12, y)
        )

        y += 20


def toggle_fullscreen():
    global screen
    global fullscreen

    fullscreen = not fullscreen

    if fullscreen:
        screen = pygame.display.set_mode(
            (0, 0),
            pygame.FULLSCREEN
        )
    else:
        screen = pygame.display.set_mode(
            (
                SCREEN_WIDTH,
                SCREEN_HEIGHT
            ),
            pygame.RESIZABLE
        )

    clamp_camera()


def create_demo_organism():
    row = GRID_HEIGHT // 2
    column = GRID_WIDTH // 2

    tile = world.get_tile_at(
        row,
        column
    )

    tile.water_content = 30.0
    tile.nutrient_content = 20.0
    tile.weathering_progress = 10.0

    moss = Moss(
        organism_position=(row, column),
        density=100.0
    )

    tile.species_biomass[
        "Moss"
    ] = moss.density

    world.add_organism(moss)


create_demo_organism()
world.update_statistics()


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.VIDEORESIZE:
            if not fullscreen:
                clamp_camera()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                selected_position = (
                    screen_to_tile(event.pos)
                )

                species_scroll = 0

            elif event.button == 4:
                change_zoom(1)

            elif event.button == 5:
                change_zoom(-1)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                change_zoom(1)

            elif event.key == pygame.K_o:
                change_zoom(-1)

            elif event.key == pygame.K_HOME:
                reset_camera()

            elif event.key == pygame.K_SPACE:
                if world.paused:
                    world.continue_world()
                else:
                    world.pause_world()

            elif event.key == pygame.K_F11:
                toggle_fullscreen()

            elif event.key == pygame.K_PAGEUP:
                species_scroll = max(
                    0,
                    species_scroll - 1
                )

            elif event.key == pygame.K_PAGEDOWN:
                tile = get_selected_tile()

                if tile is not None:
                    species_count = len(
                        get_species_rows(tile)
                    )

                    species_scroll = min(
                        max(0, species_count - 1),
                        species_scroll + 1
                    )

    delta_time = (
        clock.tick(TARGET_FPS)
        / 1000.0
    )

    pan_camera(delta_time)

    if not world.paused:
        simulation_timer += delta_time

        while (
            simulation_timer
            >= simulation_interval
        ):
            world.update()
            simulation_timer -= simulation_interval

    statistics_timer += delta_time

    if (
        statistics_timer
        >= statistics_interval
    ):
        world.update_statistics()
        statistics_timer = 0.0

    screen.fill(
        (15, 15, 15)
    )

    draw_map()
    draw_panel()
    draw_controls()

    pygame.display.flip()


pygame.quit()