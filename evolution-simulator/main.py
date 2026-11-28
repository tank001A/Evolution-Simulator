import pygame

from plant_data_handling.plant_data import load_species
from properties.classes.speciesbehavior.organisms.colonisers.rockcolonisers import (
    Moss,
    Lichen
)

from properties.classes.speciesbehavior.organisms.colonisers.watercolonisers import (
    Reeds,
    Phytoplankton
)

from properties.classes.worldbehavior.class_world import World
from properties.classes.worldbehavior.other.tiles.rock_tile import RockTile
from properties.classes.worldbehavior.other.tiles.water_tile import WaterTile

from properties.classes.worldbehavior.class_tile import Tile

tile = Tile(0, 0)

print("Initial environment:")
print(tile.get_plant_environment())

print("Initial indicators:")
print(tile.get_plant_indicator_values())

tile.add_water(50)
tile.add_nutrients(30)
tile.add_organic_matter(20)

tile.update_light(40)
tile.update_soil_ph(2.0)

print("Updated environment:")
print(tile.get_plant_environment())

print("Updated indicators:")
print(tile.get_plant_indicator_values())
grassland_species = load_species("grassland")

print("Number of species:", len(grassland_species))

for species in list(grassland_species.values())[:5]:
    print(species.name, species.moisture, species.growth_form)



pygame.init()
pygame.font.init()


# window dimensions are pixels while grid dimensions count tiles
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
SCREEN_TITLE = "Evolution Simulator"

GRID_WIDTH = 10
GRID_HEIGHT = 10

MAP_WIDTH = 720
PANEL_WIDTH = SCREEN_WIDTH - MAP_WIDTH

# drawing and simulation have separate timers so camera movement does not
# require an environmental calculation on every frame
# these rates target 500 simulation ticks and 45 display frames per second
SIMULATION_TICKS_PER_SECOND = 200
TARGET_FPS = 45

# fixed zoom choices make tile sizes predictable and keep selection simple
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

# 64 makes the small test world visible without several manual zoom steps
# use a lower value when testing much larger worlds
START_ZOOM = 64

PAN_SPEED = 300.0

# share these values between the display and its scroll controls
# this avoids separate hard-coded limits disagreeing with each other
SPECIES_ROW_HEIGHT = 20
MAX_VISIBLE_SPECIES = 15

CONTROL_LINES = [
    "Controls:",
    "P: Zoom in",
    "O: Zoom out",
    "WASD/Arrows: Move",
    "Left click: Select",
    "Mouse wheel: Zoom",
    "Page Up/Down: Species",
    "Space: Pause",
    "F11: Fullscreen",
    "Spacebar: Reset view"
]


screen = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT),
    pygame.RESIZABLE
)

pygame.display.set_caption(SCREEN_TITLE)

status_font = pygame.font.Font(None, 20)
small_font = pygame.font.Font(None, 16)

clock = pygame.time.Clock()

simulation_timer = 0.0
simulation_interval = 1 / SIMULATION_TICKS_PER_SECOND

statistics_timer = 0.0
statistics_interval = 0.5

# these are tile coordinates rather than screen pixel coordinates
camera_x = 0.0
camera_y = 0.0
zoom = START_ZOOM

selected_position = None
species_scroll = 0

fullscreen = False
running = True


