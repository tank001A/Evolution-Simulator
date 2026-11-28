
from properties.classes.Organisms import Organism


class PlantPopulation(Organism):

    def __init__(
        self,
        species,
        organism_position,
        density=1.0,
        carrying_capacity=100.0,
        growth_rate=0.02,
        mortality_rate=0.01
    ):
        super().__init__(organism_position)

        if density < 0:
            raise ValueError("Population density cannot be negative.")

        if carrying_capacity <= 0:
            raise ValueError("Carrying capacity must be positive.")

        if growth_rate < 0 or mortality_rate < 0:
            raise ValueError("Growth and mortality rates cannot be negative.")

        self.species = species
        self.species_name = species.name

        self.density = density
        self.carrying_capacity = carrying_capacity

        self.growth_rate = growth_rate
        self.mortality_rate = mortality_rate

        self.health = 1.0
        self.alive = True

    def record_biomass(self, tile):
        if self.alive and self.density > 0:
            tile.species_biomass[self.species_name] = self.density
        else:
            tile.species_biomass.pop(self.species_name, None)

    def update(self, tile, world):
        #do population dynamics later
        #for now, the population keeps its first density.
        pass
