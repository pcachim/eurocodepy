# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""Ultimate Limit State (ULS) checks — **EN 1995-1-1:2025** (second generation).

Mirrors :mod:`eurocodepy.ec5.uls` (the EN 1995-1-1:2004 edition) and overrides
only the checks whose expressions changed in the second generation — the bending
+ axial (§8), shear + torsion (§8) and the grouped cross-section verification.
Everything else (``get_safety_factor`` and the force / input / result
dataclasses) is shared, so ``ec5.uls`` and ``ec5.uls2025`` are drop-in
swappable, exactly like ``ec2.uls`` / ``ec2.uls2023``::

    from eurocodepy.ec5 import uls2025 as uls
    uls.check_bending_with_normal(...)   # 2025 §8 forms
"""

# Re-export the whole EN 1995-1-1:2004 ULS surface…
from eurocodepy.ec5.uls import *  # noqa: F401,F403
from eurocodepy.ec5.uls import __all__ as _uls_all

# …then override the bending / shear submodules and their functions with the
# EN 1995-1-1:2025 (§8) versions.
from eurocodepy.ec5.uls2025 import bending as bending
from eurocodepy.ec5.uls2025 import cross_section as cross_section
from eurocodepy.ec5.uls2025 import shear as shear
from eurocodepy.ec5.uls2025.bending import (
    calc_k_c as calc_k_c,
    calc_k_m as calc_k_m,
    calc_k_red as calc_k_red,
    calc_mcr as calc_mcr,
    check_bending_with_normal as check_bending_with_normal,
)
from eurocodepy.ec5.uls2025.cross_section import (
    eurocode5_section_check as eurocode5_section_check,
)
from eurocodepy.ec5.uls2025.shear import (
    check_shear_with_torsion as check_shear_with_torsion,
)

__all__ = list(_uls_all)
