from enum import Enum
from dataclasses import dataclass
from collections import UserDict
from itertools import product, chain

class LoadType(Enum):
    """
    Enum for different types of loads as per Eurocode standards.
    """
    PERMANENT = 0
    LIVE = 1
    WIND = 2
    SNOW = 3
    EARTHQUAKE = 4
    TEMPERATURE = 5
    FIRE = 6
    ACCIDENTAL = 7
    OTHER = 8

    def __str__(self):
        return self.value

    @classmethod
    def from_string(cls, value: str):
        """
        Convert a string to a LoadType enum member.
        
        Args:
            value (str): The string representation of the load type.
        
        Returns:
            LoadType: The corresponding enum member.
        
        Raises:
            ValueError: If the string does not match any enum member.
        """
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Invalid load type: {value}") 

class CombinationType(Enum):
    """
    Enum for different types of load combinations as per Eurocode standards.
    """
    ULS = "ULS" # Ultimate Limit State
    SLS_K = "SLS-K"  # Serviceability Limit State
    SLS_FR = "SLS-FR"  # Serviceability Limit State
    SLS_QP = "SLS-QP"  # Serviceability Limit State
    FLS = "FLS"  # Fatigue Limit State
    ALS = "ALS"  # Accidental Limit State

    def __str__(self):
        return self.value

    @classmethod
    def from_string(cls, value: str):
        """
        Convert a string to a CombinationType enum member.
        
        Args:
            value (str): The string representation of the combination type.
        
        Returns:
            CombinationType: The corresponding enum member.
        
        Raises:
            ValueError: If the string does not match any enum member.
        """
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Invalid combination type: {value}")

class LoadCombination:
    """
    Class representing a load combination for Eurocode standards.
    
    Attributes:
        name (str): Name of the load combination.
        type (CombinationType): Type of the load combination.
        factors (dict): Load factors for different loads.
    """
    
    def __init__(self, name: str, type: CombinationType, factors: dict):
        self.name = name
        self.type = type
        self.factors = factors

    def __repr__(self):
        return f"LoadCombination(name={self.name}, type={self.type}, factors={self.factors})"
    def __str__(self):
        return f"{self.name} ({self.type}): {self.factors}"

@dataclass
class Load():
    """
    Load class representing a load with its name, type, reduced coefficients and safety factors.
    """
    name: str
    load_type: LoadType
    gamma_fav: float
    gamma_unf: float
    psi0: float
    psi1: float
    psi2: float
    incombo: bool = True
    
