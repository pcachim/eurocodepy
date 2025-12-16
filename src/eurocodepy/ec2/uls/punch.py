# Copyright (c) 2025 Paulo Cachim
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See the project's LICENSE file for details.

import numpy as np


def calc_perimeters(
    dv: float,
    bxord: float,
    by: float | object = None,
    position: str = "center",
    dx: float = 0.0,
    dy: float = 0.0
) -> tuple[float, float]:
    """Calculate the perimeters for punching.

    The critical sections are located at the face of column and at a
    distance of 0.5*d from the critical section.

    Args:
        dv (float): Effective depth [mm].
        bxord (float): Dimension of the column or concentrated load in x direction [mm].
        by (float or object, optional): Dimension of the column or concentrated
        load in y direction [mm]. If None, a square section is assumed. Default None.
        position (str, optional): Position of the load with respect to the slab. Can be
                "center", "edge" or "corner". By default "center".
        dx (float, optional): Distance to x border [mm]. Defaults to 0.0.
        dy (float, optional): Distance to y border [mm]. Defaults to 0.0.

    Returns:
        tuple[float, float]: Perimeter of the critical section [mm], perimeter of the
                section located at a distance of 0.5*d from the critical section [mm].

    """
    if by is None:
        # Circular column
        d0 = bxord
        d1 = d0 + dv
        if position == "edgex":
            b0 = np.pi * d0 / 2.0 + d0 + dx
            b05 = np.pi * d1 / 2.0 + d0 + dx
            bb = np.sqrt(d1 * (d0 + 0.5 * dv + dx / 2.0))
        elif position == "edgey":
            b0 = np.pi * d0 / 2.0 + d0 + dy
            b05 = np.pi * d1 / 2.0 + d0 + dy
            bb = np.sqrt(d1 * (d0 + 0.5 * dv + dy / 2.0))
        elif position == "corner":
            b0 = np.pi * d0 / 4.0 + d0 + (dx + dy) / 2.0
            b05 = np.pi * d1 / 4.0 + d0 + (dx + dy) / 2.0
            bb = np.sqrt((d0 + 0.5 * dv + dx / 2.0) * (d0 + 0.5 * dv + dy / 2.0))
        else:
            b0 = np.pi * d0
            b05 = np.pi * (d0 + dv)
            bb = d1
    # Rectangular column
    elif position == "edgex":
        b0 = 2.0 * bxord + by
        b05 = b0 + np.pi * dv / 2.0 + dx
        bb = np.sqrt((bxord + dx / 2.0) * (by + dv))
    elif position == "edgey":
        b0 = bxord + 2.0 * by
        b05 = b0 + np.pi * dv / 2.0 + dy
        bb = np.sqrt((bxord + dv) * (by + dy / 2.0))
    elif position == "corner":
        b0 = bxord + by
        b05 = b0 + np.pi * dv / 4.0 + (dx + dy) / 2.0
        bb = np.sqrt((bxord + dx / 2.0) * (by + dy / 2.0))
    else:
        b0 = 2.0 * (bxord + by)
        b05 = b0 + np.pi * dv
        bb = np.sqrt((bxord + dv) * (by + dv))
    return b0, b05, bb


