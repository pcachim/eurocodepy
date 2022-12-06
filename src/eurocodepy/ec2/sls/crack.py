import numpy as np
import math
from .. import stress


def annexLL(fctm: float, fcm: float, 
                sigxx: float, sigyy: float, sigzz: float, 
                sigxy: float, sigyz: float, sigzx: float) -> bool:
        invar = stress.invariants(sigxx, sigyy, sigzz, sigxy, sigyz, sigzx)
        k = fctm/fcm
        c1 = 1.0/(0.7*k**0.9)
        c2 = 1.0 - 6.8*(k-0.07)**2
        alpha = 1.0/(9.0*k**1.4)
        beta = 1.0/(3.7*k**1.1)
        I1 = invar[0] / fcm
        J2 = invar[1] / fcm / fcm
        cos3t = invar[8]
        ang = math.acos(abs(c2 * cos3t))/3.0
        lamb = c1 * math.cos(ang) if cos3t >= 0 else c1 * (math.pi/3.0-ang)
        crack = alpha*J2 + lamb*math.sqrt(J2) + beta*I1 - 1.0
        return True if crack > 0 else False


