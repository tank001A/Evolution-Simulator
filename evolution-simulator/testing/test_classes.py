import unittest

from classes import (
    Coloniser,
    Moss,
    Organism,
    RockTile,
    Tile,
    WaterTile,
    World
)


class TestTile(unittest.TestCase):
    def test_tile_stores_position_and_type(self):
        tile = Tile(
            row=2,
            column=3,
            tile_type="rock"
        )

        self.assertEqual(tile.row, 2)
        self.assertEqual(tile.column, 3)
        self.assertEqual(tile.tile_type, "rock")

    def test_tile_starts_with_zero_environmental_values(self):
        tile = Tile(
            row=0,
            column=0
        )

        self.assertEqual(tile.water_content, 0)
        self.assertEqual(tile.nutrient_content, 0)

    def test_tile_can_add_and_remove_water(self):
        tile = Tile(0, 0)

        tile.add_water(20)
        self.assertEqual(tile.water_content, 20)

        tile.remove_water(5)
        self.assertEqual(tile.water_content, 15)

    def test_water_cannot_become_negative(self):
        tile = Tile(0, 0)

        tile.remove_water(10)

        self.assertEqual(tile.water_content, 0)

    def test_tile_can_add_and_remove_nutrients(self):
        tile = Tile(0, 0)

        tile.add_nutrients(20)
        self.assertEqual(tile.nutrient_content, 20)

        tile.remove_nutrients(5)
        self.assertEqual(tile.nutrient_content, 15)

    def test_nutrients_cannot_become_negative(self):
        tile = Tile(0, 0)

        tile.remove_nutrients(10)

        self.assertEqual(tile.nutrient_content, 0)

    def test_rock_colour(self):
        tile = Tile(
            row=0,
            column=0,
            tile_type="rock"
        )

        self.assertEqual(
            tile.get_colour(),
            (100, 100, 100)
        )

    def test_water_colour(self):
        tile = WaterTile(0, 0)

        self.assertEqual(
            tile.get_colour(),
            (40, 100, 200)
        )


class TestSpecialisedTiles(unittest.TestCase):
    def test_water_tile_starts_with_water(self):
        tile = WaterTile(0, 0)

        self.assertEqual(
            tile.water_content,
            100
        )

    def test_rock_tile_can_store_dust(self):
        tile = RockTile(0, 0)

        tile.update_dust(10)

        self.assertEqual(
            tile.dust,
            10
        )

    def test_rock_tile_organic_matter_adds_nutrients(self):
        tile = RockTile(0, 0)

        tile.add_organic_matter(15)

        self.assertEqual(
            tile.nutrient_content,
            15
        )


class TestWorld(unittest.TestCase):
    def test_world_has_correct_dimensions(self):
        world = World(
            name="Test World",
            grid_height=3,
            grid_width=4
        )

        self.assertEqual(
            len(world.grid),
            3
        )

        self.assertEqual(
            len(world.grid[0]),
            4
        )

    def test_first_tile_has_correct_position(self):
        world = World(
            name="Test World",
            grid_height=3,
            grid_width=4
        )

        first_tile = world.grid[0][0]

        self.assertEqual(
            first_tile.row,
            0
        )

        self.assertEqual(
            first_tile.column,
            0
        )

    def test_last_tile_has_correct_position(self):
        world = World(
            name="Test World",
            grid_height=3,
            grid_width=4
        )

        last_tile = world.grid[2][3]

        self.assertEqual(
            last_tile.row,
            2
        )

        self.assertEqual(
            last_tile.column,
            3
        )

    def test_world_starts_running(self):
        world = World(
            name="Test World",
            grid_height=2,
            grid_width=2
        )

        self.assertFalse(world.paused)

    def test_running_world_updates(self):
        world = World(
            name="Test World",
            grid_height=2,
            grid_width=2
        )

        world.update()

        self.assertEqual(
            world.simulation_time,
            1
        )

    def test_paused_world_does_not_update(self):
        world = World(
            name="Test World",
            grid_height=2,
            grid_width=2
        )

        world.pause_world()
        world.update()

        self.assertEqual(
            world.simulation_time,
            0
        )

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

    def test_get_tile_at_valid_position(self):
        world = World(
            name="Test World",
            grid_height=3,
            grid_width=4
        )

        tile = world.get_tile_at(2, 3)

        self.assertIsNotNone(tile)
        self.assertEqual(tile.row, 2)
        self.assertEqual(tile.column, 3)

    def test_get_tile_at_invalid_position(self):
        world = World(
            name="Test World",
            grid_height=3,
            grid_width=4
        )

        self.assertIsNone(
            world.get_tile_at(3, 0)
        )

        self.assertIsNone(
            world.get_tile_at(0, 4)
        )

    def test_average_water(self):
        world = World(
            name="Test World",
            grid_height=2,
            grid_width=2
        )

        for row in world.grid:
            for tile in row:
                tile.water_content = 20

        self.assertEqual(
            world.get_average_water(),
            20
        )

    def test_fast_forward(self):
        world = World(
            name="Test World",
            grid_height=2,
            grid_width=2
        )

        world.fast_forward(5)

        self.assertEqual(
            world.simulation_time,
            5
        )