def selection_menu():
    # selecting an environment changes the menu but does not create a world
    # allocation only happens once the user has also chosen a coloniser
    environment_type = None

    choices = {
        "rock": [
            ("Moss", Moss),
            ("Lichen", Lichen)
        ],
        "water": [
            ("Phytoplankton", Phytoplankton),
            ("Reeds", Reeds)
        ]
    }

    while True:
        # calculate layout again because the menu window can be resized
        width = screen.get_width()
        height = screen.get_height()

        button_width = min(400, max(120, width - 40))
        button_x = (width - button_width) // 2
        first_y = max(100, height // 2 - 70)

        first_button = pygame.Rect(
            button_x,
            first_y,
            button_width,
            65
        )

        second_button = pygame.Rect(
            button_x,
            first_y + 85,
            button_width,
            65
        )

        if environment_type is None:
            title_text = "Choose an environment"

            options = [
                ("Rocky environment", "rock"),
                ("Water environment", "water")
            ]
        else:
            title_text = "Choose a starting coloniser"
            options = choices[environment_type]

        # choose one action per frame so several queued clicks cannot
        # accidentally use the previous page's buttons on the next page
        chosen_value = None
        go_back = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    go_back = True

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and chosen_value is None:
                    if first_button.collidepoint(event.pos):
                        chosen_value = options[0][1]
                    elif second_button.collidepoint(event.pos):
                        chosen_value = options[1][1]

        if go_back:

            if environment_type is None:
                return None

            environment_type = None
            continue

        if chosen_value is not None:

            if environment_type is None:
                environment_type = chosen_value
                continue

            # return a class rather than an already created organism
            # its starting position will be chosen after the world exists
            return environment_type, chosen_value

        screen.fill((15, 15, 15))

        title = status_font.render(
            title_text,
            True,
            (255, 255, 255)
        )

        screen.blit(
            title,
            title.get_rect(
                center=(width // 2, first_y - 40)
            )
        )

        mouse_position = pygame.mouse.get_pos()

        for rectangle, (label, _) in zip(
            (first_button, second_button),
            options
        ):
            # a hover colour makes it clearer that the rectangles are buttons

            colour = (
                (75, 105, 85)
                if rectangle.collidepoint(mouse_position)
                else (45, 65, 55)
            )

            pygame.draw.rect(
                screen,
                colour,
                rectangle,
                border_radius=8
            )

            text = status_font.render(
                label,
                True,
                (255, 255, 255)
            )

            screen.blit(
                text,
                text.get_rect(center=rectangle.center)
            )

        instructions = small_font.render(
            "click on an option - press esc to go back or quit",
            True,
            (190, 190, 190)
        )

        screen.blit(
            instructions,
            instructions.get_rect(
                center=(width // 2, second_button.bottom + 35)
            )
        )

        pygame.display.flip()
        clock.tick(TARGET_FPS)


def get_map_viewport():
    # read the current surface dimensions rather than the starting window size
    return pygame.Rect(
        0,
        0,
        max(1, screen.get_width() - PANEL_WIDTH),
        screen.get_height()
    )


def get_panel_rect():
    # the panel stays the same width and follows the right window edge
    return pygame.Rect(
        screen.get_width() - PANEL_WIDTH,
        0,
        PANEL_WIDTH,
        screen.get_height()
    )


def clamp_camera():
    global camera_x
    global camera_y

    viewport = get_map_viewport()

    # use the exact visible width in tile units rather than rounding down
    # this avoids a blank strip at the edge when a partial tile is visible
    visible_columns = viewport.width / zoom
    visible_rows = viewport.height / zoom

    max_camera_x = max(0.0, world.grid_width - visible_columns)
    max_camera_y = max(0.0, world.grid_height - visible_rows)

    camera_x = max(0.0, min(camera_x, max_camera_x))
    camera_y = max(0.0, min(camera_y, max_camera_y))


def get_next_zoom(current_zoom, direction):
    current_index = ZOOM_LEVELS.index(current_zoom)

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

    # preserve the world point at the center of the view while changing scale
    # without this the view would zoom around its top left corner
    centre_x = camera_x + viewport.width / (2 * old_zoom)
    centre_y = camera_y + viewport.height / (2 * old_zoom)

    zoom = new_zoom

    camera_x = centre_x - viewport.width / (2 * zoom)
    camera_y = centre_y - viewport.height / (2 * zoom)

    # boundaries take priority if maintaining the center would leave the world
    clamp_camera()


def reset_camera():
    global camera_x
    global camera_y
    global zoom

    camera_x = 0.0
    camera_y = 0.0
    zoom = START_ZOOM

    clamp_camera()


def pan_camera(delta_time):
    global camera_x
    global camera_y

    # held-key checking is used for continuous movement
    # individual press events are used elsewhere for toggles and selection
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

    # opposite directions cancel out
    # elapsed seconds make movement independent of the number of drawn frames
    # dividing by zoom converts screen movement into world tile movement
    pan_amount = PAN_SPEED * delta_time / zoom

    camera_x += horizontal * pan_amount
    camera_y += vertical * pan_amount

    clamp_camera()


def screen_to_tile(screen_position):
    viewport = get_map_viewport()
    mouse_x, mouse_y = screen_position

    if not viewport.collidepoint(mouse_x, mouse_y):
        return None

    # undo the viewport offset and zoom before applying the camera position
    column = int(
        camera_x + (mouse_x - viewport.x) / zoom
    )

    row = int(
        camera_y + (mouse_y - viewport.y) / zoom
    )

    # empty space can be visible when the world is smaller than the viewport
    if not (
        0 <= row < world.grid_height
        and 0 <= column < world.grid_width
    ):
        return None

    return row, column


def tile_to_screen(row, column):
    # kept as a helper for future organism symbols and world markers
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

    # filtering affects this display list rather than deleting populations
    species_rows = [
        (species_name, biomass)
        for species_name, biomass in tile.species_biomass.items()
        if biomass > 0.01
    ]

    # use the biomass part of each pair to put the largest population first
    species_rows.sort(
        key=lambda item: item[1],
        reverse=True
    )

    return species_rows


def get_tile_information(tile):
    # water tiles still inherit rock fields from Tile internally
    # only show the fields that currently make sense for the chosen habitat
    information = [
        f"Position: ({tile.row}, {tile.column})",
        f"Water: {tile.water_content:.2f}",
        f"Nutrients: {tile.nutrient_content:.2f}",
        f"Organic matter: {tile.organic_matter:.2f}"
    ]

    if tile.tile_type == "rock":
        information.extend([
            f"Lithology: {tile.lithology}",
            f"UCS: {tile.ucs_mpa:.1f} MPa",
            f"Weathering: {tile.weathering_progress:.2f}",
            f"Soil: {tile.soil_depth:.2f}",
            f"Stage: {tile.get_succession_stage()}"
        ])

    return information


def get_controls_top():
    return screen.get_height() - len(CONTROL_LINES) * 20 - 10


def get_species_list_top(tile):
    # match the panel layout so scrolling and rendering use the same space
    # heading and community text finish at y 67
    # information lines use 21 pixels each followed by the species heading
    return 67 + len(get_tile_information(tile)) * 21 + 40


def get_species_page_size(tile):
    # fit species above the controls instead of always drawing 15 lines
    # otherwise the longer rock information panel can overlap the controls
    available_height = (
        get_controls_top()
        - get_species_list_top(tile)
        - 10
    )

    return min(
        MAX_VISIBLE_SPECIES,
        max(0, available_height // SPECIES_ROW_HEIGHT)
    )


def clamp_species_scroll():
    global species_scroll

    tile = get_selected_tile()

    if tile is None:
        species_scroll = 0
        return

    page_size = get_species_page_size(tile)

    if page_size == 0:
        species_scroll = 0
        return

    species_count = len(get_species_rows(tile))

    # keep the final page filled where possible and handle populations vanishing
    maximum_scroll = max(0, species_count - page_size)
    species_scroll = max(0, min(species_scroll, maximum_scroll))


def draw_map():
    world.draw_visible(
        screen,
        camera_x,
        camera_y,
        zoom,
        get_map_viewport(),
        selected_position
    )


def draw_panel():
    panel = get_panel_rect()

    pygame.draw.rect(
        screen,
        (25, 25, 25),
        panel
    )

    # clip panel content above the controls so resizing cannot make text
    # from the two sections draw over one another
    previous_clip = screen.get_clip()

    content_rect = pygame.Rect(
        panel.x,
        panel.y,
        panel.width,
        max(0, get_controls_top() - 8)
    )

    screen.set_clip(content_rect)

    try:
        tile = get_selected_tile()

        x = panel.x + 12
        y = 12

        title = status_font.render(
            "Tile information",
            True,
            (255, 255, 255)
        )

        screen.blit(title, (x, y))
        y += 30

        # community state describes the world even when no tile is selected
        stage = small_font.render(
            f"Community: {world.community_stage}",
            True,
            (180, 255, 180)
        )

        screen.blit(stage, (x, y))
        y += 25

        if tile is None:
            lines = [
                "Click a tile to inspect it.",
                "",
                f"Environment: {world.environment_type}",
                "P: Zoom in",
                "O: Zoom out",
                "WASD/Arrows: Pan",
                "Spacebar: Reset view"
            ]

            for line in lines:
                text_surface = small_font.render(
                    line,
                    True,
                    (210, 210, 210)
                )

                screen.blit(text_surface, (x, y))
                y += 22

            return

        for line in get_tile_information(tile):
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

        page_size = get_species_page_size(tile)

        visible_species = species_rows[
            species_scroll:
            species_scroll + page_size
        ]

        for species_name, biomass in visible_species:
            text_surface = small_font.render(
                f"{species_name}: {biomass:.2f}",
                True,
                (210, 255, 210)
            )

            screen.blit(text_surface, (x, y))
            y += SPECIES_ROW_HEIGHT
    finally:
        # restore even if an early return was used above
        screen.set_clip(previous_clip)


def draw_controls():
    panel = get_panel_rect()
    y = get_controls_top()

    for line in CONTROL_LINES:
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
        # restore the configured size rather than remembering manual resizes
        screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.RESIZABLE
        )

    clamp_camera()
    clamp_species_scroll()


def create_starting_organism(species_class):
    row = world.grid_height // 2
    column = world.grid_width // 2

    tile = world.get_tile_at(row, column)

    if world.environment_type == "rock":
        # a prepared patch lets the selected pioneer survive immediately
        # this is not an entirely untouched primary succession starting point
        tile.water_content = 30.0
        tile.nutrient_content = 20.0
        tile.weathering_progress = 10.0

    # the menu supplies a class so this creates exactly the selected species
    # no alternative populations are created in the background
    organism = species_class(
        organism_position=(row, column),
        density=100.0
    )

    organism.record_biomass(tile)
    world.add_organism(organism)


# no World object exists before the selection menu returns
# closing the menu therefore exits without allocating either environment
selection = selection_menu()

if selection is None:
    pygame.quit()
    raise SystemExit

environment_type, species_class = selection

tile_class = (
    WaterTile
    if environment_type == "water"
    else RockTile
)

world = World(
    name=f"{environment_type.title()} environment",
    grid_height=GRID_HEIGHT,
    grid_width=GRID_WIDTH,
    environment_type=environment_type,
    tile_class=tile_class
)

create_starting_organism(species_class)
world.update_statistics()
world.update_community_stage()

clamp_camera()

# discard time spent in the menu and constructing the world
# otherwise the first frame could try to process that time as simulation ticks
clock.tick()
simulation_timer = 0.0
statistics_timer = 0.0


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.VIDEORESIZE:
            if not fullscreen:
                clamp_camera()
                clamp_species_scroll()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                selected_position = screen_to_tile(event.pos)
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

            elif event.key == pygame.K_SPACE:
                reset_camera()

            elif event.key == pygame.K_SPACE:
                if world.paused:
                    world.continue_world()
                else:
                    world.pause_world()

            elif event.key == pygame.K_F11:
                toggle_fullscreen()

            elif event.key == pygame.K_PAGEUP:
                species_scroll -= 1
                clamp_species_scroll()

            elif event.key == pygame.K_PAGEDOWN:
                species_scroll += 1
                clamp_species_scroll()

    # stop before doing another simulation update after a close request
    if not running:
        break

    # tick limits drawing FPS and returns elapsed milliseconds
    delta_time = clock.tick(TARGET_FPS) / 1000.0

    # viewing controls remain usable while the simulation is paused
    pan_camera(delta_time)

    if not world.paused:
        simulation_timer += delta_time

        # fixed steps make the model use the same tick size regardless of FPS
        # retain leftover time instead of throwing it away each frame
        # at high tick rates a large world may still struggle to keep up
        while simulation_timer >= simulation_interval:
            world.update()
            simulation_timer -= simulation_interval

    statistics_timer += delta_time

    if statistics_timer >= statistics_interval:
        world.update_statistics()

        # only the most recent statistics are needed so missed refreshes
        # do not need to be calculated repeatedly after a slow frame
        statistics_timer %= statistics_interval

    # populations can disappear or the window can shrink after scrolling
    clamp_species_scroll()

    screen.fill((15, 15, 15))

    #draw the interface after the world so it stays above the map
    draw_map()
    draw_panel()
    draw_controls()

    pygame.display.flip()




pygame.quit()