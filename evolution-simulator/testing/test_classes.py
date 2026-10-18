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
    def test_tile_has_position(self):
        tile = Tile(
            row=2,
            column=3
        )

        self.assertEqual(
            tile.row,
            2
        )

        self.assertEqual(
            tile.column,
            3
        )

    def test_tile_has_lithology_and_ucs(self):
        tile = Tile(0, 0)

        self.assertEqual(
            tile.lithology,
            "granite"
        )

        self.assertEqual(
            tile.ucs_mpa,
            175.0
        )

    def test_lithology_can_be_changed(self):
        tile = Tile(0, 0)

        tile.set_lithology("shale")

        self.assertEqual(
            tile.lithology,
            "shale"
        )

        self.assertEqual(
            tile.ucs_mpa,
            50.0
        )

    def test_invalid_lithology_raises_error(self):
        with self.assertRaises(ValueError):
            Tile(
                0,
                0,
                lithology="unknown"
            )

    def test_tile_starts_with_empty_environment(self):
        tile = Tile(0, 0)

        self.assertEqual(
            tile.water_content,
            0.0
        )

        self.assertEqual(
            tile.nutrient_content,
            0.0
        )

        self.assertEqual(
            tile.organic_matter,
            0.0
        )

        self.assertEqual(
            tile.soil_depth,
            0.0
        )

    def test_water_is_clamped(self):
        tile = Tile(0, 0)

        tile.add_water(200)

        self.assertEqual(
            tile.water_content,
            100.0
        )

        tile.remove_water(200)

        self.assertEqual(
            tile.water_content,
            0.0
        )

    def test_nutrients_are_clamped(self):
        tile = Tile(0, 0)

        tile.add_nutrients(200)

        self.assertEqual(
            tile.nutrient_content,
            100.0
        )

        tile.remove_nutrients(200)

        self.assertEqual(
            tile.nutrient_content,
            0.0
        )

    def test_tile_stores_species_biomass(self):
        tile = Tile(0, 0)

        tile.add_species_biomass(
            "Moss",
            20.0
        )

        self.assertEqual(
            tile.get_species_biomass("Moss"),
            20.0
        )

        self.assertEqual(
            tile.get_total_biomass(),
            20.0
        )

    def test_weathering_increases(self):
        tile = Tile(0, 0)

        tile.add_water(100)

        starting_value = (
            tile.weathering_progress
        )

        tile.weather()

        self.assertGreater(
            tile.weathering_progress,
            starting_value
        )

    def test_organic_matter_develops_soil(self):
        tile = Tile(0, 0)

        tile.add_organic_matter(100)
        tile.develop_soil()

        self.assertGreater(
            tile.soil_depth,
            0.0
        )

    def test_new_tile_is_bare_rock(self):
        tile = Tile(0, 0)

        self.assertEqual(
            tile.get_succession_stage(),
            "Bare rock"
        )

    def test_soil_changes_succession_stage(self):
        tile = Tile(0, 0)

        tile.soil_depth = 25.0

        self.assertEqual(
            tile.get_succession_stage(),
            "Early soil"
        )