class TestOrganisms(unittest.TestCase):
    def test_organism_starts_alive(self):
        organism = Organism(
            organism_position=(0, 0)
        )

        self.assertTrue(organism.alive)

    def test_organism_can_die(self):
        organism = Organism(
            organism_position=(0, 0)
        )

        organism.die()

        self.assertFalse(organism.alive)

    def test_coloniser_is_an_organism(self):
        coloniser = Coloniser(
            organism_position=(0, 0)
        )

        self.assertIsInstance(
            coloniser,
            Organism
        )


class TestMoss(unittest.TestCase):
    def test_moss_starts_with_density(self):
        moss = Moss(
            organism_position=(0, 0),
            density=500
        )

        self.assertEqual(
            moss.density,
            500
        )

    def test_moss_survives_on_suitable_tile(self):
        tile = Tile(0, 0)
        tile.water_content = 20
        tile.nutrient_content = 10

        moss = Moss(
            organism_position=(0, 0),
            density=500
        )

        self.assertTrue(
            moss.can_survive_on(tile)
        )

    def test_moss_does_not_survive_on_unsuitable_tile(self):
        tile = Tile(0, 0)
        tile.water_content = 2
        tile.nutrient_content = 1

        moss = Moss(
            organism_position=(0, 0),
            density=500
        )

        self.assertFalse(
            moss.can_survive_on(tile)
        )

    def test_moss_consumes_resources(self):
        tile = Tile(0, 0)
        tile.water_content = 20
        tile.nutrient_content = 10

        moss = Moss(
            organism_position=(0, 0),
            density=500
        )

        starting_water = tile.water_content
        starting_nutrients = tile.nutrient_content

        result = moss.consume_resources(tile)

        self.assertTrue(result)

        self.assertLess(
            tile.water_content,
            starting_water
        )

        self.assertLess(
            tile.nutrient_content,
            starting_nutrients
        )

    def test_moss_death_has_controlled_mortality(self):
        tile = Tile(0, 0)

        moss = Moss(
            organism_position=(0, 0),
            density=1000,
            mortality_rate=0.05
        )

        starting_density = moss.density

        organic_mass = moss.improve_tile(tile)

        self.assertGreaterEqual(
            organic_mass,
            0
        )

        self.assertLessEqual(
            moss.density,
            starting_density
        )

        self.assertGreaterEqual(
            tile.nutrient_content,
            0
        )

    def test_moss_eventually_dies_when_density_reaches_zero(self):
        moss = Moss(
            organism_position=(0, 0),
            density=0
        )

        moss.update(
            Tile(0, 0),
            None
        )

        self.assertFalse(moss.alive)

    def test_world_updates_moss(self):
        world = World(
            name="Test World",
            grid_height=2,
            grid_width=2
        )

        tile = world.get_tile_at(0, 0)
        tile.water_content = 20
        tile.nutrient_content = 10

        moss = Moss(
            organism_position=(0, 0),
            density=500
        )

        world.add_organism(moss)

        starting_water = tile.water_content

        world.update()

        self.assertLess(
            tile.water_content,
            starting_water
        )


if __name__ == "__main__":
    unittest.main()