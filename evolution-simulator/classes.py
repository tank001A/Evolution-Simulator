import time


class Tile:
    def __init__(
        self,
        row,
        column,
        tile_type="rock",
        water_content=0,
        nutrient_content=5
    ):
        self.row = row
        self.column = column
        self.tile_type = tile_type
        self.water_content = water_content
        self.nutrient_content = nutrient_content

    def get_colour(self):
        if self.tile_type == "rock":
            return 100, 100, 100

        elif self.tile_type == "soil":
            return 120, 80, 40

        elif self.tile_type == "water":
            return 40, 100, 200

        return 255, 0, 255


class World:
    def __init__(
        self,
        name,
        grid_height,
        grid_width,
        simulation_time=0
        #paused = False
    ):
        self.name = name
        self.grid_height = grid_height
        self.grid_width = grid_width
        self.simulation_time = simulation_time
        self.grid = []
        self.paused = False

        self.start_time = time.perf_counter()
        self.simulation_time = simulation_time

        for row in range(grid_height):
            current_row = []

            for column in range(grid_width):
                next_tile = Tile(row, column)
                current_row.append(next_tile)

            self.grid.append(current_row)

    def get_elapsed_time(self):
        return time.perf_counter() - self.start_time

    def update(self):
        if self.paused:
            return
# the timer can continue running, but the simulation itself does not advance while paused
        self.simulation_time += 1

    def pause_world(self):
        self.paused = True


    def continue_world(self):
        self.paused = False

    def fast_forward(self):
        return None

    def draw(self, surface):
        import pygame

        for row in self.grid:
            for tile in row:
                surface.set_at(
                    (tile.column, tile.row),
                    tile.get_colour()
                )




class RockTile(Tile):
    def __init__(
        self,
        row,
        column,
        water_content=0,
        nutrient_content=5
    ):
        super().__init__(
            row=row,
            column=column,
            tile_type="rock",
            water_content=water_content,
            nutrient_content=nutrient_content
        )

        self.dust = 0

    def add_organic_matter(self, amount):
        self.nutrient_content += amount

    def update_dust(self, amount):
        self.dust += amount

    def update_soil_water_saturation(self, amount):
        self.water_content += amount


class WaterTile(Tile):
    def __init__(
        self,
        row,
        column,
        water_content=100,
        nutrient_content=0
    ):
        super().__init__(
            row=row,
            column=column,
            tile_type="water",
            water_content=water_content,
            nutrient_content=nutrient_content
        )


class Organism:
    def __init__(self, organism_position, tile_requirements=None):
        self.organism_position = organism_position
        self.alive = True
        self.tile_requirements = tile_requirements or {}

    def die(self):
        self.alive = False


class Coloniser(Organism):
    def improve_tile(self):
        return None

    def try_spread(self):
        return None