class LoadCollection(UserDict):
    """Collection of loads that can be added, removed, and queried.
    This class extends UserDict to manage a collection of Load objects.
    It allows adding, removing, and finding loads by type, as well as calculating load combinations for ULS and SLS.
    It also provides methods to get ULS and SLS load combinations based on the loads in the collection.
    It is initialized with an empty dictionary to store Load objects.

    Args:
        UserDict (Load): Load objects collection.
    """
    def __init__(self):
        super().__init__()
        self.packs = []
    
    def add(self, load: Load) -> None:
        if not isinstance(load, Load):
            raise ValueError("Only Load instances can be added.")
        if load.name in self.data:
            raise ValueError(f"A load with name '{load.name}' already exists.")
        self.data[load.name] = load

    def remove(self, name: str) -> None:
        if name not in self.data:
            raise ValueError(f"No load found with name '_{name}'.")
        del self.data[name]

    def find_by_type(self, load_type: LoadType) -> list[Load]:
        return [name for name, load in self.data.items() if load.load_type == load_type]

    def __repr__(self):
        return f"LoadCollection({self.data})"
    
    def get_ULS_combos(self) -> dict[LoadCombination]:
        """
        Calculate ULS load combinations based on the loads in the collection.
        
        Returns:
            list[LoadCombination]: List of ULS load combinations.
        """
        perm_loads = self.find_by_type(LoadType.PERMANENT)
        live_loads = self.find_by_type(LoadType.LIVE)
        other_loads = self.find_by_type(LoadType.OTHER)
        snow_loads = self.find_by_type(LoadType.SNOW)
        earthquake_loads = self.find_by_type(LoadType.EARTHQUAKE)
        wind_loads = self.find_by_type(LoadType.WIND)
        temperature_loads = self.find_by_type(LoadType.TEMPERATURE)
        wind_temp = list(product(wind_loads, temperature_loads))

        combinations = {}
        
        # Variable loads combinations
        for item in wind_temp:
            variable_loads = list(chain(live_loads, item, snow_loads, other_loads))
        
            for j, name in enumerate(variable_loads):
                combo = LoadCombination(
                    name=f"ULS: ",
                    type=CombinationType.ULS,
                    factors={})
                
                for name in perm_loads:
                    perm_load = self.data[name]
                    factor = round(perm_load.gamma_unf, 3)
                    if abs(factor) < 0.001: continue
                    combo.name += f"+{factor:.2f}_{name}"
                    combo.factors[name] = (perm_load, factor)

                for i, name in enumerate(variable_loads):
                    load = self.data[name]
                    factor = load.gamma_unf if i == j else load.gamma_unf * load.psi0
                    if abs(factor) < 0.001: continue
                    combo.name += f"+{factor:.2f}_{name}"
                    combo.factors[load.name] = (load, round(factor, 3))

                if combo.name not in combinations:
                    combinations[combo.name] = combo

        # Seismic loads combinations
        for item in wind_temp:
            variable_loads = list(chain(live_loads, item, snow_loads, other_loads))
        
            for loadname in earthquake_loads:
                combo = LoadCombination(
                    name=f"ULS-E: ",
                    type=CombinationType.ULS,
                    factors={})
                
                for name in perm_loads:
                    perm_load = self.data[name]
                    factor = 1.0
                    combo.name += f"+{factor:.2f}_{name}"
                    combo.factors[name] = (perm_load, factor)

                for i, name in enumerate(variable_loads):
                    load = self.data[name]
                    factor = load.psi2
                    if abs(factor) < 0.001: continue
                    combo.name += f"+{factor:.2f}_{name}"
                    combo.factors[load.name] = (load, round(factor, 3))

                load = self.data[loadname]
                combo.name += f"+{load.gamma_unf:.2f}_{loadname}"
                combo.factors[loadname] = (load, load.gamma_unf)

                if combo.name not in combinations:
                    combinations[combo.name] = combo

        return combinations

    def get_SLS_combos(self) -> dict[LoadCombination]:
        """
        Calculate ULS load combinations based on the loads in the collection.
        
        Returns:
            list[LoadCombination]: List of ULS load combinations.
        """
        perm_loads = self.find_by_type(LoadType.PERMANENT)
        live_loads = self.find_by_type(LoadType.LIVE)
        other_loads = self.find_by_type(LoadType.OTHER)
        snow_loads = self.find_by_type(LoadType.SNOW)
        earthquake_loads = self.find_by_type(LoadType.EARTHQUAKE)
        wind_loads = self.find_by_type(LoadType.WIND)
        temperature_loads = self.find_by_type(LoadType.TEMPERATURE)
        wind_temp = list(product(wind_loads, temperature_loads))

        combinations = {}
        
        # Characteristic loads combinations
        for item in wind_temp:
            variable_loads = list(chain(live_loads, item, snow_loads, other_loads))
        
            for j, name in enumerate(variable_loads):
                combo = LoadCombination(
                    name=f"SLS-K: ",
                    type=CombinationType.SLS_K,
                    factors={})
                
                for name in perm_loads:
                    perm_load = self.data[name]
                    factor = 1.0
                    if abs(factor) < 0.001: continue
                    combo.name += f"+{factor:.2f}_{name}"
                    combo.factors[name] = (perm_load, factor)

                for i, name in enumerate(variable_loads):
                    load = self.data[name]
                    factor = 1.0 if i == j else load.psi0
                    if abs(factor) < 0.001: continue
                    combo.name += f"+{factor:.2f}_{name}"
                    combo.factors[load.name] = (load, round(factor, 3))

            if combo.name not in combinations:
                combinations[combo.name] = combo

        # Frequent loads combinations
        for item in wind_temp:
            variable_loads = list(chain(live_loads, item, snow_loads, other_loads))
        
            for j, name in enumerate(variable_loads):
                combo = LoadCombination(
                    name=f"SLS-FR: ",
                    type=CombinationType.SLS_FR,
                    factors={})
                
                for name in perm_loads:
                    perm_load = self.data[name]
                    factor = 1.0
                    if abs(factor) < 0.001: continue
                    combo.name += f"+{factor:.2f}_{name}"
                    combo.factors[name] = (perm_load, factor)

                for i, name in enumerate(variable_loads):
                    load = self.data[name]
                    factor = load.psi1 if i == j else load.psi2
                    if abs(factor) < 0.001: continue
                    combo.name += f"+{factor:.2f}_{name}"
                    combo.factors[load.name] = (load, round(factor, 3))

            if combo.name not in combinations:
                combinations[combo.name] = combo

        # Quasi-permanent loads combinations
        for item in wind_temp:
            variable_loads = list(chain(live_loads, item, snow_loads, other_loads))
        
            for j, name in enumerate(variable_loads):
                combo = LoadCombination(
                    name=f"SLS-QP: ",
                    type=CombinationType.SLS_QP,
                    factors={})
                
                for name in perm_loads:
                    perm_load = self.data[name]
                    factor = 1.0
                    if abs(factor) < 0.001: continue
                    combo.name += f"+{factor:.2f}_{name}"
                    combo.factors[name] = (perm_load, factor)

                for i, name in enumerate(variable_loads):
                    load = self.data[name]
                    factor = load.psi2
                    if abs(factor) < 0.001: continue
                    combo.name += f"+{factor:.2f}_{name}"
                    combo.factors[load.name] = (load, round(factor, 3))

            if combo.name not in combinations:
                combinations[combo.name] = combo

        return combinations


