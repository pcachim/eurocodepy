import numpy as np
import math
from . import utils


def iscracked_annexLL(fctm: float, fcm: float, 
                sigxx: float, sigyy: float, sigzz: float, 
                sigxy: float, sigyz: float, sigzx: float) -> bool:
    """Checks if the point is cracked using expression (LL.101) of Annex LL of EN 1992-2:2005.
    Author. Paulo Cachim (2022)

    Args:
        fctm (float): mean tensile strength of concrete
        fcm (float): mean comprerssive strength of concrete
        sigxx (float): stress xx
        sigyy (float): stress yy
        sigzz (float): stress zz
        sigxy (float): stress xy
        sigyz (float): stress yz
        sigzx (float): stress zx

    Returns:
        bool: True if cracked, False otherwise
    """
    # Calculate stress invariants
    invar = utils.stress.invariants(sigxx, sigyy, sigzz, sigxy, sigyz, sigzx)
    I1 = invar[0] / fcm
    J2 = invar[1] / fcm / fcm
    cos3t = invar[8]
    
    # Calculate auxiliary parameters
    k = fctm/fcm
    c1 = 1.0/(0.7*k**0.9)
    c2 = 1.0 - 6.8*(k-0.07)**2
    alpha = 1.0/(9.0*k**1.4)
    beta = 1.0/(3.7*k**1.1)
    ang = math.acos(abs(c2 * cos3t))/3.0
    lamb = c1 * math.cos(ang) if cos3t >= 0 else c1 * (math.pi/3.0-ang)
    
    # Calculate cracking condition (>0 cracked; <0 uncracked)
    crack = alpha*J2 + lamb*math.sqrt(J2) + beta*I1 - 1.0
    
    # Return cracked stated (True: cracked: False: uncracked)
    return True if crack > 0 else False
