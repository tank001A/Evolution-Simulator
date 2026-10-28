import time

import pygame

from properties.classes.worldbehavior.class_tile import Tile


class World:
    def __init__(
        self,
        name,
        grid_height,
        grid_width,
        simulation_time=0,
        environment_type="rock",
        tile_class=Tile
    ):
        # reject an invalid environment before allocating the tile grid
        # this prevents a partly constructed world being used elsewhere
        if environment_type not in ("rock", "water"):
            raise ValueError(
                "Environment must be rock or water."
            )

        if grid_height <= 0 or grid_width <= 0:
            raise ValueError(
                "Grid dimensions must be positive."
            )

        self.name = name
        self.grid_height = grid_height
        self.grid_width = grid_width
        self.simulation_time = simulation_time
        self.environment_type = environment_type
        self.paused = False

        # this measures real elapsed time, including time spent paused
        # simulation_time is separate and counts completed simulation ticks
        self.start_time = time.perf_counter()

        self.grid = []

        # main supplies the selected tile class rather than world importing
        # every habitat type and deciding which one to use itself
        # only the selected environment is allocated in memory
        for row in range(grid_height):
            current_row = []

            for column in range(grid_width):
                tile = tile_class(
                    row=row,
                    column=column
                )

                # both tile classes must accept row and column and expose
                # the same basic tile methods used throughout the world
                if tile.tile_type != environment_type:
                    raise ValueError(
                        "Tile class does not match the selected environment."
                    )

                if environment_type == "water":
                    # assumed starting nutrients for the aquatic env
                    # this is a model setting rather than measured water data
                    tile.nutrient_content = 30.0

                current_row.append(tile)

            self.grid.append(current_row)

        # organisms are stored separately from tiles because their behaviour
        # and population state belong to organism objects
        # tile.species_biomass is a display record of those populations
        self.all_organisms = []

        # retained for future conditional drawing and statistics updates
        # main currently redraws every frame rather than checking these flags
        self.display_changed = True
        self.statistics_changed = True

        # environmental changes are less frequent than organism updates
        # all of these rates are per simulation tick or environment update
        # changing ticks per second therefore changes the real time pace
        self.environment_update_interval = 5
        self.weathering_rate = 0.02
        self.rainfall_amount = 1.0
        self.evaporation_amount = 0.5

        # a small external nutrient supply keeps the aquatic env from
        # stopping solely because its initial nutrients have run out
        # this is not yet a complete nutrient cycling model
        self.water_nutrient_input = 0.05

        # store expensive grid-wide calculations so callers can read them
        # without calculating the average again on every display frame
        self.cached_average_water = 0.0
        self.cached_average_soil = 0.0

        # community state is separate from the soil stage of an individual tile
        # a water environment should not be called mature just because a soil
        # depth threshold has been reached
        self.community_stage = "Uncolonised"
        self.stable_community_ticks = 0

        # require the endpoint conditions for consecutive ticks rather than
        # declaring success from one brief population peak
        self.stability_ticks_required = 200

    def get_elapsed_time(self):
        return time.perf_counter() - self.start_time

    def update(self):
        # also check here so callers other than main cannot advance a paused world
        if self.paused:
            return

        self.simulation_time += 1

        # preserve a consistent update order so the model is easier to test
        # organisms receive this tick's rainfall and evaporation before acting
        self.apply_rainfall()
        self.apply_evaporation()
        self.update_organisms()

        if (
            self.simulation_time
            % self.environment_update_interval
            == 0
        ):
            self.update_environment()

        self.update_community_stage()

        self.statistics_changed = True
        self.display_changed = True

    def apply_rainfall(self):
        for row in self.grid:
            for tile in row:
                tile.add_water(self.rainfall_amount)

    def apply_evaporation(self):
        for row in self.grid:
            for tile in row:
                tile.remove_water(self.evaporation_amount)

    def update_environment(self):
        for row in self.grid:
            for tile in row:
                if self.environment_type == "water":
                    # keep the selected aquatic habitat flooded for the env
                    # rainfall and evaporation can still alter it between updates
                    # water depth and drying ponds need a separate model later
                    tile.water_content = 100.0
                    tile.add_nutrients(self.water_nutrient_input)
                else:
                    # only rocky environments use the current weathering model
                    # applying it to open water would produce misleading soil stages
                    tile.weather(self.weathering_rate)
                    tile.develop_soil()

    def pause_world(self):
        self.paused = True

    def continue_world(self):
        self.paused = False

    def fast_forward(self, number_of_ticks=1):
        if number_of_ticks < 0:
            raise ValueError(
                "Number of ticks cannot be negative."
            )

        # use the normal update path so fast forwarding follows the same rules
        # a paused world deliberately remains paused here too
        for _ in range(number_of_ticks):
            self.update()

    def add_organism(self, organism):
        self.all_organisms.append(organism)

        self.statistics_changed = True
        self.display_changed = True

    def get_tile_at(self, row, column):
        # returning None gives callers a safe way to handle positions at the edge
        # negative indices must be rejected because Python otherwise wraps them
        if not (
            0 <= row < self.grid_height
            and 0 <= column < self.grid_width
        ):
            return None

        return self.grid[row][column]

    def get_neighbouring_tiles(self, row, column):
        neighbours = []

        # use four directly adjacent neighbours rather than diagonals
        # this keeps the current spreading rule consistent across all species
        directions = [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1)
        ]

        for row_change, column_change in directions:
            tile = self.get_tile_at(
                row + row_change,
                column + column_change
            )

            if tile is not None:
                neighbours.append(tile)

        return neighbours

    def update_organisms(self):
        # iterate over a snapshot because spreading adds to all_organisms
        # without a snapshot an offspring could act during its birth tick
        # and potentially create another offspring before the tick finishes
        for organism in self.all_organisms[:]:
            if not organism.alive:
                continue

            row, column = organism.organism_position
            tile = self.get_tile_at(row, column)

            if tile is not None:
                organism.update(tile, self)

                # spreading changes the source density after reproduction
                # record it again so the panel does not show the older value
                # the check leaves room for future organisms without this method
                if hasattr(organism, "record_biomass"):
                    organism.record_biomass(tile)

        self.all_organisms = [
            organism
            for organism in self.all_organisms
            if organism.alive
        ]

    def update_community_stage(self):
        # this detector right now is patiently expecting population-based organisms with
        # density and carrying_capacity, as used by the four colonisers
        living = [
            organism
            for organism in self.all_organisms
            if organism.alive and organism.density > 0
        ]

        if not living:
            self.community_stage = "Uncolonised"
            self.stable_community_ticks = 0
            return

        # a set counts an occupied tile once even if it contains several species
        occupied_positions = {
            organism.organism_position
            for organism in living
        }

        total_tiles = self.grid_height * self.grid_width
        coverage = len(occupied_positions) / total_tiles

        total_density = sum(
            organism.density
            for organism in living
        )

        total_capacity = sum(
            organism.carrying_capacity
            for organism in living
        )

        population_fill = total_density / total_capacity


        # coverage checks spread across the habitat while population_fill
        # checks how established the living populations have become
        if coverage >= 0.9 and population_fill >= 0.8:
            self.stable_community_ticks += 1
        else:
            self.stable_community_ticks = 0

        # the stage can move backwards if populations later decline
        # this is a description of current conditions, not a permanent award
        if self.stable_community_ticks >= self.stability_ticks_required:
            self.community_stage = "Stable community"
        elif coverage >= 0.9:
            self.community_stage = "Establishing community"
        else:
            self.community_stage = "Colonising"

    def update_statistics(self):
        total_water = 0.0
        total_soil = 0.0
        tile_count = 0

        for row in self.grid:
            for tile in row:
                total_water += tile.water_content
                total_soil += tile.soil_depth
                tile_count += 1

        if tile_count > 0:
            self.cached_average_water = total_water / tile_count
            self.cached_average_soil = total_soil / tile_count

        self.statistics_changed = False

    def get_average_water(self):
        return self.cached_average_water

    def get_average_soil_depth(self):
        return self.cached_average_soil

    def get_population_density(self, organism_type):
        # filter by the requested class rather than returning every species
        # isinstance also includes subclasses of the supplied class
        return sum(
            organism.density
            for organism in self.all_organisms
            if (
                organism.alive
                and isinstance(organism, organism_type)
            )
        )

    def get_visible_bounds(
        self,
        camera_x,
        camera_y,
        zoom,
        viewport_width,
        viewport_height
    ):
        # these bounds select what to draw rather than moving the camera
        #  movement limits are handled separately in main
        first_column = max(0, int(camera_x))
        first_row = max(0, int(camera_y))

        # include a small margin for partially visible edge tiles
        # the camera can sit between whole tile positions
        visible_columns = viewport_width // zoom + 2
        visible_rows = viewport_height // zoom + 2

        last_column = min(
            self.grid_width,
            first_column + visible_columns
        )

        last_row = min(
            self.grid_height,
            first_row + visible_rows
        )

        return (
            first_row,
            last_row,
            first_column,
            last_column
        )

    def draw_visible(
        self,
        surface,
        camera_x,
        camera_y,
        zoom,
        viewport_rect,
        selected_position=None
    ):
        # clip drawing to the map so enlarged edge tiles cannot cover the panel
        # restore the previous clip afterwards so main can draw its interface
        previous_clip = surface.get_clip()
        surface.set_clip(viewport_rect)

        try:
            surface.fill((15, 15, 15), viewport_rect)

            (
                first_row,
                last_row,
                first_column,
                last_column
            ) = self.get_visible_bounds(
                camera_x,
                camera_y,
                zoom,
                viewport_rect.width,
                viewport_rect.height
            )

            for row in range(first_row, last_row):
                for column in range(first_column, last_column):
                    tile = self.grid[row][column]

                    # convert world tile coordinates into viewport pixels
                    screen_x = (
                        viewport_rect.x
                        + int((column - camera_x) * zoom)
                    )

                    screen_y = (
                        viewport_rect.y
                        + int((row - camera_y) * zoom)
                    )

                    # slight overlap avoids gaps caused by rounding positions
                    tile_rect = pygame.Rect(
                        screen_x,
                        screen_y,
                        zoom + 1,
                        zoom + 1
                    )

                    pygame.draw.rect(
                        surface,
                        tile.get_colour(),
                        tile_rect
                    )

                    if selected_position == (row, column):
                        pygame.draw.rect(
                            surface,
                            (255, 255, 0),
                            tile_rect,
                            max(1, zoom // 4)
                        )
        finally:
            surface.set_clip(previous_clip)