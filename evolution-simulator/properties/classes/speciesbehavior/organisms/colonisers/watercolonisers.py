import random

from properties.classes.Organisms import Coloniser
from properties.utility_functions import clamp


class WaterColoniser(Coloniser):
    species_name = None
    tile_requirements = None

    # these are assumed simulation values, not measured species data
    nutrient_use_rate = 0.00001
    spread_threshold = 100.0
    spread_amount = 10.0

    def __init__(
        self,
        organism_position,
        density=100.0,
        carrying_capacity=1000.0,
        growth_rate=0.02,
        mortality_rate=0.05
    ):
        if self.species_name is None:
            raise TypeError(
                "create a water species such as Reeds or Phytoplankton"
            )

        if density < 0:
            raise ValueError("Density cannot be negative.")

        if carrying_capacity <= 0:
            raise ValueError("Carrying capacity must be positive.")

        if density > carrying_capacity:
            raise ValueError("Density cannot exceed carrying capacity.")

        if not 0 <= growth_rate <= 1:
            raise ValueError("Growth rate must be between 0 and 1.")

        if not 0 <= mortality_rate <= 1:
            raise ValueError("Mortality rate must be between 0 and 1.")

        super().__init__(
            organism_position=organism_position,
            tile_requirements=self.tile_requirements
        )

        self.density = float(density)
        self.carrying_capacity = float(carrying_capacity)
        self.growth_rate = growth_rate
        self.mortality_rate = mortality_rate
        self.health = 1.0

    def can_survive_on(self, tile):
        # enough water on a rock tile should not turn it into a water habitat
        return (
            tile.tile_type == "water"
            and super().can_survive_on(tile)
        )

    def get_suitability(self, tile):
        # aquatic growth does not depend on rock weathering
        water = clamp(tile.water_content / 100.0, 0.0, 1.0)
        nutrients = clamp(tile.nutrient_content / 100.0, 0.0, 1.0)

        return water * nutrients

    def consume_resources(self, tile):
        # water is maintained as the habitat rather than used up as a stock
        # this MVP only removes nutrients from the water
        tile.remove_nutrients(
            self.density * self.nutrient_use_rate
        )

    def record_biomass(self, tile):
        tile.species_biomass[self.species_name] = self.density

    def reproduce(self, tile):
        density_ratio = self.density / self.carrying_capacity

        growth = (
            self.growth_rate
            * self.density
            * (1.0 - density_ratio)
            * self.get_suitability(tile)
        )

        self.density = min(
            self.carrying_capacity,
            self.density + growth
        )

        self.record_biomass(tile)
        return growth

    def improve_tile_via_death(self):
        mortality = self.density * self.mortality_rate

        amount_dead = min(
            self.density,
            mortality * random.uniform(0.8, 1.2)
        )

        self.density -= amount_dead

        if self.density <= 0:
            self.density = 0.0
            self.die()

        return amount_dead * 0.01

    def improve_tile(self, tile):
        organic_mass = self.improve_tile_via_death()

        tile.add_organic_matter(organic_mass)
        tile.add_nutrients(organic_mass)
        self.record_biomass(tile)

        return organic_mass

    def receive(self, amount):
        available_capacity = max(
            0.0,
            self.carrying_capacity - self.density
        )

        accepted = clamp(amount, 0.0, available_capacity)
        self.density += accepted

        return accepted

    def spawn_offspring(self, position, density):
        # type(self) creates the same species as the parent
        return type(self)(
            organism_position=position,
            density=density,
            carrying_capacity=self.carrying_capacity,
            growth_rate=self.growth_rate,
            mortality_rate=self.mortality_rate
        )

    def find_same_species_at(self, world, position):
        for organism in world.all_organisms:
            if (
                type(organism) is type(self)
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

        neighbour = self.find_same_species_at(
            world,
            target_position
        )

        # limit transfers so a new population cannot exceed its capacity
        amount = min(
            self.spread_amount,
            self.density,
            self.carrying_capacity
        )

        if neighbour is not None:
            transferred = neighbour.receive(amount)
            neighbour.record_biomass(target_tile)
        else:
            offspring = self.spawn_offspring(
                target_position,
                amount
            )

            world.add_organism(offspring)
            offspring.record_biomass(target_tile)
            transferred = offspring.density

        self.density -= transferred

        # the source tile must also show the population lost through spreading
        source_tile = world.get_tile_at(row, column)

        if source_tile is not None:
            self.record_biomass(source_tile)

        return transferred > 0

    def update(self, tile, world):
        if self.density <= 0:
            self.density = 0.0
            self.record_biomass(tile)
            self.die()
            return

        if self.can_survive_on(tile):
            self.health = min(1.0, self.health + 0.01)

            self.consume_resources(tile)
            self.reproduce(tile)

            if random.random() < 0.05:
                self.try_spread(world)
        else:
            self.health = max(0.0, self.health - 0.05)

            if self.health <= 0:
                self.improve_tile(tile)


class Reeds(WaterColoniser):
    species_name = "Reeds"

    tile_requirements = {
        "minimum_water": 70.0,
        "minimum_nutrients": 5.0
    }


class Phytoplankton(WaterColoniser):
    species_name = "Phytoplankton"

    tile_requirements = {
        "minimum_water": 80.0,
        "minimum_nutrients": 5.0
    }