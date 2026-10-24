import time
import pygame

from properties.classes.worldbehavior.class_tile import *

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
        #grid holding all of the tiles:
        self.grid = []
        #Creates tile objects for the grid.
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
        #list for all organisms
        self.all_organisms = []
        self.display_changed = True
        self.statistics_changed = True

        #these values are assumed.
        self.environment_update_interval = 5
        self.weathering_rate = 0.02
        self.rainfall_amount = 1.0
        self.evaporation_amount = 0.5
        #these stpre calculated average values so the program does not need to recalculate them every frame, which heightens performance.
        self.cached_average_water = 0.0
        self.cached_average_soil = 0.0

    def get_elapsed_time(self):
        return (
            time.perf_counter()
            - self.start_time
        )

    def update(self):
        '''
        Does one simulation update, and applies various environmental affects like rainfall and evaporation.
        '''
        if self.paused:
            return

        self.simulation_time += 1

        self.apply_rainfall()
        self.apply_evaporation()
        self.update_organisms()

        # this checks if 5 ticks have passed. Every 5 ticks, the environment is updated.
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

        for i in range(number_of_ticks):
            self.update()

    def add_organism(self, organism):
        '''
        adds organisms into the world.
        '''
        self.all_organisms.append(organism)
        #keeps track of the fact that both the statistics and the display has changed, so next update the program considers this.
        self.statistics_changed = True
        self.display_changed = True

    #methods get_tile_at, get_neighboring_tiles are for the location of tile positions.
    #Significant for both applying effects, and the "selection" of specific tiles.


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

        #updates list of all the organisms, adding only the organisms that are still alive.
        self.all_organisms = [
            organism
            for organism in self.all_organisms
            if organism.alive
        ]

    def update_statistics(self):
        '''
        Updates all statistics shown on home screen globally, referring to the total of something.
        '''
        total_water = 0.0
        total_soil = 0.0
        tile_count = 0

        #For every individual tile updates average water and soil.
        for row in self.grid:
            for tile in row:
                total_water += tile.water_content
                total_soil += tile.soil_depth
                tile_count += 1

        # this section is averages for all the tiles.
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

        #Increases organism density by a certain amount.
        for organism in self.all_organisms:
            if (
                organism.alive
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

        """
        Sets constraints for the camera, so the user doesn't pan too far away
        """
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