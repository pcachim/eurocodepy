# Copyright (c) 2025 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Eurocode 2 ULS — **EN 1992-1-1:2023** flavour.

This package mirrors :mod:`eurocodepy.ec2.uls`, exposing the same names, and
overrides only the calculations for which the 2023 generation of EC2 is already
implemented — currently **punching shear**, **shear** (8.2), **torsion** (8.3, with
the combined shear+torsion check), **membrane/slab design** (Annex G) and the **detailing rules** (Clause 12,
``uls2023.detailing``). Every
other check (bending) is re-used from the shared EN 1992-1-1:2004
modules until a 2023 version exists, so ``ec2.uls`` and ``ec2.uls2023`` are
drop-in swappable.

    from eurocodepy.ec2 import uls2023 as uls
    uls.calc_vrdcp(...)                  # 2023 punching
    uls.shear.calc_taurdc(...)           # 2023 shear formulae (8.2)
    uls.eurocode2_shear_check(...)       # 2023 shear check (new ShearInput)
    uls.calc_vrd(...)                    # 2004 shear functions (``calc_vrdc`` ...)
"""

# Re-export the whole EN 1992-1-1:2004 ULS surface…
from eurocodepy.ec2.uls import *  # ruff: ignore[undefined-local-with-import-star]
from eurocodepy.ec2.uls import __all__ as _uls_all

# …then override the punching submodule and its functions with the 2023 model.
from eurocodepy.ec2.uls2023 import punch as punch
from eurocodepy.ec2.uls2023.punch import (
    calc_perimeters as calc_perimeters,
)
from eurocodepy.ec2.uls2023.punch import (
    calc_vedp as calc_vedp,
)
from eurocodepy.ec2.uls2023.punch import (
    calc_vrdcminp as calc_vrdcminp,
)
from eurocodepy.ec2.uls2023.punch import (
    calc_vrdcp as calc_vrdcp,
)

# …the shear formulae and the shear check (EN 1992-1-1:2023 Clause 8.2)…
import importlib as _importlib

# (the submodule is imported by name so that it replaces the 2004 ``shear`` that the
# star import above put in this namespace)
shear = _importlib.import_module("eurocodepy.ec2.uls2023.shear")
shear_check = _importlib.import_module("eurocodepy.ec2.uls2023.shear_check")
detailing = _importlib.import_module("eurocodepy.ec2.uls2023.detailing")  # Clause 12
from eurocodepy.ec2.uls2023.shear_check import (
    ShearInput as ShearInput,
    ShearResult as ShearResult,
    eurocode2_shear_check as eurocode2_shear_check,
)

# …and the column check (no override yet -- see column.py's own docstring).
from eurocodepy.ec2.uls2023 import column as column
from eurocodepy.ec2.uls2023.column import (
    ColumnInput as ColumnInput,
    ColumnResult as ColumnResult,
    RebarLayout as RebarLayout,
    biaxial_interaction_exponent as biaxial_interaction_exponent,
    design_column_reinforcement as design_column_reinforcement,
    effective_length as effective_length,
    eurocode2_column_check as eurocode2_column_check,
    maximum_column_reinforcement_m2 as maximum_column_reinforcement_m2,
    minimum_column_reinforcement_m2 as minimum_column_reinforcement_m2,
    nominal_curvature_e2 as nominal_curvature_e2,
    nominal_stiffness_moment as nominal_stiffness_moment,
    slenderness_limit as slenderness_limit,
    uniaxial_moment_resistance as uniaxial_moment_resistance,
)

# …the Annex G design of membrane, shell and slab elements (``slab_design`` is not a drop-in
# for ``slab_check``: it takes the design moments of the element, not Wood-Armer moments,
# so it keeps its own module and names)…
annex_g = _importlib.import_module("eurocodepy.ec2.uls2023.annex_g")
membrane_check = _importlib.import_module("eurocodepy.ec2.uls2023.membrane_check")
slab_design = _importlib.import_module("eurocodepy.ec2.uls2023.slab_design")
from eurocodepy.ec2.uls2023.membrane_check import (
    MembraneInput as MembraneInput,
    MembraneResult as MembraneResult,
    eurocode2_membrane_check as eurocode2_membrane_check,
)

# …the torsion design (EN 1992-1-1:2023 8.3) and the combined shear+torsion check.
torsion = _importlib.import_module("eurocodepy.ec2.uls2023.torsion")
shear_torsion = _importlib.import_module("eurocodepy.ec2.uls2023.shear_torsion")
from eurocodepy.ec2.uls2023.torsion import calc_torsion as calc_torsion
from eurocodepy.ec2.uls2023.shear_torsion import (
    ShearTorsionInput as ShearTorsionInput,
    ShearTorsionResult as ShearTorsionResult,
    distribute_torsion_longitudinal as distribute_torsion_longitudinal,
    eurocode2_shear_torsion_check as eurocode2_shear_torsion_check,
)

__all__ = list(_uls_all)
