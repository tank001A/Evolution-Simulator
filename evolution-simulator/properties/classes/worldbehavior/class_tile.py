
from properties.rock_properties import ROCK_PROPERTIES
from properties.utility_functions import clamp


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

        # Environmental resources
        self.water_content = 0.0
        self.nutrient_content = 0.0
        self.organic_matter = 0.0

        # Soil and weathering properties
        self.weathering_progress = 0.0
        self.soil_depth = 0.0
        self.soil_ph = 6.5

        # Environmental properties used for plant suitability
        self.light_level = 100.0
        self.salt_level = 0.0

        self.lithology = None
        self.ucs_mpa = None
        self.weathering_factor = None

        # Stores the total biomass of each species on this tile.
        self.species_biomass = {}

        self.set_lithology(lithology)

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
            ROCK_PROPERTIES[lithology]["weathering_factor"]
        )

    def update_light(self, cloud_cover):
        if not 0.0 <= cloud_cover <= 100.0:
            raise ValueError(
                "Cloud cover must be between 0 and 100."
            )

        # More cloud cover means less available light.
        self.light_level = 100.0 - cloud_cover

    def add_salt(self, amount):
        if amount < 0:
            raise ValueError(
                "Salt amount cannot be negative."
            )

        self.salt_level = clamp(
            self.salt_level + amount,
            0.0,
            100.0
        )

    def remove_salt(self, amount):
        if amount < 0:
            raise ValueError(
                "Salt amount cannot be negative."
            )

        self.salt_level = clamp(
            self.salt_level - amount,
            0.0,
            100.0
        )

    def set_soil_ph(self, value):
        if not 0.0 <= value <= 14.0:
            raise ValueError(
                "Soil pH must be between 0 and 14."
            )

        self.soil_ph = value

    def update_soil_ph(
        self,
        rainfall_amount,
        ph_change_rate=0.001
    ):
        if rainfall_amount < 0:
            raise ValueError(
                "Rainfall cannot be negative."
            )

        if ph_change_rate < 0:
            raise ValueError(
                "pH change rate cannot be negative."
            )

        # Rainfall and organic matter contribute to acidification.
        acidification = (
            rainfall_amount * ph_change_rate
            + self.organic_matter * ph_change_rate * 0.01
        )

        # Weathering of minerals provides some buffering.
        mineral_buffering = (
            self.weathering_factor
            * ph_change_rate
            * 0.25
        )

        ph_change = (
            mineral_buffering - acidification
        )

        self.soil_ph = clamp(
            self.soil_ph + ph_change,
            3.5,
            8.5
        )

    def get_soil_fertility(self):
        # These weights are initial model assumptions.
        fertility = (
            self.nutrient_content * 0.6
            + self.organic_matter * 0.25
            + self.soil_depth * 0.15
        )

        return clamp(
            fertility,
            0.0,
            100.0
        )

    def get_plant_environment(self):
        # Returns actual simulation measurements.
        return {
            "light": self.light_level,
            "moisture": self.water_content,
            "soil_acidity": self.soil_ph,
            "soil_fertility": self.get_soil_fertility(),
            "salt": self.salt_level
        }

    def convert_to_indicator(
        self,
        value,
        source_min,
        source_max,
        indicator_min,
        indicator_max
    ):
        # Converts a measurement into an estimated indicator value.
        value = clamp(
            value,
            source_min,
            source_max
        )

        proportion = (
            (value - source_min)
            / (source_max - source_min)
        )

        return (
            indicator_min
            + proportion * (indicator_max - indicator_min)
        )

    def get_plant_indicator_values(self):
        # These conversions are simplified assumptions.
        # They are not experimentally calibrated relationships.

        indicators = {
            # Light: L scale 1-9.
            "light": self.convert_to_indicator(
                self.light_level,
                0.0,
                100.0,
                1.0,
                9.0
            ),

            # Moisture: F scale 1-12.
            "moisture": self.convert_to_indicator(
                self.water_content,
                0.0,
                100.0,
                1.0,
                12.0
            ),

            # Soil reaction: R scale 1-9.
            # The model uses pH 3.5-8.5 as its conversion range.
            "soil_acidity": self.convert_to_indicator(
                self.soil_ph,
                3.5,
                8.5,
                1.0,
                9.0
            ),

            # Fertility: N scale 1-9.
            "soil_fertility": self.convert_to_indicator(
                self.get_soil_fertility(),
                0.0,
                100.0,
                1.0,
                9.0
            ),

            # Salinity: S scale 0-9.
            "salt": self.convert_to_indicator(
                self.salt_level,
                0.0,
                100.0,
                0.0,
                9.0
            )
        }

        return indicators

    def add_species_biomass(
        self,
        species_name,
        amount
    ):
        if amount < 0:
            raise ValueError(
                "Biomass amount cannot be negative."
            )

        current_amount = self.species_biomass.get(
            species_name,
            0.0
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

        current_amount = self.species_biomass.get(
            species_name,
            0.0
        )

        remaining_amount = max(
            0.0,
            current_amount - amount
        )

        if remaining_amount == 0.0:
            self.species_biomass.pop(
                species_name,
                None
            )
        else:
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

    def weather(self, weathering_rate=0.02):
        water_suitability = (
            self.get_water_suitability()
        )

        organic_multiplier = (
            1.0 + self.organic_matter / 100.0
        )

        weathering_change = (
            weathering_rate
            * self.weathering_factor
            * water_suitability
            * organic_multiplier
        )

        self.weathering_progress = clamp(
            self.weathering_progress + weathering_change,
            0.0,
            100.0
        )

    def develop_soil(self, soil_conversion_rate=0.02):
        # Converts weathered rock and organic matter into soil.

        organic_contribution = (
            self.organic_matter * soil_conversion_rate
        )

        mineral_contribution = (
            self.weathering_progress * 0.005
        )

        soil_change = (
            organic_contribution + mineral_contribution
        )

        self.soil_depth = clamp(
            self.soil_depth + soil_change,
            0.0,
            100.0
        )

        self.organic_matter = clamp(
            self.organic_matter - organic_contribution,
            0.0,
            100.0
        )

        self.add_nutrients(
            soil_change * 0.1
        )

    def get_succession_stage(self):
        if self.soil_depth < 5.0:
            return "Bare rock"

        if self.soil_depth < 20.0:
            return "Pioneer"

        if self.soil_depth < 50.0:
            return "Early soil"

        if self.soil_depth < 80.0:
            return "Developing soil"

        return "Mature soil"

    def get_colour(self):
        if self.tile_type == "water":
            return 40, 100, 200

        if self.soil_depth >= 50.0:
            return 80, 120, 50

        if self.soil_depth >= 20.0:
            return 110, 100, 55

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