if __name__ == "__main__":
    # Example usage
    loads = LoadCollection()
    loads.add(Load(name="DW", load_type=LoadType.PERMANENT, gamma_fav=1.0, gamma_unf=1.35, psi0=0.0, psi1=0.0, psi2=0.0))
    loads.add(Load(name="LL", load_type=LoadType.LIVE, gamma_fav=0.0, gamma_unf=1.5, psi0=0.7, psi1=0.5, psi2=0.3))
    loads.add(Load(name="W0", load_type=LoadType.WIND, gamma_fav=0.0, gamma_unf=1.5, psi0=0.6, psi1=0.4, psi2=0.0))
    loads.add(Load(name="W90", load_type=LoadType.WIND, gamma_fav=0.0, gamma_unf=1.5, psi0=0.6, psi1=0.4, psi2=0.0))
    loads.add(Load(name="Tint", load_type=LoadType.TEMPERATURE, gamma_fav=0.0, gamma_unf=1.5, psi0=0.3, psi1=0.0, psi2=0.2))
    loads.add(Load(name="Text", load_type=LoadType.TEMPERATURE, gamma_fav=0.0, gamma_unf=1.5, psi0=0.3, psi1=0.0, psi2=0.1))
    loads.add(Load(name="S", load_type=LoadType.SNOW, gamma_fav=0.0, gamma_unf=1.5, psi0=0.6, psi1=0.3, psi2=0.0))
    loads.add(Load(name="E1", load_type=LoadType.EARTHQUAKE, gamma_fav=0.0, gamma_unf=1.0, psi0=0.0, psi1=0.0, psi2=0.0))
    loads.add(Load(name="E2", load_type=LoadType.EARTHQUAKE, gamma_fav=0.0, gamma_unf=1.0, psi0=0.0, psi1=0.0, psi2=0.0))
    
    # Calculate ULS and SLS combinations
    print("ULS Combinations:")
    uls_combinations = loads.get_ULS_combinations()
    for key, combo in uls_combinations.items():
        print(key)
        for load_name, (load, factor) in combo.factors.items():
            print(f"  {load_name}: {factor}")
    print("\nSLS Combinations:")
    sls_combinations = loads.get_SLS_combinations()
    for key, combo in sls_combinations.items():
        print(key)
        for load_name, (load, factor) in combo.factors.items():
            print(f"  {load_name}: {factor}")
    