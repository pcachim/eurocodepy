from math import *
from typing import Tuple, Dict, List
import eurocodepy as ec


def bend_ast(b: float=0.3, d: float=0.5, med: float=100.0, fck: float=20.0, fyk: float=400.0) -> Tuple[float, float, float, float]:
    """[summary]

    Args:
        b (float, optional): [description]. Defaults to 0.3.
        d (float, optional): [description]. Defaults to 0.5.
        med (float, optional): [description]. Defaults to 100.0.
        fck (float, optional): [description]. Defaults to 20.0.
        fyk (float, optional): [description]. Defaults to 400.0.

    Returns:
        Tuple[float, float, float, float]: [description]
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
    return ast, epss, omega, miu


def bend_ast_asc():
    return


def bend_mrd():
    return


def bend_params(conc:str='C20/25')->Tuple[float, float]:
    n = ec.ConcreteClasses[conc]['n']
    epsc2 = ec.ConcreteClasses[conc]['epsc2']
    epscu2 = ec.ConcreteClasses[conc]['epscu2']
    epsc12 = epsc2/epscu2
    chi1 = 1.0-epsc12/(n+1)
    chi2 = 1.0-((n+1)*(n+2)*0.5-epsc12**2)/((n+1)*(n+2)*chi1)
    chi = 0.5*chi1/chi2
    return chi1, chi2, chi
    