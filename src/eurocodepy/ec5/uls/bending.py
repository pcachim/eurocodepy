# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT
import numpy as np


def k_h(height: float, timber_type: str = "timber") -> float:
    """Calculate the height factor k_h for bending according to Eurocode 5.

    Args:
        height (float): Height of the timber member in mm.
        timber_type (str): Type of timber ('timber' or 'glulam').

    Returns:
        float: Height factor k_h

    """
    if timber_type not in {"timber", "glulam"}:
        return 1.0

    if timber_type == "timber":
        if height > 0.150:  # noqa: PLR2004
            return 1.0
        return np.minimum((0.150/height)**0.2, 1.3)

    if timber_type == "glulam":
        if height > 0.6:  # noqa: PLR2004
            return 1.0
        return np.minimum((0.60/height)**0.1, 1.1)

    if timber_type == "lvl":
        if height > 0.3:  # noqa: PLR2004
            return 1.0
        return np.minimum((0.3 / height)**0.15, 1.2)

    return 1.0


def k_l(length: float, timber_type: str = "lvl") -> float:
    """Calculate the height factor k_l for tension according to Eurocode 5.

    Args:
        length (float): Length of the timber member in mm.
        timber_type (str): Type of timber ('lvl').

    Returns:
        float: Height factor k_h

    """
    if timber_type != "lvl":
        return 1.0

    if timber_type == "lvl":
        if length > 3.0:  # noqa: PLR2004
            return 1.0
        return np.minimum((3.0/length)**0.075, 1.1)

    return 1.0

