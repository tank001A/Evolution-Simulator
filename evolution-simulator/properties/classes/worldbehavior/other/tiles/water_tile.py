from properties.classes.worldbehavior.class_tile import *


class WaterTile(Tile):
    def __init__(
        self,
        row,
        column
    ):
        super().__init__(
            row=row,
            column=column,
            tile_type="water"
        )

        self.water_content = 100.0

    def get_colour(self):
        return 40, 100, 200

