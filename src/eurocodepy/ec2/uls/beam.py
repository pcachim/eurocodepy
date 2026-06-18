# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT

import numpy as np

from eurocodepy.ec2.materials import (
    Concrete,
    C30_37,
    GammaC,
    GammaS,
    Reinforcement,
    get_concrete,
    get_reinforcement,
)

# Shear/torsion checks live in `shear`; import them rather than redefining,
# so a change to a shear formula cannot diverge between the two modules.
from eurocodepy.ec2.uls.shear import (  # noqa: E402
    calc_asws as calc_asws,
    calc_vrd as calc_vrd,
    calc_vrdc as calc_vrdc,
    calc_vrdmax as calc_vrdmax,
)


def calc_asl(b: float, d: float, med: float, fcd: float = 13.7,
        fyd: float = 348.0, iprint: bool = False) -> tuple[float, float, float]:
    """Calculate the reinforcement in a rectangular concrete beam.

    Args:
        b (float): bredth of the beam in m.
        d (float): depth of the reinforced in beam in m.
        med (float): bending moment in kNm.
        fcd (float, optional): concrete strength in MPa. Defaults to 20.0.
        fyd (float, optional): reinforcement strength in MPa. Defaults to 400.0.
        iprint (bool, optional): print results. Defaults to False.

    Returns:
        Tuple[float, float, float, float]: reinforcement area in cm2,
        strain in reinforcement, neutral axis depth, omega.

    """
    mmed = med
    bb = b
    miu = mmed / bb / d**2 / fcd / 1000.0
    try:
        omega = 1.0 - np.sqrt(1 - 2 * miu)
    except ValueError:
        omega = np.nan
    alpha = 1.25 * omega
    ast = omega * b * d * fcd / fyd * 10000.0
    epss = (1.0 - alpha) * 3.5 / alpha
    if iprint:
        print(
            f"miu={miu:.3f} omega={round(omega, 3):.3f} x/d={alpha:.3f} "
            f"eps-s={epss:.3f} As={ast:.2f} cm2",
        )
    return ast, epss, alpha


def calc_mrd(b: float, d: float, ast: float, fcd: float = 20.0, fyd: float = 400.0,
            iprint: bool = False) -> tuple[float, float, float]:
    """Calculate the bending moment in a rectangular concrete beam.

    Args:
        b (float): bredth of the beam in m.
        d (float): depth of the reinforced in beam in m.
        ast (float): reinforcement area in cm2.
        fcd (float, optional): concrete strength in MPa. Defaults to 20.0.
        fyd (float, optional): reinforcement strength in MPa. Defaults to 400.0.
        iprint (bool, optional): print results. Defaults to False.

    Returns:
        Tuple[float, float, float]: bending moment in kNm, strain in reinforcement,
        neutral axis depth.

    """
    omega = ast * fyd / b / d / fcd / 10000.0
    miu = omega * (1 - 0.5 * omega)
    alpha = 1.25 * omega
    epss = (1.0 - alpha) * 3.5 / alpha
    mrd = miu * b * d * d * fcd * 1000
    if iprint:
        print(
            f"med={mrd:.1f} kNm; miu={round(miu, 3):.3f}; "
            f"omega={round(omega, 3):.3f}",
        )
    return mrd, epss, alpha


def get_bend_params(conc: str = "C20/25") -> tuple[float, float, float]:
    """Calculate bending parameters for a given concrete class.

    Args:
        conc (str): Concrete class as a string (e.g., "C20/25").

    Returns:
        tuple[float, float, float]: chi1, chi2, chi parameters for bending calculations.

    """
    concrete = Concrete(conc)
    n = concrete.n
    epsc2 = concrete.eps_c2
    epscu2 = concrete.eps_cu2
    epsc12 = epsc2 / epscu2
    chi1 = 1.0 - epsc12 / (n + 1)
    chi2 = 1.0 - ((n + 1) * (n + 2) * 0.5 - epsc12**2) / ((n + 1) * (n + 2) * chi1)
    chi = 0.5 * chi1 / chi2
    return chi1, chi2, chi


