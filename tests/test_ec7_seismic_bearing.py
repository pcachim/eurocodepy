"""EN 1998-5 Annex F: seismic bearing resistance of shallow foundations (it used to raise on every call)."""
import numpy as np

from eurocodepy.ec7 import seismic_bearing_resistance

PHI = np.radians(30.0)


def test_incoherent_soil_verified_and_not_verified():
    args = (0.2, 0.5, 1.4, 1.5, 20.0)                  # ag, avg/ahg, S, B, H
    assert seismic_bearing_resistance(*args, 200.0, 10.0, PHI, 18.0).tolist() == [True, True]
    assert seismic_bearing_resistance(*args, 5000.0, 10.0, PHI, 18.0).tolist() == [False, False]


def test_out_of_domain_is_not_verified():
    # a negative vertical force (uplift) or one beyond Nmax is outside the criterion: never "verified"
    assert not seismic_bearing_resistance(0.2, 0.5, 1.4, 1.5, 20.0, -10.0, 10.0, PHI, 18.0).any()


def test_coherent_soil_uses_the_undrained_strength():
    args = (0.2, 0.5, 1.4, 1.5, 20.0)
    ok = seismic_bearing_resistance(*args, 100.0, 10.0, PHI, 18.0, cu=60.0, soil_type="coherent")
    no = seismic_bearing_resistance(*args, 400.0, 10.0, PHI, 18.0, cu=60.0, soil_type="coherent")
    assert ok.tolist() == [True] and no.tolist() == [False]
