"""calc_asl_nm_strain (vectorised grid, fewer bisection steps) against the frozen
previous implementation in ``_strain_reference_v1``: same areas, same verdicts."""
import itertools
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import _strain_reference_v1 as ref  # noqa: E402

from eurocodepy.ec2.uls.bend_axial import calc_asl_nm_strain  # noqa: E402

SECTIONS = [(0.3, 0.5, 0.04, 0.04, 30.0, 500.0),
            (0.25, 0.6, 0.05, 0.03, 25.0, 500.0),
            (0.4, 0.4, 0.04, 0.04, 50.0, 400.0),
            (0.2, 0.3, 0.035, 0.035, 90.0, 500.0)]
MOMENTS = [0.0, 20.0, -20.0, 150.0, -150.0, 400.0, -700.0]
AXIALS = [-300.0, -50.0, 0.0, 100.0, 600.0, 1500.0, 3000.0, 9000.0]


@pytest.mark.parametrize("sec", SECTIONS)
def test_matches_the_previous_implementation(sec):
    b, h, d1, d2, fck, fyk = sec
    for med, ned in itertools.product(MOMENTS, AXIALS):
        new = calc_asl_nm_strain(b, h, d1, d2, med, ned, fck, fyk)
        old = ref.calc_asl_nm_strain(b, h, d1, d2, med, ned, fck, fyk)
        assert new["feasible"] == old["feasible"], (sec, med, ned)
        assert new["note"] == old["note"], (sec, med, ned)
        # Above 4 % Ac ("enlarge the section") the equilibrium has two roots in x
        # and the old bisection landed on either one, sometimes tripping its
        # x1.001 safety margin; the design there is only indicative, 0.2 % is fine.
        rel = 2e-3 if "4%" in old["note"] else 1e-6
        for key in ("As1", "As2", "x"):
            assert new[key] == pytest.approx(old[key], rel=rel, abs=1e-6), \
                (sec, med, ned, key)
