
import time
import random

import pygame

from properties.classes.worldbehavior.class_tile import Tile
from properties.utility_functions import clamp


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

        self.start_time = time.perf_counter()

        self.grid = []

        # Create the tile grid.
        for row in range(grid_height):
            current_row = []

            for column in range(grid_width):
                tile = tile_class(
                    row=row,
                    column=column
                )

                if tile.tile_type != environment_type:
                    raise ValueError(
                        "Tile class does not match the selected environment."
                    )

                if environment_type == "water":
                    tile.nutrient_content = 30.0
                    tile.water_content = 100.0

                current_row.append(tile)

            self.grid.append(current_row)

        self.all_organisms = []

        self.display_changed = True
        self.statistics_changed = True

        # Global weather conditions.
        self.cloud_cover = 40.0
        self.temperature = 18.0

        self.rainfall_amount = 0.0
        self.evaporation_amount = 0.5

        # Weather changes every ten simulation ticks.
        self.weather_update_interval = 3600

        self.cloud_cover_change = 5.0
        self.temperature_change = 1.0

        # Environmental update settings.
        self.environment_update_interval = 5
        self.weathering_rate = 0.02

        self.water_nutrient_input = 0.05

        # Salt model settings.
        self.salt_washout_rate = 0.05
        self.salt_concentration_rate = 0.02

        # Soil acidity model settings.
        self.soil_ph_change_rate = 0.001

        # Initialise light using the starting cloud cover.
        for row in self.grid:
            for tile in row:
                tile.update_light(self.cloud_cover)

        # Cached statistics.
        self.cached_average_water = 0.0
        self.cached_average_soil = 0.0

        # Community development.
        self.community_stage = "Uncolonised"
        self.stable_community_ticks = 0
        self.stability_ticks_required = 200 #change this

    def get_elapsed_time(self):
        return time.perf_counter() - self.start_time

    def update(self):
        if self.paused:
            return

        self.simulation_time += 1

        # Update global weather at set intervals.
        if (
            self.simulation_time
            % self.weather_update_interval
            == 0
        ):
            self.update_weather()

        # Apply the current weather to every tile.
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

    def update_weather(self):
        # Change cloud cover gradually.
        cloud_change = random.uniform(
            -self.cloud_cover_change,
            self.cloud_cover_change
        )

        self.cloud_cover = clamp(
            self.cloud_cover + cloud_change,
            0.0,
            100.0
        )

        # Change temperature gradually.
        temperature_change = random.uniform(
            -self.temperature_change,
            self.temperature_change
        )

        self.temperature = clamp(
            self.temperature + temperature_change,
            -5.0,
            40.0
        )

        # Estimate rainfall using cloud cover.
        self.rainfall_amount = max(
            0.0,
            (self.cloud_cover - 50.0) / 20.0
        )

        # Estimate evaporation using temperature.
        self.evaporation_amount = clamp(
            (self.temperature + 5.0) / 30.0 * 0.5,
            0.05,
            1.0
        )

        # All tiles experience the same light conditions.
        for row in self.grid:
            for tile in row:
                tile.update_light(self.cloud_cover)

    def apply_rainfall(self):
        for row in self.grid:
            for tile in row:
                tile.add_water(
                    self.rainfall_amount
                )

                if self.environment_type == "rock":
                    # Rainfall washes some salt out of the soil.
                    tile.remove_salt(
                        self.rainfall_amount
                        * self.salt_washout_rate
                    )

    def apply_evaporation(self):
        for row in self.grid:
            for tile in row:
                tile.remove_water(
                    self.evaporation_amount
                )

                if self.environment_type == "rock":
                    # Evaporation increases the concentration of salt.
                    tile.add_salt(
                        self.evaporation_amount
                        * self.salt_concentration_rate
                    )

    def update_environment(self):
        for row in self.grid:
            for tile in row:
                if self.environment_type == "water":
                    # Keep the aquatic environment permanently flooded.
                    tile.water_content = 100.0

                    tile.add_nutrients(
                        self.water_nutrient_input
                    )

                else:
                    # Update the rocky environment.
                    tile.weather(
                        self.weathering_rate
                    )

                    tile.develop_soil()

                    tile.update_soil_ph(
                        self.rainfall_amount,
                        self.soil_ph_change_rate
                    )

    def pause_world(self):
        self.paused = True

    def continue_world(self):
        self.paused = False

    def fast_forward(self, number_of_ticks=1):
        if number_of_ticks < 0:
            raise ValueError(
                "Number of ticks cannot be negative."
            )

        for tick in range(number_of_ticks):
            self.update()

    def add_organism(self, organism):
        self.all_organisms.append(organism)

        self.statistics_changed = True
        self.display_changed = True

    def get_tile_at(self, row, column):
        if not (
            0 <= row < self.grid_height
            and 0 <= column < self.grid_width
        ):
            return None

        return self.grid[row][column]

    def get_neighbouring_tiles(self, row, column):
        neighbours = []

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
        # Iterate over a copy because organisms may spread.
        for organism in self.all_organisms[:]:
            if not organism.alive:
                continue

            row, column = organism.organism_position

            tile = self.get_tile_at(
                row,
                column
            )

            if tile is not None:
                organism.update(tile, self)

                if hasattr(organism, "record_biomass"):
                    organism.record_biomass(tile)

        self.all_organisms = [
            organism
            for organism in self.all_organisms
            if organism.alive
        ]

    def update_community_stage(self):
        living = [
            organism
            for organism in self.all_organisms
            if (
                organism.alive
                and getattr(organism, "density", 0) > 0
            )
        ]

        if not living:
            self.community_stage = "Uncolonised"
            self.stable_community_ticks = 0
            return

        occupied_positions = {
            organism.organism_position
            for organism in living
        }

        total_tiles = (
            self.grid_height * self.grid_width
        )

        coverage = (
            len(occupied_positions) / total_tiles
        )

        total_density = sum(
            organism.density
            for organism in living
        )

        total_capacity = sum(
            organism.carrying_capacity
            for organism in living
        )

        if total_capacity > 0:
            population_fill = (
                total_density / total_capacity
            )
        else:
            population_fill = 0.0

        if coverage >= 0.9 and population_fill >= 0.8:
            self.stable_community_ticks += 1
        else:
            self.stable_community_ticks = 0

        if (
            self.stable_community_ticks
            >= self.stability_ticks_required
        ):
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
            self.cached_average_water = (
                total_water / tile_count
            )

            self.cached_average_soil = (
                total_soil / tile_count
            )

        self.statistics_changed = False

    def get_average_water(self):
        return self.cached_average_water

    def get_average_soil_depth(self):
        return self.cached_average_soil

    def get_population_density(self, organism_type):
        total_density = 0

        for organism in self.all_organisms:
            if organism.alive and isinstance(organism, organism_type):
                total_density += organism.density

        return total_density

    def get_visible_bounds(
        self,
        camera_x,
        camera_y,
        zoom,
        viewport_width,
        viewport_height
    ):
        first_column = max(
            0,
            int(camera_x)
        )

        first_row = max(
            0,
            int(camera_y)
        )

        visible_columns = (
            viewport_width // zoom + 2
        )

        visible_rows = (
            viewport_height // zoom + 2
        )

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
        previous_clip = surface.get_clip()
        surface.set_clip(viewport_rect)

        try:
            surface.fill(
                (15, 15, 15),
                viewport_rect
            )

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

                    screen_x = (
                        viewport_rect.x
                        + int((column - camera_x) * zoom)
                    )

                    screen_y = (
                        viewport_rect.y
                        + int((row - camera_y) * zoom)
                    )

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
