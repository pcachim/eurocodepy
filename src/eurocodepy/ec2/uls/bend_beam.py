from math import *
from typing import Tuple, Dict, List
import eurocodepy as ec


def calc_reinf_beam(b: float, d: float, med: float, fck: float=20.0, fyk: float=400.0) -> Tuple[float, float, float]:
    """Calculates the reinforcement in a rectangular concrete beam.

    Args:
        b (float): bradth of the beam in m.
        d (float): depth of the reinforced in beam in m.
        med (float): bending moment in kNm.
        fck (float, optional): concrete strength in MPa. Defaults to 20.0.
        fyk (float, optional): reinforcement strength in MPa. Defaults to 400.0.

    Returns:
        Tuple[float, float, float, float]: reinforcement area in cm2, strain in reinforcement, neutral axis depth, omega.
    """
    fcd = fck/1.5
    fyd = fyk/1.15
    mmed = med
    bb = b
    dd = d
    miu = mmed/bb/d**2/fcd/1000.0
    try:
        omega = 1.0-sqrt(1-2*miu)
    except:
        omega = nan
    alpha = 1.25*omega
    ast = omega*b*d*fcd/fyd * 10000.0
    epss = (1.0-alpha)*3.5/alpha
    return ast, epss, alpha


def bend_ast_asc():
    return


def calc_mom_beam(b: float, d: float, ast: float, fck: float=20.0, fyk: float=400.0) -> Tuple[float, float, float]:
    """Calculates the bending moment in a rectangular concrete beam.

    Args:
        b (float): bradth of the beam in m.
        d (float): depth of the reinforced in beam in m.
        ast (float): reinforcement area in cm2.
        fck (float, optional): concrete strength in MPa. Defaults to 20.0.
        fyk (float, optional): reinforcement strength in MPa. Defaults to 400.0.

    Returns:
        Tuple[float, float, float]: bending moment in kNm, strain in reinforcement, neutral axis depth.
    """
    fcd = fck/1.5
    fyd = fyk/1.15
    omega = ast*fyd/b/d/fcd/10000.0
    miu = omega*(1-0.5*omega)
    alpha = 1.25*omega
    epss = (1.0-alpha)*3.5/alpha
    mrd = miu*b*d*d*fcd*1000
    return mrd, epss, alpha


def get_bend_params(conc:str='C20/25')->Tuple[float, float]:
    n = ec.ConcreteClasses[conc]['n']
    epsc2 = ec.ConcreteClasses[conc]['epsc2']
    epscu2 = ec.ConcreteClasses[conc]['epscu2']
    epsc12 = epsc2/epscu2
    chi1 = 1.0-epsc12/(n+1)
    chi2 = 1.0-((n+1)*(n+2)*0.5-epsc12**2)/((n+1)*(n+2)*chi1)
    chi = 0.5*chi1/chi2
    return chi1, chi2, chi
    