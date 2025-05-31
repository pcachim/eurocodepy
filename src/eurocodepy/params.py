from . import db
from .db import WindLoads
from .db import SeismicLoads



def wind_get_params(code: str = "PT", zone: str="ZonaA", terrain: str = "II") -> tuple:
    """Gets the wind load parameters for a given code, zone, and terrain.
    This function retrieves the wind load parameters from the WindLoads database based on the provided parameters.
    It returns a tuple containing the base velocity, minimum height, roughness length, and roughness length for terrain II.
    The parameters are case-insensitive for the zone and terrain, but the code should be provided in uppercase.
    The function is designed to work with different localization codes, such as "PT" for Portugal or "EU" for standard CEN.
    The zones can include "ZonaA", "ZonaB", etc., and the terrain types can include "I", "II", "III", etc.
    This function is useful for engineers and designers who need to apply wind loads according to Eurocode standards.

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
    z0II = wind["terrain"]["II"]["z0"]
    zmin = wind["terrain"][terrain]["zmin"]
    return vb0, zmin, z0, z0II

def seismic_get_params(code, seismic_type, soil_type, importance_class) -> dict:
    """Gets the seismic spectrum parameters for a given code, seismic type, soil type, and importance class.
    This function retrieves the seismic spectrum parameters from the SeismicLoads database based on the provided parameters.
    It returns a dictionary containing the spectrum parameters, including the importance coefficient.
    The parameters are case-insensitive for soil type and importance class, but the seismic type should be provided in uppercase.
    The function is designed to work with different localization codes, such as "PT" for Portugal or "EU" for standard CEN.
    The seismic types can include "PT1", "PT2", "PTA" for Portugal, or "CEN-1", "CEN-2" for CEN standards.
    This function is useful for engineers and designers who need to apply seismic loads according to Eurocode standards.
    Args:
        code (str): Localization code (e.g., "PT" for Portugal, "EU" for standard CEN).
        seismic_type (str): type of seismic action (e.g., "PT1", "PT2", "PTA", "CEN-1", "CEN-2").
        soil_type (str): soil type (e.g., "A", "B", "C", "D", "E" for different soil conditions).   
        importance_class (str): importance class (e.g., "i", "ii", "iii", "iv").

    Returns:
        dict: spectrum parameters for the specified code, seismic type, soil type, and importance class.
    """
    code = str.upper(code)
    seismic_type = str.upper(seismic_type)
    soil_type = str.upper(soil_type)
    importance_class = str.lower(importance_class)
    if code not in SeismicLoads["Locale"]:
        raise ValueError(f"Invalid code: {code}. Available codes: {list(SeismicLoads['Locale'].keys())}")
    if seismic_type not in SeismicLoads["Locale"][code]["Spectrum"]:
        raise ValueError(f"Invalid seismic type: {seismic_type}. Available types: {list(SeismicLoads['Locale'][code]['Spectrum'].keys())}")
    if soil_type not in SeismicLoads["Locale"][code]["Spectrum"][seismic_type]:
        raise ValueError(f"Invalid soil type: {soil_type}. Available types: {list(SeismicLoads['Locale'][code]['Spectrum'][seismic_type].keys())}")
    if importance_class not in SeismicLoads["Locale"][code]["ImportanceClass"]:
        raise ValueError(f"Invalid importance class: {importance_class}. Available classes: {list(SeismicLoads['Locale'][code]['ImportanceCoef'].keys())}")

    # Retrieve the spectrum parameters
    spectrum = SeismicLoads["Locale"][code]["Spectrum"][seismic_type][str.upper(soil_type)]
    spectrum["ImportanceCoef"] = SeismicLoads["Locale"][code]["ImportanceCoef"][seismic_type][importance_class]
    return spectrum