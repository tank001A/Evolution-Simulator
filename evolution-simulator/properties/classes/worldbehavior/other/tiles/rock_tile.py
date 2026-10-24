from properties.classes.worldbehavior.class_tile import *

class RockTile(Tile):
    def __init__(
        self,
        row,
        column,
        lithology="granite"
    ):
        super().__init__(
            row=row,
            column=column,
            tile_type="rock",
            lithology=lithology
        )

        self.dust = 0.0

    def update_dust(self, amount):
        if amount < 0:
            raise ValueError(
                "Dust amount cannot be negative."
            )

        self.dust += amount
