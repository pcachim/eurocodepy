"""CHS catalogue consistency: a circular tube is axisymmetric, so the minor-axis
properties must equal the major-axis ones, and IT = 2·Iy, WT = 2·Wel."""
import pytest

from eurocodepy import dbase


def test_chs_minor_axis_equals_major_axis():
    for r in dbase.SteelCHSProfiles:
        name = r["Section"]
        assert r["Iz"] == pytest.approx(r["Iy"], rel=1e-9), name
        assert r["iz"] == pytest.approx(r["iy"], rel=1e-9), name
        assert r["Wel_z"] == pytest.approx(r["Wel_y"], rel=1e-9), name
        assert r["Wpl_z"] == pytest.approx(r["Wpl_y"], rel=1e-9), name
        assert r["IT"] == pytest.approx(2 * r["Iy"], rel=1e-3), name
        assert r["WT"] == pytest.approx(2 * r["Wel_y"], rel=2e-2), name
