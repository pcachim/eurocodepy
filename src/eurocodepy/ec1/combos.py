# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT
"""Module for Eurocode Load Combinations and Load Types."""
from collections import UserDict
from dataclasses import dataclass
from enum import Enum
from itertools import chain, product

COMBO_TOLERANCE: float = 0.001


class LoadType(Enum):
    """Enum for different types of loads as per Eurocode standards."""

    PERMANENT = 0
    LIVE = 1
    WIND = 2
    SNOW = 3
    EARTHQUAKE = 4
    TEMPERATURE = 5
    FIRE = 6
    ACCIDENTAL = 7
    OTHER = 8

    def __str__(self) -> str:  # noqa: D105
        return self.value

    @classmethod
    def from_string(cls, value: str) -> "LoadType":
        """Convert a string to a LoadType enum member.

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
            msg = f"Invalid load type: {value}"
            raise ValueError(msg) from None


class CombinationType(Enum):
    """Enum for different types of load combinations as per Eurocode standards."""

    ULS = "ULS"  # Ultimate Limit State
    SLS_K = "SLS-K"  # Serviceability Limit State
    SLS_FR = "SLS-FR"  # Serviceability Limit State
    SLS_QP = "SLS-QP"  # Serviceability Limit State
    FLS = "FLS"  # Fatigue Limit State
    ALS = "ALS"  # Accidental Limit State

    def __str__(self) -> str:  # noqa: D105
        return self.value

    @classmethod
    def from_string(cls, value: str) -> "CombinationType":
        """Convert a string to a CombinationType enum member.

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
            msg = f"Invalid combination type: {value}"
            raise ValueError(msg) from None


class LoadCombination:
    """Class representing a load combination for Eurocode standards.

    Attributes:
        name (str): Name of the load combination.
        combotype (CombinationType): Type of the load combination.
        factors (dict): Load factors for different loads.

    """

    def __init__(self, name: str, combotype: CombinationType, factors: dict) -> None:  # noqa: D107
        self.name = name
        self.type = combotype
        self.factors = factors

    def __repr__(self) -> str:  # noqa: D105
        return f"LoadCombination(name={self.name}, type={self.type}, factors={self.factors})"

    def __str__(self) -> str:  # noqa: D105
        return f"{self.name} ({self.type}): {self.factors}"


