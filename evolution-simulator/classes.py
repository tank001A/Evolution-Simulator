import random
import time

import numpy as np
import pygame


ROCK_PROPERTIES = {
    "granite": {
        "ucs_mpa": 175.0,
        "weathering_factor": 0.8
    },
    "basalt": {
        "ucs_mpa": 200.0,
        "weathering_factor": 0.7
    },
    "sandstone": {
        "ucs_mpa": 80.0,
        "weathering_factor": 1.2
    },
    "limestone": {
        "ucs_mpa": 100.0,
        "weathering_factor": 1.3
    },
    "shale": {
        "ucs_mpa": 50.0,
        "weathering_factor": 1.8
    }
}


def clamp(value, minimum, maximum):
    return min(
        maximum,
        max(minimum, value)
    )


class Tile:
    def __init__(
        self,
        row,
        column,
        tile_type="rock",
        lithology="granite"
    ):
        self.row = row
        self.column = column
        self.tile_type = tile_type

        self.water_content = 0.0
        self.nutrient_content = 0.0
        self.organic_matter = 0.0

        self.weathering_progress = 0.0
        self.soil_depth = 0.0

        self.lithology = None
        self.ucs_mpa = None
        self.weathering_factor = None

        self.species_biomass = {}

        self.set_lithology(lithology)

    def set_lithology(self, lithology):
        if lithology not in ROCK_PROPERTIES:
            raise ValueError(
                f"Unknown lithology: {lithology}"
            )

        self.lithology = lithology

        self.ucs_mpa = (
            ROCK_PROPERTIES[lithology]["ucs_mpa"]
        )

        self.weathering_factor = (
            ROCK_PROPERTIES[lithology]
            ["weathering_factor"]
        )

    def add_species_biomass(
        self,
        species_name,
        amount
    ):
        if amount < 0:
            raise ValueError(
                "Biomass amount cannot be negative."
            )

        current_amount = (
            self.species_biomass.get(
                species_name,
                0.0
            )
        )

        self.species_biomass[species_name] = (
            current_amount + amount
        )

    def remove_species_biomass(
        self,
        species_name,
        amount
    ):
        if amount < 0:
            raise ValueError(
                "Biomass amount cannot be negative."
            )

        current_amount = (
            self.species_biomass.get(
                species_name,
                0.0
            )
        )

        remaining_amount = max(
            0.0,
            current_amount - amount
        )

        self.species_biomass[species_name] = (
            remaining_amount
        )

    def get_species_biomass(self, species_name):
        return self.species_biomass.get(
            species_name,
            0.0
        )

    def get_total_biomass(self):
        return sum(
            self.species_biomass.values()
        )

    def add_water(self, amount):
        if amount < 0:
            raise ValueError(
                "Water amount cannot be negative."
            )

        self.water_content = clamp(
            self.water_content + amount,
            0.0,
            100.0
        )

    def remove_water(self, amount):
        if amount < 0:
            raise ValueError(
                "Water amount cannot be negative."
            )

        self.water_content = clamp(
            self.water_content - amount,
            0.0,
            100.0
        )

    def add_nutrients(self, amount):
        if amount < 0:
            raise ValueError(
                "Nutrient amount cannot be negative."
            )

        self.nutrient_content = clamp(
            self.nutrient_content + amount,
            0.0,
            100.0
        )

    def remove_nutrients(self, amount):
        if amount < 0:
            raise ValueError(
                "Nutrient amount cannot be negative."
            )

        self.nutrient_content = clamp(
            self.nutrient_content - amount,
            0.0,
            100.0
        )

    def add_organic_matter(self, amount):
        if amount < 0:
            raise ValueError(
                "Organic matter amount cannot be negative."
            )

        self.organic_matter = clamp(
            self.organic_matter + amount,
            0.0,
            100.0
        )

    def get_water_suitability(self):
        return clamp(
            self.water_content / 100.0,
            0.0,
            1.0
        )

    def get_nutrient_suitability(self):
        return clamp(
            self.nutrient_content / 100.0,
            0.0,
            1.0
        )

    def weather(self, weathering_rate=0.02):
        water_suitability = (
            self.get_water_suitability()
        )

        organic_multiplier = (
            1.0
            + self.organic_matter / 100.0
        )

        weathering_change = (
            weathering_rate
            * self.weathering_factor
            * water_suitability
            * organic_multiplier
        )

        self.weathering_progress = clamp(
            self.weathering_progress
            + weathering_change,
            0.0,
            100.0
        )

    def develop_soil(
        self,
        soil_conversion_rate=0.02
    ):
        organic_contribution = (
            self.organic_matter
            * soil_conversion_rate
        )

        mineral_contribution = (
            self.weathering_progress
            * 0.005
        )

        soil_change = (
            organic_contribution
            + mineral_contribution
        )

        self.soil_depth = clamp(
            self.soil_depth + soil_change,
            0.0,
            100.0
        )

        self.organic_matter = clamp(
            self.organic_matter
            - organic_contribution,
            0.0,
            100.0
        )

        self.add_nutrients(
            soil_change * 0.1
        )

    def get_succession_stage(self):
        if self.soil_depth < 5.0:
            return "Bare rock"

        if self.soil_depth < 20.0:
            return "Pioneer"

        if self.soil_depth < 50.0:
            return "Early soil"

        if self.soil_depth < 80.0:
            return "Developing soil"

        return "Mature soil"

    def get_colour(self):
        if self.tile_type == "water":
            return 40, 100, 200

        if self.soil_depth >= 50.0:
            return 80, 120, 50

        if self.soil_depth >= 20.0:
            return 110, 100, 55

        weathering_ratio = (
            self.weathering_progress / 100.0
        )

        red = int(
            100 + 35 * weathering_ratio
        )

        green = int(
            100 + 20 * weathering_ratio
        )

        blue = int(
            100 - 35 * weathering_ratio
        )

        return red, green, blue


