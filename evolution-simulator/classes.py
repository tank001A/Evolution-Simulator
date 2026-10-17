import random
import time

import numpy as np
import pygame


class Tile:
    def __init__(
        self,
        row,
        column,
        tile_type="rock"
    ):
        self.row = row
        self.column = column
        self.tile_type = tile_type

        self.water_content = 0.0
        self.nutrient_content = 0.0

    def add_water(self, amount):
        if amount < 0:
            raise ValueError(
                "Water amount cannot be negative."
            )

        self.water_content += amount

    def remove_water(self, amount):
        if amount < 0:
            raise ValueError(
                "Water amount cannot be negative."
            )

        self.water_content = max(
            0,
            self.water_content - amount
        )

    def add_nutrients(self, amount):
        if amount < 0:
            raise ValueError(
                "Nutrient amount cannot be negative."
            )

        self.nutrient_content += amount

    def remove_nutrients(self, amount):
        if amount < 0:
            raise ValueError(
                "Nutrient amount cannot be negative."
            )

        self.nutrient_content = max(
            0,
            self.nutrient_content - amount
        )

    def get_colour(self):
        if self.tile_type == "rock":
            return 100, 100, 100

        if self.tile_type == "water":
            return 40, 100, 200

        return 255, 0, 255


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
                tile = Tile(
                    row=row,
                    column=column
                )

                current_row.append(tile)

            self.grid.append(current_row)

        self.all_organisms = []
        self.display_changed = True

    def get_elapsed_time(self):
        return time.perf_counter() - self.start_time

    def update(self):
        if self.paused:
            return

        self.simulation_time += 1
        self.update_organisms()
        self.display_changed = True

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
        self.display_changed = True

    def get_tile_at(self, row, column):
        if not (
            0 <= row < self.grid_height
            and 0 <= column < self.grid_width
        ):
            return None

        return self.grid[row][column]

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

    def get_average_water(self):
        total_water = 0.0
        tile_count = 0

        for row in self.grid:
            for tile in row:
                total_water += tile.water_content
                tile_count += 1

        if tile_count == 0:
            return 0.0

        return total_water / tile_count

    def get_total_organism_density(self):
        total_density = 0.0

        for organism in self.all_organisms:
            if hasattr(organism, "density"):
                total_density += organism.density

        return total_density

    def draw(self, surface):
        colour_array = np.zeros(
            (
                self.grid_width,
                self.grid_height,
                3
            ),
            dtype=np.uint8
        )

        for row in self.grid:
            for tile in row:
                colour_array[
                    tile.column,
                    tile.row
                ] = tile.get_colour()

        pygame.surfarray.blit_array(
            surface,
            colour_array
        )

        self.display_changed = False


class RockTile(Tile):
    def __init__(
        self,
        row,
        column
    ):
        super().__init__(
            row=row,
            column=column,
            tile_type="rock"
        )

        self.dust = 0.0

    def add_organic_matter(self, amount):
        self.add_nutrients(amount)

    def update_dust(self, amount):
        if amount < 0:
            raise ValueError(
                "Dust amount cannot be negative."
            )

        self.dust += amount

    def update_soil_water_saturation(self, amount):
        if amount >= 0:
            self.add_water(amount)
        else:
            self.remove_water(-amount)


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
            "Each coloniser must define how it improves a tile."
        )

    def try_spread(self, world):
        return False


class Moss(Coloniser):
    def __init__(
        self,
        organism_position,
        density=500.0,
        mortality_rate=0.05
    ):
        super().__init__(
            organism_position=organism_position,
            tile_requirements={
                "minimum_water": 10.0,
                "minimum_nutrients": 5.0
            }
        )

        if density < 0:
            raise ValueError(
                "Moss density cannot be negative."
            )

        if not 0 <= mortality_rate <= 1:
            raise ValueError(
                "Mortality rate must be between 0 and 1."
            )

        self.density = float(density)
        self.mortality_rate = mortality_rate

    def can_survive_on(self, tile):
        minimum_water = (
            self.tile_requirements["minimum_water"]
        )

        minimum_nutrients = (
            self.tile_requirements["minimum_nutrients"]
        )

        return (
            tile.water_content >= minimum_water
            and
            tile.nutrient_content >= minimum_nutrients
        )

    def consume_resources(self, tile):
        if not self.can_survive_on(tile):
            return False

        water_used = max(
            1.0,
            self.density / 100
        )

        nutrients_used = max(
            1.0,
            self.density / 200
        )

        tile.remove_water(water_used)
        tile.remove_nutrients(nutrients_used)

        return True

    def improve_tile(self, tile):
        organic_mass = (
            self.improve_tile_via_death()
        )

        tile.add_nutrients(organic_mass)

        return organic_mass

    def improve_tile_via_death(self):
        if self.density <= 0:
            self.die()
            return 0.0

        expected_deaths = (
            self.density * self.mortality_rate
        )

        variation = random.uniform(
            0.8,
            1.2
        )

        amount_dead = expected_deaths * variation
        amount_dead = min(
            amount_dead,
            self.density
        )

        self.density -= amount_dead

        organic_mass = amount_dead * 0.5

        if self.density <= 0:
            self.density = 0.0
            self.die()

        return organic_mass

    def update(self, tile, world):
        if self.density <= 0:
            self.die()
            return

        if self.can_survive_on(tile):
            self.consume_resources(tile)
        else:
            self.improve_tile(tile)