import pygame

from properties.classes.Organisms import *
from properties.classes.worldbehavior.class_world import World

pygame.init()
pygame.font.init()


# window dimensions are measured in pixels; grid dimensions count tiles.
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
SCREEN_TITLE = "Evolution Simulator"

GRID_WIDTH = 10
GRID_HEIGHT = 10

# The information panel keeps a fixed width when the window is resized.
MAP_WIDTH = 720
PANEL_WIDTH = SCREEN_WIDTH - MAP_WIDTH

# simulation ticks and redrawing are different things.
# Keeping them separate lets camera movement stay smooth without updating
# the environmental and biological calculations every frame.
SIMULATION_TICKS_PER_SECOND = 500
TARGET_FPS = 45

# these two constants are currently unused because i use ZOOM_LEVELS instead.
#MIN_ZOOM = 1
#MAX_ZOOM = 32

# Each zoom value is the number of screen pixels representing one tile, making it easy to configure it
#also avoids "strange" numbers
ZOOM_LEVELS = [
    1,
    2,
    4,
    8,
    16,
    24,
    32,
    64
]

PAN_SPEED = 300.0


screen = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT),
    pygame.RESIZABLE
)

pygame.display.set_caption(SCREEN_TITLE)

# None selects pygame's default font.
status_font = pygame.font.Font(None, 20)
small_font = pygame.font.Font(None, 16)


world = World(
    name="Test World",
    grid_height=GRID_HEIGHT,
    grid_width=GRID_WIDTH
)


clock = pygame.time.Clock()

# accumulate elapsed seconds until enough time has passed for another tick.
simulation_timer = 0.0
simulation_interval = 1 / SIMULATION_TICKS_PER_SECOND

# stats are recalculated less frequently than the display is redrawn.
statistics_timer = 0.0
statistics_interval = 0.5

# camera coordinates are measured in tiles, not pixels.
# decimals allow smooth movement between tile positions.
camera_x = 0.0
camera_y = 0.0
zoom = 2

# A selection is stored as (row, column), or None when nothing is selected.
selected_position = None

# Index of the first species shown in the selected tile's species list.
species_scroll = 0

fullscreen = False
running = True


def get_map_viewport():
    # Use the current window size rather than its original dimensions.
    # max(1, ...) prevents the map width becoming zero or negative.
    return pygame.Rect(
        0,
        0,
        max(1, screen.get_width() - PANEL_WIDTH),
        screen.get_height()
    )


def get_panel_rect():
    # anchors the panel to the right edge of the window.
    return pygame.Rect(
        screen.get_width() - PANEL_WIDTH,
        0,
        PANEL_WIDTH,
        screen.get_height()
    )


