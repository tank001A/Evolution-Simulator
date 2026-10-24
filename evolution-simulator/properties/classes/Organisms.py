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



class Lichen(Coloniser):
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

        self.species_name = "Lichen"

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
                self.density * 0.005
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
                    "Lichen"
                ] = organism.density

                return transfer > 0

        new_lichen = Lichen(
            organism_position=target_position,
            density=10.0,
            carrying_capacity=self.carrying_capacity,
            growth_rate=self.growth_rate,
            mortality_rate=self.mortality_rate
        )

        world.add_organism(new_lichen)

        target_tile.species_biomass[
            "Lichen"
        ] = new_lichen.density

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
