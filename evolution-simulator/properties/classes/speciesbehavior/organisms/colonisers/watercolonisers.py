import random

from properties.classes.Organisms import Coloniser
from properties.visual_properties import clamp

class WaterColoniser(Coloniser):
    species_name = None
    tile_requirements = None
    water_use_rate = 0.001
    nutrient_use_rate = 0.0005
    spread_threshold = 100.0
    spread_amount = 10.0

    def __init__(
        self,
        organism_position,
        density=100.0,
        carrying_capacity=1000.0,
        growth_rate=0.02,
        mortality_rate=0.05,
    ):
        if self.species_name is None:
            raise TypeError(
                "WaterColoniser is a base class; create a specific "
                "species such as Reeds or  Pytoplankton instead."
            )
        if density < 0:
            raise ValueError("Density cannot be negative.")
        if carrying_capacity <= 0:
            raise ValueError("Carrying capacity must be positive.")
        if not 0 <= growth_rate <= 1:
            raise ValueError("Growth rate must be between 0 and 1.")
        if not 0 <= mortality_rate <= 1:
            raise ValueError("Mortality rate must be between 0 and 1.")
        if density > carrying_capacity:
            raise ValueError("Density cannot exceed carrying capacity.")

        super().__init__(
            organism_position=organism_position,
            tile_requirements=self.tile_requirements,
        )

        self.density = float(density)
        self.carrying_capacity = float(carrying_capacity)
        self.growth_rate = growth_rate
        self.mortality_rate = mortality_rate
        self.health = 1.0


    #def get_suitability(self, tile):
    #    water = clamp(tile.water_content / 100.0, 0.0, 1.0)
    #    nutrients = clamp(tile.nutrient_content / 100.0, 0.0, 1.0)
    #    weathering = clamp(tile.weathering_progress / 10.0, 0.0, 1.0)
    #    return water * nutrients * weathering

    def consume_resources(self, tile):
        tile.remove_water(self.density * self.water_use_rate)
        tile.remove_nutrients(self.density * self.nutrient_use_rate)

    def record_biomass(self, tile):
        tile.species_biomass[self.species_name] = self.density

    def reproduce(self, tile):
        density_ratio = self.density / self.carrying_capacity
        logistic_growth = (
            self.growth_rate
            * self.density
            * (1.0 - density_ratio)
            #* self.get_suitability(tile)
        )
        self.density = min(self.carrying_capacity, self.density + logistic_growth)
        self.record_biomass(tile)
        return logistic_growth

    def improve_tile(self, tile):
        organic_mass = self.improve_tile_via_death()
        tile.add_organic_matter(organic_mass)
        tile.add_nutrients(organic_mass)
        self.record_biomass(tile)
        return organic_mass

    def improve_tile_via_death(self):
        mortality = self.density * self.mortality_rate
        amount_dead = min(self.density, mortality * random.uniform(0.8, 1.2))
        self.density -= amount_dead
        if self.density <= 0:
            self.density = 0.0
            self.die()
        return amount_dead * 0.01

    def receive(self, amount):
        accepted = clamp(amount, 0.0, self.carrying_capacity - self.density)
        self.density += accepted
        return accepted


    def spawn_offspring(self, position):

        return type(self)(
            organism_position=position,
            density=self.spread_amount,
            carrying_capacity=self.carrying_capacity,
            growth_rate=self.growth_rate,
            mortality_rate=self.mortality_rate,
        )

    def find_same_species_at(self, world, position):
        for organism in world.all_organisms:
            if (
                isinstance(organism, type(self))
                and organism.alive
                and organism.organism_position == position
            ):
                return organism
        return None

    def try_spread(self, world):
        if self.density < self.spread_threshold:
            return False

        row, column = self.organism_position
        suitable_tiles = [
            tile
            for tile in world.get_neighbouring_tiles(row, column)
            if self.can_survive_on(tile)
        ]
        if not suitable_tiles:
            return False

        target_tile = random.choice(suitable_tiles)
        target_position = (target_tile.row, target_tile.column)

        neighbour = self.find_same_species_at(world, target_position)
        if neighbour is not None:
            transferred = neighbour.receive(min(self.spread_amount, self.density))
            self.density -= transferred
            neighbour.record_biomass(target_tile)
            return transferred > 0

        offspring = self.spawn_offspring(target_position)
        world.add_organism(offspring)
        offspring.record_biomass(target_tile)
        self.density -= offspring.density
        return True

    def update(self, tile, world):
        if self.density <= 0:
            self.die()
            return

        if self.can_survive_on(tile):
            self.health = min(1.0, self.health + 0.01)
            self.consume_resources(tile)
            self.reproduce(tile)
            if random.random() < 0.05:
                self.try_spread(world)
        else:
            self.health -= 0.05
            if self.health <= 0:
                self.improve_tile(tile)


class Reeds(WaterColoniser):
    species_name = "Reeds"
    tile_requirements = {
        "minimum_water": 10.0,
        "minimum_nutrients": 5.0,
    }


class Pytoplankton(WaterColoniser):
    species_name = "Pytoplankton"
    tile_requirements = {
        "minimum_water": 10.0,
        "minimum_nutrients": 5.0,
    }
    nutrient_use_rate = 0.005