def get_visible_tile_size(viewport):
    # Dividing pixels by pixels-per-tile gives the number of whole tiles
    # that fit across the viewport.
    visible_columns = max(1, viewport.width // zoom)
    visible_rows = max(1, viewport.height // zoom)

    return visible_columns, visible_rows


def clamp_camera():
    # These functions modify the module-level camera variables.
    global camera_x
    global camera_y

    viewport = get_map_viewport()

    visible_columns, visible_rows = get_visible_tile_size(viewport)

    # Subtract the visible area so the camera cannot move beyond the world.
    # If the whole world fits on screen, the maximum position becomes zero.
    max_camera_x = max(0, GRID_WIDTH - visible_columns)
    max_camera_y = max(0, GRID_HEIGHT - visible_rows)

    camera_x = max(0.0, min(camera_x, max_camera_x))
    camera_y = max(0.0, min(camera_y, max_camera_y))


def get_next_zoom(current_zoom, direction):
    # direction is normally +1 for zooming in or -1 for zooming out.
    # current_zoom must already be one of the values in ZOOM_LEVELS.
    current_index = ZOOM_LEVELS.index(current_zoom)

    # Keep the new index inside the list's valid range.
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
    new_zoom = get_next_zoom(zoom, direction)

    if new_zoom == old_zoom:
        return

    viewport = get_map_viewport()

    # Remember the world coordinates at the centre of the old view.
    # This lets us zoom around the centre instead of the top-left corner.
    centre_x = camera_x + viewport.width / (2 * old_zoom)
    centre_y = camera_y + viewport.height / (2 * old_zoom)

    zoom = new_zoom

    # Reposition the camera to keep the same world point centred.
    camera_x = centre_x - viewport.width / (2 * zoom)
    camera_y = centre_y - viewport.height / (2 * zoom)

    # Staying inside the world takes priority over keeping that centre.
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

    # Poll held keys for continuous movement, rather than reacting only
    # to the instant a key is pressed.
    keys = pygame.key.get_pressed()

    horizontal = 0
    vertical = 0

    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        horizontal -= 1

    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        horizontal += 1

    if keys[pygame.K_w] or keys[pygame.K_UP]:
        vertical -= 1

    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        vertical += 1

    # Opposite directions cancel out because their values add to zero.
    # Multiplying by elapsed seconds makes movement independent of FPS.
    # Dividing by zoom converts the intended screen movement into tile units.
    pan_amount = PAN_SPEED * delta_time / zoom

    camera_x += horizontal * pan_amount
    camera_y += vertical * pan_amount

    clamp_camera()


def screen_to_tile(screen_position):
    viewport = get_map_viewport()

    mouse_x, mouse_y = screen_position

    # Clicking the information panel should not select a world tile.
    if not viewport.collidepoint(mouse_x, mouse_y):
        return None

    # Remove the viewport offset, convert pixels to tiles, and then add
    # the camera offset to find the position in the full world.
    column = int(
        camera_x + (mouse_x - viewport.x) / zoom
    )

    row = int(
        camera_y + (mouse_y - viewport.y) / zoom
    )

    # The map area can be larger than the world, so a click inside the
    # viewport does not necessarily land on an existing tile.
    if not (
        0 <= row < GRID_HEIGHT
        and 0 <= column < GRID_WIDTH
    ):
        return None

    return row, column


def tile_to_screen(row, column):
    # Reverse the coordinate conversion used by screen_to_tile.
    # This helper is available for future markers or organism drawings,
    # but nothing in this main.py currently calls it.
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

    return world.get_tile_at(row, column)


def get_species_rows(tile):
    if tile is None:
        return []

    # Convert the tile's species dictionary into displayable pairs.
    # Very small biomass values are hidden from this list, not removed
    # from the simulation itself.
    species_rows = [
        (species_name, biomass)
        for species_name, biomass in tile.species_biomass.items()
        if biomass > 0.01
    ]

    # Each pair is (name, biomass), so item[1] is the biomass.
    # Show the largest populations first.
    species_rows.sort(
        key=lambda item: item[1],
        reverse=True
    )

    return species_rows


def draw_map():
    viewport = get_map_viewport()

    # The World class handles tile rendering; main.py supplies the view.
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

    # Padding keeps the text away from the panel edges.
    x = panel.x + 12
    y = 12

    # Font.render creates a surface containing text.
    # blit then copies that text surface onto the screen.
    title = status_font.render(
        "Tile information",
        True,
        (255, 255, 255)
    )

    screen.blit(title, (x, y))
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

            screen.blit(text_surface, (x, y))
            y += 22

        # No tile exists to inspect, so skip the remaining panel sections.
        return

    # f-strings insert tile values into the text.
    # .1f and .2f display one or two decimal places without changing
    # the underlying values stored in the simulation.
    information = [
        f"Position: ({tile.row}, {tile.column})",
        f"Lithology: {tile.lithology}",
        f"UCS: {tile.ucs_mpa:.1f} MPa",
        f"Weathering: {tile.weathering_progress:.2f}",
        f"Soil: {tile.soil_depth:.2f}",
        f"Water: {tile.water_content:.2f}",
        f"Nutrients: {tile.nutrient_content:.2f}",
        f"Organic matter: {tile.organic_matter:.2f}",
        f"Stage: {tile.get_succession_stage()}"
    ]

    for line in information:
        text_surface = small_font.render(
            line,
            True,
            (220, 220, 220)
        )

        screen.blit(text_surface, (x, y))
        y += 21

    y += 10

    species_title = status_font.render(
        "Species populations",
        True,
        (180, 255, 180)
    )

    screen.blit(species_title, (x, y))
    y += 30

    species_rows = get_species_rows(tile)

    if not species_rows:
        text_surface = small_font.render(
            "No species present.",
            True,
            (200, 200, 200)
        )

        screen.blit(text_surface, (x, y))
        return

    # Take up to 15 entries, starting at the current scroll position.
    # The end index of a slice is excluded.
    visible_species = species_rows[
        species_scroll:
        species_scroll + 15
    ]

    for species_name, biomass in visible_species:
        line = f"{species_name}: {biomass:.2f}"

        text_surface = small_font.render(
            line,
            True,
            (210, 255, 210)
        )

        screen.blit(text_surface, (x, y))
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

    # Work upwards from the bottom so the controls remain bottom-aligned
    # when the window height changes.
    y = screen.get_height() - len(controls) * 20 - 10

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
        # (0, 0) requests the current display resolution for fullscreen.
        screen = pygame.display.set_mode(
            (0, 0),
            pygame.FULLSCREEN
        )
    else:
        # Restore the configured starting size, not the last resized size.
        screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.RESIZABLE
        )

    # A different screen size changes how many tiles fit in the viewport.
    clamp_camera()


def create_demo_organism():
    # Integer division chooses a central tile.
    row = GRID_HEIGHT // 2
    column = GRID_WIDTH // 2

    tile = world.get_tile_at(row, column)

    # Give the starting tile suitable conditions so the demo moss can grow.
    tile.water_content = 30.0
    tile.nutrient_content = 20.0
    tile.weathering_progress = 10.0

    moss = Moss(
        organism_position=(row, column),
        density=100.0
    )

    # The tile dictionary supplies the panel's population information.
    # The world organism list supplies the objects that receive updates.
    tile.species_biomass["Moss"] = moss.density
    world.add_organism(moss)


create_demo_organism()
world.update_statistics()


while running:
    # Process queued actions before updating and drawing the next frame.
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.VIDEORESIZE:
            if not fullscreen:
                clamp_camera()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                selected_position = screen_to_tile(event.pos)

                # A newly selected tile should show its list from the top.
                species_scroll = 0

            # Mouse-wheel scrolling is handled here as button 4 or 5.
            elif event.button == 4:
                change_zoom(1)

            elif event.button == 5:
                change_zoom(-1)

        elif event.type == pygame.KEYDOWN:
            # Use press events for actions that should happen once,
            # rather than every frame while the key is held.
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
                    species_count = len(get_species_rows(tile))

                    # This original limit allows scrolling until only the
                    # final species remains. To keep the last page full,
                    # use species_count - 15 instead of species_count - 1.
                    species_scroll = min(
                        max(0, species_count - 1),
                        species_scroll + 1
                    )

    # tick limits FPS and returns elapsed milliseconds.
    # Convert to seconds for the movement and simulation calculations.
    delta_time = clock.tick(TARGET_FPS) / 1000.0

    # Viewing controls still work while the biological simulation is paused.
    pan_camera(delta_time)

    if not world.paused:
        simulation_timer += delta_time

        # A while loop allows multiple ticks after a slow frame.
        # Subtracting each interval preserves any leftover elapsed time.
        while simulation_timer >= simulation_interval:
            world.update()
            simulation_timer -= simulation_interval

    # Statistics continue refreshing while paused, although the world itself
    # does not advance.
    statistics_timer += delta_time

    if statistics_timer >= statistics_interval:
        world.update_statistics()
        statistics_timer = 0.0

    # Draw the complete frame from back to front.
    # Drawing the panel after the map ensures the panel appears above it.
    screen.fill((15, 15, 15))

    draw_map()
    draw_panel()
    draw_controls()

    # Present the completed frame after all drawing has finished.
    pygame.display.flip()


pygame.quit()