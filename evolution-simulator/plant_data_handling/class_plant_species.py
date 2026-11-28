
class PlantSpecies:
    def __init__(self, row):

        self.id = row["id"]
        self.name = row["name"]

        #plantatt environmental preferences
        self.light = row["light"]
        self.moisture = row["moisture"]
        self.soil_acidity = row["soil_acidity"]
        self.soil_fertility = row["soil_fertility"]
        self.salt = row["salt"]

        #additional characteristics
        self.leaf_thinness = row.get("leaf_thinness")
        self.leaf_area = row.get("leaf_area")

        self.survival_strategy = row.get("survival_strategy")
        self.predicted_survival_strategy = row.get(
            "predicted_survival_strategy"
        )

        self.growth_form = row.get("growth_form")
