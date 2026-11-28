
import pandas as pd

from plant_data_handling.class_plant_species import PlantSpecies
from pathlib import Path

FILE_NAME = Path(__file__).parent / "simulationdataset_final.xlsx"


def load_data():
    return pd.read_excel(FILE_NAME)


def clean_data(df):
    required_columns = [
        "id",
        "name",
        "light",
        "moisture",
        "soil_acidity",
        "soil_fertility",
        "salt"
    ]

    return df.dropna(subset=required_columns)


def filter_by_preset(df, preset_name):
    if preset_name == "grassland":
        filtered_df = df[
            (df["growth_form"] == "Herb")
            | (df["growth_form"] == "Graminoid")
            | (df["growth_form"] == "Shrub")
        ]

        filtered_df = filtered_df[
            (filtered_df["moisture"] >= 3)
            & (filtered_df["moisture"] <= 8)
        ]

    elif preset_name == "freshwater":
        filtered_df = df[df["growth_form"] == "Aquatic"]

    else:
        filtered_df = df

    return filtered_df


def load_species(preset_name):
    df = load_data()
    df = clean_data(df)
    df = filter_by_preset(df, preset_name)

    species = {}

    for index, row in df.iterrows():
        plant_species = PlantSpecies(row)
        species[plant_species.id] = plant_species

    return species
