"""Tests for the EC2 §6.3 St-Venant torsion design (ec2.uls.torsion.calc_torsion).

Run on Python >= 3.11 with eurocodepy importable:
    pytest tests/test_torsion.py
"""
import math

from eurocodepy.ec2.uls import calc_torsion

# Reference section / materials.
B, H = 0.30, 0.50
FCK, FYK = 30.0, 500.0
GC, GS = 1.5, 1.15
COTT = 1.0                       # theta = 45 degrees


def test_thin_wall_geometry():
    r = calc_torsion(50.0, B, H, FCK, GC, FYK, GS, COTT)
    # t_ef = A/u = (0.3·0.5)/(2·0.8) = 0.09375 m.
    assert abs(r["t_ef"] - 0.09375) < 1e-9
    assert abs(r["A_k"] - (B - r["t_ef"]) * (H - r["t_ef"])) < 1e-12
    assert abs(r["u_k"] - 2 * ((B - r["t_ef"]) + (H - r["t_ef"]))) < 1e-12


def test_reference_values():
    """Hand-checked EC2 §6.3 values for T_Ed = 50 kN·m at theta = 45 degrees."""
    r = calc_torsion(50.0, B, H, FCK, GC, FYK, GS, COTT)
    assert abs(r["TRd_max"] - 82.95) < 0.1          # crushing resistance [kNm]
    assert abs(r["Asw_tor_s"] * 1e4 - 6.86) < 0.05  # cm²/m per leg
    assert abs(r["Asl_tor"] * 1e4 - 8.41) < 0.05    # cm² total
    assert abs(r["util"] - 50.0 / r["TRd_max"]) < 1e-9


def test_torsion_scales_linearly():
    a = calc_torsion(30.0, B, H, FCK, GC, FYK, GS, COTT)
    b = calc_torsion(60.0, B, H, FCK, GC, FYK, GS, COTT)
    assert abs(b["Asw_tor_s"] - 2 * a["Asw_tor_s"]) < 1e-12
    assert abs(b["Asl_tor"] - 2 * a["Asl_tor"]) < 1e-12
    # TRd,max is a section property, independent of the demand.
    assert abs(a["TRd_max"] - b["TRd_max"]) < 1e-9


def test_flatter_strut_reduces_stirrups_and_raises_longitudinal():
    """A flatter strut (larger cot θ) needs fewer stirrups but more longitudinal
    steel — the classic truss trade-off."""
    steep = calc_torsion(50.0, B, H, FCK, GC, FYK, GS, 1.0)
    flat = calc_torsion(50.0, B, H, FCK, GC, FYK, GS, 2.5)
    assert flat["Asw_tor_s"] < steep["Asw_tor_s"]
    assert flat["Asl_tor"] > steep["Asl_tor"]


def test_sign_independent():
    assert calc_torsion(-50.0, B, H, FCK, GC, FYK, GS, COTT)["Asw_tor_s"] == \
        calc_torsion(50.0, B, H, FCK, GC, FYK, GS, COTT)["Asw_tor_s"]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok: {name}")