class RCBeam:
    """A reinforced concrete beam object for ULS checks in bending and shear.

    Attributes
    ----------
    b : float
        Breadth of the beam in meters.
    h : float
        Height of the beam in meters.
    at : float
        Tensile reinforcement mechanical cover in meters.
    ac : float
        Compressive reinforcement mechanical cover in meters.
    conc : Union[str, Concrete, ConcreteGrade]
        Concrete class or object.
    reinf : Union[str, Reinforcement, ReinforcementGrade]
        Reinforcement class or object.

    Methods
    -------
    calc_shear(ved: float, cott: float = 2.5)
        Calculate shear parameters for the beam.
    calc_bending(med: float, iprint: bool = False)
        Calculate bending reinforcement for the beam.

    """

    def __init__(self, b: float, h: float, at: float, ac: float,
                conc: str | Concrete = "C20/25",
                reinf: str | Reinforcement = "B500B") -> None:
        """Reinforced concrete beam object.

        Characterized by bredth (b), height (h), reinforcement covers  and materials.
        Checks ULS for bending and shear.

        Args:
            b (float): bredth of the beam in m.
            h (float): height of the beam in m.
            conc (str, optional): concrete class. Defaults to "C25/30".
            reinf (str, optional): reinforcement lass. Defaults to "B500B".
            at (float, optional): tensile reinforcement mechanical cover.
            Defaults to 0.05 m.
            ac (float, optional): compressive reinforcement mechanical cover.
            Defaults to 0.05 m.

        """
        self.concrete = get_concrete(conc)
        self.reinforcement = get_reinforcement(reinf)
        self.b = b
        self.h = h
        self.conc = conc
        self.reinf = reinf
        self.at = at
        self.ac = ac
        self.d = self.h - self.at
        self.fck = self.concrete.fck
        self.fyk = self.reinforcement.fyk
        self.gammac = GammaC
        self.gammas = GammaS
        self.fcd = self.concrete.fcd
        self.fyd = self.reinforcement.fyd

    def calc_shear(self, ved: float,
        cott: float = 2.5) -> tuple[float, float, float, float, float, float, float]:
        """Calculate shear parameters for the reinforced concrete beam.

        Args:
            ved (float): Design shear force.
            cott (float, optional): Truss inclination (cotangent of theta).
            Defaults to 2.5.

        Returns:
            Tuple[float, float, float, float, float, float, float]:
                aslt, aslc, alpha, epsst, epssc, asws, vrdmax

        """
        aslt = 0.0
        aslc = 0.0
        alpha = 0.0
        epsst = 0.0
        epssc = 0.0
        vrdmax = 0.0

        # cotetas = np.arange(1.0, 2.5001, 0.1)  # noqa: ERA001
        # vrdmaxs = calc_vrdmax(self.b, self.d, self.fck, self.gammac, self.fyk, 
        # self.gammas, cotetas)
        # min_val = np.min((lambda i: i > ved, vrdmaxs))  # noqa: ERA001
        # cott = cotetas[i]  # noqa: ERA001

        asws_val, vrdmax = calc_asws(self.b, self.d, self.fck, self.gammac,
                        self.fyk, self.gammas, cott, ved)
        return aslt, aslc, alpha, epsst, epssc, asws_val, vrdmax

    def calc_bending(self, med: float, iprint: bool = False,
                ) -> tuple:
        """Calculate the reinforcement area in a rectangular concrete beam.

        Args:
            med (float): design bending moment in kNm.
            delta (float, optional): redistribution ratio (0.7 to 1.0). Defaults to 1.0
            (no redistribution).
            iprint (bool, optional): prints results to stdout. Defaults to False.

        Returns:
            Tuple[float, float, float, float, float]: reinforcement area in cm2,
            strain in reinforcement, neutral axis depth.

        """
        # Calculate med_max
        alpha_c = self.ac / self.d
        epscu2 = self.concrete.eps_cu2

        alpha_lim = 0.45 if self.fck <= 50 else 0.35  # correct this values for fck > 50
        omega_max = alpha_lim / 1.25
        miu_max = omega_max * (1 - 0.5 * omega_max)
        med_max = miu_max * self.b * self.d * self.d * self.fck / self.gammac * 1000.0

        aslt = 0.0
        aslc = 0.0
        alpha = 0.0
        epsst = 0.0
        epssc = 0.0

        # Check if miu is less than miu-max and calculate reinforcement accordingly
        # if med <= med_max:
        med_eff = np.minimum(med, med_max)
        aslt, epsst, alpha = calc_asl(
            self.b, self.d, med_eff, self.fcd, self.fyd, iprint)
        aslc = np.where(med <= med_max, 0.0,
                    (med - med_max) / ((self.d - self.ac) * self.fyd) * 10.0)
        aslt += aslc
        epssc = np.where(med <= med_max, np.nan, (alpha - alpha_c) / alpha * epscu2)

        return aslt, aslc, alpha, epsst, epssc


if __name__ == "__main__":
    # test RCBeam class
    print("\nTest RCBeam:\n")
    beam = RCBeam(0.3, 0.5, at=0.05, ac=0.05, conc=C30_37, reinf="A500NR")
    a = beam.calc_shear(100.0, 100.0)
    asl, asc, a, epst, epsc = beam.calc_bending(100.0)
    print(f"\n{asl=}, {asc=}, {a=}, {epst=}, {epsc=}")
    asl, asc, a, epst, epsc = beam.calc_bending(500.0)
    print(f"\n{asl=}, {asc=}, {a=}, {epst=}, {epsc=}")
    asl, asc, a, epst, epsc = beam.calc_bending(900.0)
    print(f"\n{asl=}, {asc=}, {a=}, {epst=}, {epsc=}")
