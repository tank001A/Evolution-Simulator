import unittest
from classes import Tile, World


class TestTile(unittest.TestCase):
    def test_paused_world_does_not_update(self):
        world = World(
            name="Test World",
            grid_height=2,
            grid_width=2
        )

        world.pause_world()
        world.update()

        self.assertEqual(world.simulation_time, 0)

    def test_tile_stores_values(self):
        tile = Tile(
            2,
            3,
            tile_type="soil",
            water_content=75,
            nutrient_content=40
        )

        self.assertEqual(tile.row, 2)
        self.assertEqual(tile.column, 3)
        self.assertEqual(tile.tile_type, "soil")
        self.assertEqual(tile.water_content, 75)
        self.assertEqual(tile.nutrient_content, 40)


class TestWorld(unittest.TestCase):
    def test_world_starts_running(self):
        world = World(
            name="Test World",
            grid_height=2,
            grid_width=2
        )

        self.assertFalse(world.paused)

    def test_paused_world_does_not_update(self):
        world = World(
            name="Test World",
            grid_height=2,
            grid_width=2
        )

        world.pause_world()
        world.update()

        self.assertEqual(world.simulation_time, 0)

    def test_running_world_updates(self):
        world = World(
            name="Test World",
            grid_height=2,
            grid_width=2
        )

        world.update()

        self.assertEqual(world.simulation_time, 1)

    def test_pause_and_resume(self):
        world = World(
            name="Test World",
            grid_height=2,
            grid_width=2
        )

        world.pause_world()
        self.assertTrue(world.paused)

        world.continue_world()
        self.assertFalse(world.paused)
    def test_world_has_correct_dimensions(self):
        world = World(
            name="Test World",
            grid_height=3,
            grid_width=4
        )

        self.assertEqual(len(world.grid), 3)
        self.assertEqual(len(world.grid[0]), 4)

    def test_first_tile_has_correct_position(self):
        world = World(
            name="Test World",
            grid_height=3,
            grid_width=4
        )


        first_tile = world.grid[0][0]

        self.assertEqual(first_tile.row, 0)
        self.assertEqual(first_tile.column, 0)

    def test_last_tile_has_correct_position(self):
        world = World(
            name="Test World",
            grid_height=3,
            grid_width=4
        )

        last_tile = world.grid[2][3]

        self.assertEqual(last_tile.row, 2)
        self.assertEqual(last_tile.column, 3)



if __name__ == "__main__":
    unittest.main()
