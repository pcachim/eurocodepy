import math
import numpy as np

# useful functions
aval = [0.5, 1, 2, 4]
bval = [150, 120, 80, 50]


def floor_freq(l, EI, m):
    f1 = (math.pi/2/l**2)*math.sqrt(EI/m)
    return f1


def vel(f1, b, l, m, EIl, EIt):
    n40 = math.pow(((40/f1)**2-1.0)*((b/l)**4)*(EIl/EIt), 0.25)
    print(f"n40 = {n40}")
    v = 4*(0.4+0.6*n40)/(m*b*l+200)
    return v


def b_from_a(a):
    return np.interp(a, aval, bval)


def a_from_b(b):
    return np.interp(b, np.flip(bval), aval)


def vlim(f1, b, damp):
    return math.pow(b, f1*damp-1.0)