@dataclass
class Load:
    """Class representing a load with its properties.

    Attributes:
        name (str): Name of the load.
        load_type (LoadType): Type of the load.
        gamma_fav (float): Favorable load factor.
        gamma_unf (float): Unfavorable load factor.
        psi0 (float): Coefficient for quasi-permanent loads.
        psi1 (float): Coefficient for frequent loads.
        psi2 (float): Coefficient for characteristic loads.
        incombo (bool): Indicates if the load is included in combos (default is True).

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
    It allows adding, removing, and finding loads by type, as well as calculating
    load combinations for ULS and SLS.
    It also provides methods to get ULS and SLS load combinations based on the loads
    in the collection.
    It is initialized with an empty dictionary to store Load objects.

    Args:
        UserDict (Load): Load objects collection.

    """

    def __init__(self) -> None:  # noqa: D107
        super().__init__()
        self.packs = []

    def add(self, load: Load) -> None:
        """Add a Load instance to the collection.

        Args:
            load (Load): The Load instance to add.

        Raises:
            TypeError: If the provided object is not a Load instance.
            ValueError: If a load with the same name already exists.

        """
        if not isinstance(load, Load):
            msg = "Only Load instances can be added."
            raise TypeError(msg)
        if load.name in self.data:
            msg = f"A load with name '{load.name}' already exists."
            raise ValueError(msg)
        self.data[load.name] = load

    def remove(self, name: str) -> None:
        """Remove a load from the collection by its name.

        Args:
            name (str): The name of the load to remove.

        Raises:
            ValueError: If no load is found with the given name.

        """
        if name not in self.data:
            msg = f"No load found with name '_{name}'."
            raise ValueError(msg)
        del self.data[name]

    def find_by_type(self, load_type: LoadType) -> list[Load]:
        """Find all loads of a specific type.

        Args:
            load_type (LoadType): The type of load to find.

        Returns:
            list[Load]: List of load names that match the specified type.

        """
        return [name for name, load in self.data.items() if load.load_type == load_type]

    def __repr__(self) -> str:  # noqa: D105
        return f"LoadCollection({self.data})"

    def get_ULS_combos(self) -> dict:  # noqa: C901, N802, PLR0912
        """Calculate ULS load combinations based on the loads in the collection.

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
        if len(wind_temp) == 0:
            wind_temp = [{w} for w in wind_loads]

        combinations = {}

        # Variable loads combinations
        for item in wind_temp:
            variable_loads = list(chain(live_loads, item, snow_loads, other_loads))

            for j, name in enumerate(variable_loads):  # noqa: B007
                combo = LoadCombination(
                    name="ULS: ",
                    combotype=CombinationType.ULS,
                    factors={})

                for _name in perm_loads:
                    perm_load = self.data[_name]
                    factor = round(perm_load.gamma_unf, 3)
                    if abs(factor) < COMBO_TOLERANCE:
                        continue
                    combo.name += f"+{factor:.2f}_{_name}"
                    combo.factors[_name] = (perm_load, factor)

                for i, _name in enumerate(variable_loads):
                    load = self.data[_name]
                    factor = load.gamma_unf if i == j else load.gamma_unf * load.psi0
                    if abs(factor) < COMBO_TOLERANCE:
                        continue
                    combo.name += f"+{factor:.2f}_{_name}"
                    combo.factors[load.name] = (load, round(factor, 3))

                if combo.name not in combinations:
                    combinations[combo.name] = combo

        # Seismic loads combinations
        for item in wind_temp:
            variable_loads = list(chain(live_loads, item, snow_loads, other_loads))

            for loadname in earthquake_loads:
                combo = LoadCombination(
                    name="ULS-E: ",
                    combotype=CombinationType.ULS,
                    factors={})

                for name in perm_loads:
                    perm_load = self.data[name]
                    factor = 1.0
                    combo.name += f"+{factor:.2f}_{name}"
                    combo.factors[name] = (perm_load, factor)

                for name in variable_loads:
                    load = self.data[name]
                    factor = load.psi2
                    if abs(factor) < COMBO_TOLERANCE:
                        continue
                    combo.name += f"+{factor:.2f}_{name}"
                    combo.factors[load.name] = (load, round(factor, 3))

                load = self.data[loadname]
                combo.name += f"+{load.gamma_unf:.2f}_{loadname}"
                combo.factors[loadname] = (load, load.gamma_unf)

                if combo.name not in combinations:
                    combinations[combo.name] = combo

        return combinations

    def get_SLS_combos(self) -> dict:  # noqa: C901, N802, PLR0912, PLR0915
        """Calculate ULS load combinations based on the loads in the collection.

        Returns:
            list[LoadCombination]: List of ULS load combinations.

        """
        perm_loads = self.find_by_type(LoadType.PERMANENT)
        live_loads = self.find_by_type(LoadType.LIVE)
        other_loads = self.find_by_type(LoadType.OTHER)
        snow_loads = self.find_by_type(LoadType.SNOW)
        wind_loads = self.find_by_type(LoadType.WIND)
        temperature_loads = self.find_by_type(LoadType.TEMPERATURE)
        wind_temp = list(product(wind_loads, temperature_loads))
        if len(wind_temp) == 0:
            wind_temp = [{w} for w in wind_loads]

        combinations = {}

        # Characteristic loads combinations
        for item in wind_temp:
            variable_loads = list(chain(live_loads, item, snow_loads, other_loads))

            for j in range(len(variable_loads)):
                combo = LoadCombination(
                    name="SLS-K: ",
                    combotype=CombinationType.SLS_K,
                    factors={})

                for _name in perm_loads:
                    perm_load = self.data[_name]
                    factor = 1.0
                    if abs(factor) < COMBO_TOLERANCE:
                        continue
                    combo.name += f"+{factor:.2f}_{_name}"
                    combo.factors[_name] = (perm_load, factor)

                for i, _name in enumerate(variable_loads):
                    load = self.data[_name]
                    factor = 1.0 if i == j else load.psi0
                    if abs(factor) < COMBO_TOLERANCE:
                        continue
                    combo.name += f"+{factor:.2f}_{_name}"
                    combo.factors[load.name] = (load, round(factor, 3))

            if combo.name not in combinations:
                combinations[combo.name] = combo

        # Frequent loads combinations
        for item in wind_temp:
            variable_loads = list(chain(live_loads, item, snow_loads, other_loads))

            for j, __name in enumerate(variable_loads):
                combo = LoadCombination(
                    name="SLS-FR: ",
                    combotype=CombinationType.SLS_FR,
                    factors={})

                for _name in perm_loads:
                    perm_load = self.data[_name]
                    factor = 1.0
                    if abs(factor) < COMBO_TOLERANCE:
                        continue
                    combo.name += f"+{factor:.2f}_{_name}"
                    combo.factors[_name] = (perm_load, factor)

                for i, _name in enumerate(variable_loads):
                    load = self.data[_name]
                    factor = load.psi1 if i == j else load.psi2
                    if abs(factor) < COMBO_TOLERANCE:
                        continue
                    combo.name += f"+{factor:.2f}_{_name}"
                    combo.factors[load.name] = (load, round(factor, 3))

            if combo.name not in combinations:
                combinations[combo.name] = combo

        # Quasi-permanent loads combinations
        for item in wind_temp:
            variable_loads = list(chain(live_loads, item, snow_loads, other_loads))

            for __name in variable_loads:
                combo = LoadCombination(
                    name="SLS-QP: ",
                    combotype=CombinationType.SLS_QP,
                    factors={})

                for _name in perm_loads:
                    perm_load = self.data[_name]
                    factor = 1.0
                    if abs(factor) < COMBO_TOLERANCE:
                        continue
                    combo.name += f"+{factor:.2f}_{_name}"
                    combo.factors[_name] = (perm_load, factor)

                for _name in variable_loads:
                    load = self.data[_name]
                    factor = load.psi2
                    if abs(factor) < COMBO_TOLERANCE:
                        continue
                    combo.name += f"+{factor:.2f}_{_name}"
                    combo.factors[load.name] = (load, round(factor, 3))

            if combo.name not in combinations:
                combinations[combo.name] = combo

        return combinations


if __name__ == "__main__":
    # Example usage
    loads = LoadCollection()
    loads.add(Load(name="G", load_type=LoadType.PERMANENT,gamma_fav=1.0, gamma_unf=1.35, psi0=0.0, psi1=0.0, psi2=0.0))
    loads.add(Load(name="Q", load_type=LoadType.LIVE, gamma_fav=0.0, gamma_unf=1.5, psi0=0.0, psi1=0.0, psi2=0.0))
    loads.add(Load(name="WX", load_type=LoadType.WIND, gamma_fav=0.0, gamma_unf=1.5, psi0=0.6, psi1=0.2, psi2=0.0))
    loads.add(Load(name="WY", load_type=LoadType.WIND, gamma_fav=0.0, gamma_unf=1.5, psi0=0.6, psi1=0.2, psi2=0.0))
    # loads.add(Load(name="T", load_type=LoadType.TEMPERATURE, gamma_fav=0.0, gamma_unf=1.5, psi0=0.3, psi1=0.0, psi2=0.2))
    # loads.add(Load(name="Text", load_type=LoadType.TEMPERATURE, gamma_fav=0.0, gamma_unf=1.5, psi0=0.3, psi1=0.0, psi2=0.1))
    loads.add(Load(name="S", load_type=LoadType.SNOW, gamma_fav=0.0, gamma_unf=1.5, psi0=0.5, psi1=0.2, psi2=0.0))
    loads.add(Load(name="E", load_type=LoadType.EARTHQUAKE, gamma_fav=0.0, gamma_unf=1.0, psi0=0.0, psi1=0.0, psi2=0.0))
    # loads.add(Load(name="E2", load_type=LoadType.EARTHQUAKE, gamma_fav=0.0, gamma_unf=1.0, psi0=0.0, psi1=0.0, psi2=0.0))

    # Calculate ULS and SLS combinations
    print("ULS Combinations:")  # noqa: T201
    uls_combinations = loads.get_ULS_combos()
    for key, combo in uls_combinations.items():
        print(key)  # noqa: T201
        for load_name, (__load, factor) in combo.factors.items():
            print(f"  {load_name}: {factor}")  # noqa: T201
    print("\nSLS Combinations:")  # noqa: T201
    sls_combinations = loads.get_SLS_combos()
    for key, combo in sls_combinations.items():
        print(key)  # noqa: T201
        for load_name, (__load, factor) in combo.factors.items():
            print(f"  {load_name}: {factor}")  # noqa: T201