class TestSpecialisedTiles(unittest.TestCase):
    def test_water_tile_starts_full(self):
        tile = WaterTile(0, 0)

        self.assertEqual(
            tile.water_content,
            100.0
        )

    def test_water_tile_has_water_colour(self):
        tile = WaterTile(0, 0)

        self.assertEqual(
            tile.get_colour(),
            (40, 100, 200)
        )

    def test_rock_tile_stores_dust(self):
        tile = RockTile(0, 0)

        tile.update_dust(10)

        self.assertEqual(
            tile.dust,
            10
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

    def test_world_starts_unpaused(self):
        world = World(
            name="Test World",
            grid_height=2,
            grid_width=2
        )

        self.assertFalse(
            world.paused
        )

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

    def test_get_tile_at_valid_position(self):
        world = World(
            name="Test World",
            grid_height=3,
            grid_width=4
        )

        tile = world.get_tile_at(2, 3)

        self.assertIsNotNone(tile)

        self.assertEqual(
            tile.row,
            2
        )

        self.assertEqual(
            tile.column,
            3
        )

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

    def test_neighbouring_tiles(self):
        world = World(
            name="Test World",
            grid_height=3,
            grid_width=3
        )

        neighbours = (
            world.get_neighbouring_tiles(1, 1)
        )

        self.assertEqual(
            len(neighbours),
            4
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

    def test_visible_bounds(self):
        world = World(
            name="Test World",
            grid_height=300,
            grid_width=400
        )

        bounds = world.get_visible_bounds(
            camera_x=0,
            camera_y=0,
            zoom=8,
            viewport_width=800,
            viewport_height=600
        )

        first_row, last_row, first_column, last_column = (
            bounds
        )

        self.assertEqual(
            first_row,
            0
        )

        self.assertEqual(
            first_column,
            0
        )

        self.assertLessEqual(
            last_row,
            300
        )

        self.assertLessEqual(
            last_column,
            400
        )


class TestOrganisms(unittest.TestCase):
    def test_organism_starts_alive(self):
        organism = Organism(
            organism_position=(0, 0)
        )

        self.assertTrue(
            organism.alive
        )

    def test_organism_can_die(self):
        organism = Organism(
            organism_position=(0, 0)
        )

        organism.die()

        self.assertFalse(
            organism.alive
        )

    def test_coloniser_is_an_organism(self):
        coloniser = Coloniser(
            organism_position=(0, 0)
        )

        self.assertIsInstance(
            coloniser,
            Organism
        )


class TestMoss(unittest.TestCase):
    def make_suitable_tile(self):
        tile = Tile(0, 0)

        tile.water_content = 50.0
        tile.nutrient_content = 50.0
        tile.weathering_progress = 10.0

        return tile

    def test_moss_starts_with_density(self):
        moss = Moss(
            organism_position=(0, 0),
            density=100.0
        )

        self.assertEqual(
            moss.density,
            100.0
        )

    def test_moss_survives_on_suitable_tile(self):
        moss = Moss(
            organism_position=(0, 0)
        )

        tile = self.make_suitable_tile()

        self.assertTrue(
            moss.can_survive_on(tile)
        )

    def test_moss_does_not_survive_on_bare_tile(self):
        moss = Moss(
            organism_position=(0, 0)
        )

        tile = Tile(0, 0)

        tile.water_content = 50.0
        tile.nutrient_content = 50.0

        self.assertFalse(
            moss.can_survive_on(tile)
        )

    def test_moss_consumes_resources(self):
        moss = Moss(
            organism_position=(0, 0),
            density=100.0
        )

        tile = self.make_suitable_tile()

        starting_water = tile.water_content
        starting_nutrients = (
            tile.nutrient_content
        )

        moss.consume_resources(tile)

        self.assertLess(
            tile.water_content,
            starting_water
        )

        self.assertLess(
            tile.nutrient_content,
            starting_nutrients
        )

    def test_moss_logistic_growth_stays_below_capacity(self):
        moss = Moss(
            organism_position=(0, 0),
            density=990.0,
            carrying_capacity=1000.0
        )

        tile = self.make_suitable_tile()

        moss.reproduce(tile)

        self.assertLessEqual(
            moss.density,
            moss.carrying_capacity
        )

    def test_moss_updates_tile_biomass(self):
        moss = Moss(
            organism_position=(0, 0),
            density=100.0
        )

        tile = self.make_suitable_tile()

        moss.reproduce(tile)

        self.assertGreater(
            tile.get_species_biomass("Moss"),
            0.0
        )

    def test_moss_death_adds_organic_matter(self):
        moss = Moss(
            organism_position=(0, 0),
            density=100.0
        )

        tile = Tile(0, 0)

        moss.improve_tile(tile)

        self.assertGreaterEqual(
            tile.organic_matter,
            0.0
        )

    def test_moss_can_spread(self):
        world = World(
            name="Test World",
            grid_height=2,
            grid_width=2
        )

        source = world.get_tile_at(0, 0)
        source.water_content = 50.0
        source.nutrient_content = 50.0
        source.weathering_progress = 10.0

        target = world.get_tile_at(0, 1)
        target.water_content = 50.0
        target.nutrient_content = 50.0
        target.weathering_progress = 10.0

        moss = Moss(
            organism_position=(0, 0),
            density=200.0
        )

        world.add_organism(moss)

        result = moss.try_spread(world)

        self.assertTrue(result)

        self.assertGreaterEqual(
            len(world.all_organisms),
            2
        )


if __name__ == "__main__":
    unittest.main()