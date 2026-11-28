from properties.classes.Organisms import Organism


class Plant(Organism):

    TOLERANCE = 2  # how far from the preference the plant can tolerate

    def __init__(self, row, organism_position):
        super().__init__(organism_position)

        self.id = row["id"]
        self.name = row["name"]

        self.leaf_thinness = row["leaf_thinness"]
        self.leaf_area = row["leaf_area"]

        self.light = row["light"]
        self.moisture = row["moisture"]
        self.soil_acidity = row["soil_acidity"]
        self.soil_fertility = row["soil_fertility"]
        self.salt = row["salt"]

        self.survival_strategy = row["survival_strategy"]
        self.predicted_survival_strategy = row["predicted_survival_strategy"]

        self.growth_form = row["growth_form"]

        self.alive = True

    def can_survive_on(self, tile):
        tolerance = self.TOLERANCE
        #we need to know if the tiles condidtion is ina certain distance of the actual plants preference not caring if the tile is too high or too low
        #no abs would mean then a very dry tile would incorrectly pass. so its more forgiving, checking both sides since plants can be harmed in both directions

        light_ok = abs(tile.light_level - self.light) <= tolerance
        moisture_ok = abs(tile.moisture_level - self.moisture) <= tolerance
        acidity_ok = abs(tile.soil_acidity - self.soil_acidity) <= tolerance
        fertility_ok = abs(tile.soil_fertility - self.soil_fertility) <= tolerance
        salt_ok = tile.salt_level <= self.salt

        return all((
            light_ok,
            moisture_ok,
            acidity_ok,
            fertility_ok,
            salt_ok
        ))

