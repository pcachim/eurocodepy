"""Vectorised crack_opening_rect / is_cracked_rect against the scalar functions."""
import numpy as np
import pytest

from eurocodepy.ec2.materials import Concrete
from eurocodepy.ec2.sls import crack_opening, crack_opening_rect, is_cracked, is_cracked_rect


@pytest.mark.parametrize("fck,b,h,cover", [(30, 0.3, 0.5, 0.04), (25, 0.25, 0.7, 0.05),
                                           (50, 0.4, 0.4, 0.035)])
def test_matches_the_scalar_functions(fck, b, h, cover):
    rng = np.random.default_rng(7)
    n = 300
    As = rng.uniform(4e-4, 4e-3, n)
    Asc = rng.uniform(2e-4, 3e-3, n)
    M = rng.uniform(0.0, 400.0, n)
    N = np.concatenate([rng.uniform(-600.0, 3000.0, n - 4), [0.0, 5e-4, -5e-4, 1500.0]])
    ds, dsc, phi, k_t = h - cover, cover, 0.016, 0.4
    conc = Concrete.from_fck(fck)
    wk = crack_opening_rect(b, h, phi, As, ds, Asc, dsc, conc, "A500NR", M, N, k_t)
    cr = is_cracked_rect(b, h, As, ds, Asc, dsc, conc, M, N)
    for i in range(n):
        a1, a2, a3, a4 = (np.array([v]) for v in (As[i], ds, Asc[i], dsc))
        ref_wk = float(np.max(crack_opening(b, h, phi, a1, a2, a3, a4, conc, "A500NR",
                                            np.array([M[i]]), np.array([N[i]]), k_t)))
        ref_cr = bool(is_cracked(b, h, a1, a2, a3, a4, conc, "A500NR",
                                 np.array([M[i]]), np.array([N[i]])))
        assert cr[i] == ref_cr, i
        if np.isnan(ref_wk):
            assert np.isnan(wk[i]), i
        else:
            assert wk[i] == pytest.approx(ref_wk, rel=1e-9, abs=1e-12), i
