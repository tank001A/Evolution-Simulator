import random

from properties.utility_functions import *


class Organism:
    def __init__(self, organism_position, tile_requirements=None):
        self.organism_position = organism_position
        self.alive = True

        self.tile_requirements = (
            dict(tile_requirements) if tile_requirements is not None else {}
        )

    def die(self):
        self.alive = False

    def can_survive_on(self, tile):
        requirements = self.tile_requirements
        return (
                tile.water_content >= requirements.get("minimum_water", 0.0)
                and tile.nutrient_content >= requirements.get("minimum_nutrients", 0.0)
                and tile.weathering_progress >= requirements.get("minimum_weathering", 0.0)
        )


class Coloniser(Organism):
    # organism's __init__ is inherited

    def improve_tile(self, tile):
        pass

    def try_spread(self, world):
        pass