def calc_vedp(  # noqa: PLR0913, PLR0917
    ned: float | np.ndarray,
    medx: float | np.ndarray,
    medy: float | np.ndarray,
    dv: float,
    bxord: float,
    by: float | object = None,
    position: str = "center",
    dx: float = 0.0,
    dy: float = 0.0
    ) -> float | np.ndarray:
    """Calculate design punching shear force.

    Args:
        ned (float or np.ndarray): Design axial force [kN].
        medx (float or np.ndarray): Design bending moment about x-axis [kNm].
        medy (float or np.ndarray): Design bending moment about y-axis [kNm].
        dv (float): Effective depth [mm].
        bxord (float): Dimension of the column or concentrated load in x direction [mm].
        by (float or object, optional): Dimension of the column or
                concentrated load in y direction [mm]. If None, a square section
                is assumed. By default None.
        position (str, optional): Position of the load with respect to the slab. Can be
                "center", "edge" or "corner". By default "center".
        dx (float, optional): Distance to x border [mm]. Defaults to 0.0.
        dy (float, optional): Distance to y border [mm]. Defaults to 0.0.

    Returns:
        float or np.ndarray: Design punching shear force [kN].

    Raises:
        ValueError: If position is not "center", "edge" or "corner".

    """
    # Calculate perimeters
    position = position.lower()
    if position in {"center", "internal", "centre"}:
        position = "center"
    b0, b05, bb = calc_perimeters(dv, bxord, by, 
                                position=position, dx=dx, dy=dy)

    # Calculate beta values
    ex = medx / ned * 1e3  # [mm]
    ey = medy / ned * 1e3  # [mm]
    if position in {"center", "internal", "centre"}:
        eb = np.sqrt(ex ** 2 + ey ** 2)
    elif position in {"edgex", "edgey", "edge"}:
        eb = 0.5 * np.abs(ex) + np.abs(ey)
    elif position == "corner":
        eb = 0.27 * (np.abs(ex) + np.abs(ey))
    else:
        msg = 'Position must be "center", "edge" or "corner".'
        raise ValueError(msg)
    beta = 1.0 + 1.1 * eb / bb
    beta = np.where(beta < 1.05, 1.05, beta)  # noqa: PLR2004

    # Calculate ved
    ved = ned / b05 / dv
    return beta * ved * 1e3  # [N/mm²] = [MPa]


def calc_vrdcp(dmax: float, rhol: float,  # noqa: PLR0913, PLR0917
                fck: float,
                dv: float,
                bxord: float,
                by: float | object = None,
                gamma_v: float = 1.4,
                position: str = "center",
                dx: float = 0.0,
                dy: float = 0.0
                ) -> float | np.ndarray:
    """Calculate punching shear resistance of concrete slab.

    Args:
        dv (float):  Effective depth [mm].
        b0 (float): Perimeter of the critical section [mm].
        b05 (float): Perimeter of the section located at a distance of 0.5*d
                    from the critical section [mm].
        dmax (float): Maximum aggregate size [mm].
        rhol (float): Longitudinal reinforcement ratio.
        fck (float): Characteristic compressive cylinder strength of concrete [MPa].
        gamma_v (float, optional): Partial safety factor for shear, by default 1.4.

    Returns:
        float or np.ndarray: Punching shear resistance of concrete slab [MPa].

    """
    b0, b05, bd  = calc_perimeters(dv, bxord, by,
                            position=position, dx=dx, dy=dy)  # noqa: RUF059
    kpb = max(1.0, min(3.6 * np.sqrt(1.0 - (b0 / b05)), 2.5))
    ddg = 16.0 + dmax * min(1.0, (60.0 / fck)**2)
    vrdc1 = 0.6 * kpb * (100.0 * rhol * fck * ddg / dv) ** (1.0 / 3.0) / gamma_v
    vrdc2 = 0.5 * np.sqrt(fck) / gamma_v
    return max(vrdc1, vrdc2)


def calc_vrdcminp(fck: float,
                    fyd: float,
                    dv: float,
                    dmax: float = 20.0,
                    gamma_v: float = 1.4,
                    ) -> float | np.ndarray:
    """Calculate minimum punching shear resistance of concrete slab.

    Args:
        fck (float): Characteristic compressive cylinder strength of concrete [MPa].
        fyd (float): Design tensile strength of reinforcement [MPa].
        dv (float): Effective depth [mm]. Defaults to 20 mm.
        gamma_v (float, optional): Partial safety factor for shear, by default 1.4.

    Returns:
        float or np.ndarray: Minimum punching shear resistance of concrete slab [MPa].

    """
    ddg = 16.0 + dmax * min(1.0, (60.0 / fck)**2)
    return 11.0 * np.sqrt((fck / fyd) * (ddg / dv) ) / gamma_v
