# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import pandas as pd

from . import dbase
from .dbase import SeismicLoads, WindLoads

# National parameters
local_name = Path(__file__).parent / "data" / "eurocode_data_portugal.csv"
locale = Enum("locale", ["EU", "PT"])
locales = {}
locales["PT"] = pd.read_csv(local_name)


@dataclass
class NationalParams:
    """Class to hold national parameters."""

    local: locale = locale.PT
    """Locale for national parameters."""
    concelho: str = "Lisboa"
    """Municipality name, default is 'Lisboa'."""

    def __post_init__(self):  # noqa: ANN204
        """Post-initialization to load data."""
        self.data = get_national_params(self.local, self.concelho)


class LocaleData:
    """Class to hold locale data."""

    PT: pd.DataFrame = pd.read_csv(local_name)


def get_national_params(local: locale = locale.PT, concelho: str = "Lisboa") -> object:
    """Get Portuguese data for municipalities.

    Args:
        local (locale, optional): Locale to use for national parameters.
        Defaults to locale.PT.
        concelho (str, optional): Municipality name. Defaults to "Lisboa".

    Returns:
        dict: the data

    """
    pt_data = locale[local.name]
    row = pt_data[pt_data["Concelho"] == concelho]
    # Convert to dict if found
    if not row.empty:
        result = row.iloc[0].to_dict()
        print(result)  # noqa: T201
    else:
        result = None
        print("Concelho not found.")  # noqa: T201
    return result


def wind_get_params(code: str = "PT", zone: str = "ZonaA", terrain: str = "II") -> tuple:
    """Get the wind load parameters for a given code, zone, and terrain.

    This function retrieves the wind load parameters from the WindLoads database based
    on the provided parameters.
    It returns a tuple containing the base velocity, minimum height, roughness length,
    and roughness length for terrain II.
    The parameters are case-insensitive for the zone and terrain, but the code should
    be provided in uppercase.
    The function is designed to work with different localization codes, such as "PT"
    for Portugal or "EU" for standard CEN.
    The zones can include "ZonaA", "ZonaB", etc., and the terrain types can include
    "I", "II", "III", etc.
    This function is useful for engineers and designers who need to apply wind
    loads according to Eurocode standards.

    Args:
        code (str, optional): Localization code. Defaults to "PT".
        zone (str, optional): Wind zone. Defaults to "ZonaA" for Portugal.
        terrain (str, optional): terrain type. Defaults to "II".

    Returns:
        tuple: wind load parameters for the specified code, zone, and terrain.
        The tuple contains:
            - vb0 (float): base velocity for the specified zone.
            - zmin (float): minimum height for the specified terrain.
            - z0 (float): roughness length for the specified terrain.
            - z0II (float): roughness length for terrain II.

    """
    terrain = str.upper(terrain)
    code = str.upper(code)

    wind = WindLoads["locale"][code]
    vb0 = wind["base_velocity"][zone]["vb0"]
    z0 = wind["terrain"][terrain]["z0"]
    z0II = wind["terrain"]["II"]["z0"]  # noqa: N806
    zmin = wind["terrain"][terrain]["zmin"]
    return vb0, zmin, z0, z0II


def seismic_get_params(code, seismic_type, soil_type, importance_class) -> dict:
    """Get the seismic spectrum parameters.

    This function retrieves the seismic spectrum parameters from the SeismicLoads
    database based on the provided parameters. It returns a dictionary containing
    the spectrum parameters, including the importance coefficient. The parameters
    are case-insensitive for soil type and importance class, but the seismic type
    should be provided in uppercase. The function is designed to work with different
    localization codes, such as "PT" for Portugal or "EU" for standard CEN. The
    seismic types can include "PT1", "PT2", "PTA" for Portugal, or "CEN-1", "CEN-2"
    for CEN standards. This function is useful for engineers and designers who need
    to apply seismic loads according to Eurocode standards.

    Args:
        code (str): Localization code (e.g., "PT" for Portugal, "EU" for standard
            CEN).
        seismic_type (str): type of seismic action (e.g., "PT1", "PT2", "PTA",
            "CEN-1", "CEN-2").
        soil_type (str): soil type (e.g., "A", "B", "C", "D", "E" for different
            soil conditions).
        importance_class (str): importance class (e.g., "i", "ii", "iii", "iv").

    Returns:
        dict: spectrum parameters for the specified code, seismic type, soil type,
            and importance class.

    Raises:
        ValueError: If the code, seismic type, soil type, or importance class is
            invalid.

    """
    code = str.upper(code)
    seismic_type = str.upper(seismic_type)
    soil_type = str.upper(soil_type)
    importance_class = str.lower(importance_class)
    if code not in SeismicLoads["Locale"]:
        msg = f"Invalid code: {code}. Available codes: {
            list(SeismicLoads['Locale'].keys())}"
        raise ValueError(msg)
    if seismic_type not in SeismicLoads["Locale"][code]["Spectrum"]:
        msg = f"Invalid seismic type: {seismic_type}. Available types: {
            list(SeismicLoads['Locale'][code]['Spectrum'].keys())}"
        raise ValueError(msg)
    if soil_type not in SeismicLoads["Locale"][code]["Spectrum"][seismic_type]:
        msg = f"Invalid soil type: {soil_type}. Available types: {
            list(SeismicLoads['Locale'][code]['Spectrum'][seismic_type].keys())}"
        raise ValueError(msg)
    if importance_class not in SeismicLoads["Locale"][code]["ImportanceClass"]:
        msg = f"Invalid importance class: {importance_class}. Available classes: {
            list(SeismicLoads['Locale'][code]['ImportanceCoef'].keys())}"
        raise ValueError(msg)

    # Retrieve the spectrum parameters
    spectrum = SeismicLoads["Locale"
            ][code]["Spectrum"][seismic_type][str.upper(soil_type)]
    spectrum["ImportanceCoef"] = SeismicLoads["Locale"
            ][code]["ImportanceCoef"][seismic_type][importance_class]
    return spectrum
