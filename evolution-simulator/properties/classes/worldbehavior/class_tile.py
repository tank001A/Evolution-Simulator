from properties.rock_properties import *
from properties.visual_properties import *

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
#



        self.lithology = None
        self.ucs_mpa = None
        self.weathering_factor = None
        #empty dictionary for species populations
        #dictionary {species_name: total biomass on that tile}
        self.species_biomass = {}
        self.set_lithology(lithology)

    # fills in the correct UCS value and weathering factor, depending on the rock type.
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
        #finds the species current biomass; if this species isnt there default to 0.0
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

        # finds the species current biomass; if this species isnt there default to 0.0
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
        #amount is defined via formula
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
    #normalising values for 0-100 to 0-1 based on water suitability for that tile, for native species
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
    #default weathering rate is assumed to be 2%
    def weather(self, weathering_rate=0.02):
        water_suitability = (
            self.get_water_suitability()
        )


        #speeds up weathering rate based on organic matter
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
    #conversion rate is assumed to be 2%
    def develop_soil(
        self,
        soil_conversion_rate=0.02
    ):
        """
        a method to turn weathered rock and organic matter into soil.
        contribution to the soil dependent on numerous factors.
        """
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

        """
        describes a tiles state of ecological development, from 0-100%
        """

        if 0 < self.soil_depth < 5.0:
            return "Bare rock"

        if 5.0 < self.soil_depth < 20.0:
            return "Pioneer"

        if 20.0 < self.soil_depth < 50.0:
            return "Early soil"

        if 50.0 < self.soil_depth < 80.0:
            return "Developing soil"

        return "Mature soil"

    def get_colour(self):

        """
        assigns the tile a color depending on its environmental conditions. As weathering increases, the tile becomes more reddish, and less blue.
        """

        if self.tile_type == "water":
            return 40, 100, 200

        if self.soil_depth >= 50.0:
            return 80, 120, 50

        if self.soil_depth >= 20.0:
            return 110, 100, 55


        #changes weathering from 0-100 to 0-1, dependent on progress
        #perhaps normalise it from the get-go. Dont wanna do extra work for no reason, since you might as well normalise initially.
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