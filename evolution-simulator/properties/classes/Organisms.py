import random

from properties.visual_properties import *


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
            #if tile_requirements is not None
            #else {}
        )

    def die(self):
        self.alive = False

    def update(self, tile, world):
        raise NotImplementedError(
            "Each organism must define its own update method."
        )


class Coloniser(Organism):
    def __init__(
        self,
        organism_position,
        tile_requirements=None
    ):
        super().__init__(
        organism_position=organism_position,
        tile_requirements=tile_requirements
    )

    def improve_tile(self, tile):
        raise NotImplementedError(
            "Each coloniser must define its own tile effect."
        )



    def try_spread(self, world):
        return False