class World:
    def __init__(
        self,
        name,
        grid_height,
        grid_width,
        simulation_time=0
    ):
        self.name = name
        self.grid_height = grid_height
        self.grid_width = grid_width
        self.simulation_time = simulation_time
        self.paused = False

        self.start_time = time.perf_counter()

        self.grid = []

        for row in range(grid_height):
            current_row = []

            for column in range(grid_width):
                current_row.append(
                    Tile(
                        row=row,
                        column=column
                    )
                )

            self.grid.append(current_row)

        self.all_organisms = []

        self.display_changed = True
        self.statistics_changed = True

        self.environment_update_interval = 5
        self.weathering_rate = 0.02
        self.rainfall_amount = 1.0
        self.evaporation_amount = 0.5

        self.cached_average_water = 0.0
        self.cached_average_soil = 0.0

    def get_elapsed_time(self):
        return (
            time.perf_counter()
            - self.start_time
        )

    def update(self):
        if self.paused:
            return

        self.simulation_time += 1

        self.apply_rainfall()
        self.apply_evaporation()
        self.update_organisms()

        if (
            self.simulation_time
            % self.environment_update_interval
            == 0
        ):
            self.update_environment()

        self.statistics_changed = True
        self.display_changed = True

    def apply_rainfall(self):
        for row in self.grid:
            for tile in row:
                tile.add_water(
                    self.rainfall_amount
                )

    def apply_evaporation(self):
        for row in self.grid:
            for tile in row:
                tile.remove_water(
                    self.evaporation_amount
                )

    def update_environment(self):
        for row in self.grid:
            for tile in row:
                tile.weather(
                    self.weathering_rate
                )

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

        for _ in range(number_of_ticks):
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
        for organism in self.all_organisms:
            if not organism.alive:
                continue

            row, column = organism.organism_position

            tile = self.get_tile_at(
                row,
                column
            )

            if tile is not None:
                organism.update(
                    tile,
                    self
                )

        self.all_organisms = [
            organism
            for organism in self.all_organisms
            if organism.alive
        ]

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
        total_density = 0.0

        for organism in self.all_organisms:
            if (
                isinstance(organism, organism_type)
                and organism.alive
            ):
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
            viewport_width // zoom
        ) + 2

        visible_rows = (
            viewport_height // zoom
        ) + 2

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
        surface.fill(
            (15, 15, 15)
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
            for column in range(
                first_column,
                last_column
            ):
                tile = self.grid[row][column]

                screen_x = (
                    viewport_rect.x
                    + int(
                        (column - camera_x)
                        * zoom
                    )
                )

                screen_y = (
                    viewport_rect.y
                    + int(
                        (row - camera_y)
                        * zoom
                    )
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

                if (
                    selected_position
                    == (row, column)
                ):
                    pygame.draw.rect(
                        surface,
                        (255, 255, 0),
                        tile_rect,
                        max(1, zoom // 4)
                    )


class RockTile(Tile):
    def __init__(
        self,
        row,
        column,
        lithology="granite"
    ):
        super().__init__(
            row=row,
            column=column,
            tile_type="rock",
            lithology=lithology
        )

        self.dust = 0.0

    def update_dust(self, amount):
        if amount < 0:
            raise ValueError(
                "Dust amount cannot be negative."
            )

        self.dust += amount


class WaterTile(Tile):
    def __init__(
        self,
        row,
        column
    ):
        super().__init__(
            row=row,
            column=column,
            tile_type="water"
        )

        self.water_content = 100.0

    def get_colour(self):
        return 40, 100, 200


class Organism:
    def __init__(
        self,
        organism_position,
        tile_requirements=None
    ):
        self.organism_position = organism_position
        self.alive = True

        self.tile_requirements = (
            tile_requirements
            if tile_requirements is not None
            else {}
        )

    def die(self):
        self.alive = False

    def update(self, tile, world):
        raise NotImplementedError(
            "Each organism must define its own update method."
        )


class Coloniser(Organism):
    def improve_tile(self, tile):
        raise NotImplementedError(
            "Each coloniser must define its own tile effect."
        )

    def try_spread(self, world):
        return False


class Moss(Coloniser):
    def __init__(
        self,
        organism_position,
        density=100.0,
        carrying_capacity=1000.0,
        growth_rate=0.02,
        mortality_rate=0.05
    ):
        super().__init__(
            organism_position=organism_position,
            tile_requirements={
                "minimum_water": 10.0,
                "minimum_nutrients": 5.0,
                "minimum_weathering": 0.1
            }
        )

        if density < 0:
            raise ValueError(
                "Density cannot be negative."
            )

        if carrying_capacity <= 0:
            raise ValueError(
                "Carrying capacity must be positive."
            )

        if not 0 <= growth_rate <= 1:
            raise ValueError(
                "Growth rate must be between 0 and 1."
            )

        if not 0 <= mortality_rate <= 1:
            raise ValueError(
                "Mortality rate must be between 0 and 1."
            )

        if density > carrying_capacity:
            raise ValueError(
                "Density cannot exceed carrying capacity."
            )

        self.density = float(density)
        self.carrying_capacity = float(
            carrying_capacity
        )
        self.growth_rate = growth_rate
        self.mortality_rate = mortality_rate

        self.health = 1.0

        self.species_name = "Moss"

    def can_survive_on(self, tile):
        return (
            tile.water_content
            >= self.tile_requirements
            ["minimum_water"]
            and
            tile.nutrient_content
            >= self.tile_requirements
            ["minimum_nutrients"]
            and
            tile.weathering_progress
            >= self.tile_requirements
            ["minimum_weathering"]
        )

    def get_suitability(self, tile):
        water_suitability = clamp(
            tile.water_content / 100.0,
            0.0,
            1.0
        )

        nutrient_suitability = clamp(
            tile.nutrient_content / 100.0,
            0.0,
            1.0
        )

        weathering_suitability = clamp(
            tile.weathering_progress / 10.0,
            0.0,
            1.0
        )

        return (
            water_suitability
            * nutrient_suitability
            * weathering_suitability
        )

    def consume_resources(self, tile):
        water_used = (
            self.density * 0.001
        )

        nutrients_used = (
            self.density * 0.0005
        )

        tile.remove_water(
            water_used
        )

        tile.remove_nutrients(
            nutrients_used
        )

    def reproduce(self, tile):
        suitability = (
            self.get_suitability(tile)
        )

        density_ratio = (
            self.density
            / self.carrying_capacity
        )

        logistic_growth = (
            self.growth_rate
            * self.density
            * (1.0 - density_ratio)
            * suitability
        )

        self.density = min(
            self.carrying_capacity,
            self.density + logistic_growth
        )

        tile.species_biomass[
            self.species_name
        ] = self.density

        return logistic_growth

    def improve_tile(self, tile):
        organic_mass = (
            self.improve_tile_via_death()
        )

        tile.add_organic_matter(
            organic_mass
        )

        tile.add_nutrients(
            organic_mass
        )

        tile.species_biomass[
            self.species_name
        ] = self.density

        return organic_mass

    def improve_tile_via_death(self):
        mortality = (
            self.density
            * self.mortality_rate
        )

        variation = random.uniform(
            0.8,
            1.2
        )

        amount_dead = min(
            self.density,
            mortality * variation
        )

        self.density -= amount_dead

        if self.density <= 0:
            self.density = 0.0
            self.die()

        return amount_dead * 0.01

    def try_spread(self, world):
        if self.density < 100.0:
            return False

        row, column = self.organism_position

        suitable_tiles = [
            tile
            for tile in world.get_neighbouring_tiles(
                row,
                column
            )
            if self.can_survive_on(tile)
        ]

        if not suitable_tiles:
            return False

        target_tile = random.choice(
            suitable_tiles
        )

        target_position = (
            target_tile.row,
            target_tile.column
        )

        for organism in world.all_organisms:
            if (
                isinstance(organism, Moss)
                and
                organism.organism_position
                == target_position
            ):
                transfer = min(
                    10.0,
                    self.density
                )

                available_capacity = (
                    organism.carrying_capacity
                    - organism.density
                )

                transfer = min(
                    transfer,
                    available_capacity
                )

                organism.density += transfer
                self.density -= transfer

                target_tile.species_biomass[
                    "Moss"
                ] = organism.density

                return transfer > 0

        new_moss = Moss(
            organism_position=target_position,
            density=10.0,
            carrying_capacity=self.carrying_capacity,
            growth_rate=self.growth_rate,
            mortality_rate=self.mortality_rate
        )

        world.add_organism(new_moss)

        target_tile.species_biomass[
            "Moss"
        ] = new_moss.density

        self.density -= 10.0

        return True

    def update(self, tile, world):
        if self.density <= 0:
            self.die()
            return

        if self.can_survive_on(tile):
            self.health = min(
                1.0,
                self.health + 0.01
            )

            self.consume_resources(tile)
            self.reproduce(tile)

            if random.random() < 0.05:
                self.try_spread(world)
        else:
            self.health -= 0.05

            if self.health <= 0:
                self.improve_tile(tile)