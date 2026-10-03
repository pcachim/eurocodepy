"""Tests for the calculation-report ("explain mode") of the EC3 member check.

The core invariant: passing a ``trace`` must NOT change the computed result — the
report only *records* what was computed. Also checks the report structure and the
convenience renderers.

Run on Python >= 3.11 with eurocodepy importable:
    pytest tests/test_calc_report.py
"""
import dataclasses

import pytest

from eurocodepy.ec3.uls import member_buckling as mb
from eurocodepy.calc_report import CalcReport, SCHEMA_VERSION

# IPE300, as in test_ec3_member_check.
IPE300 = dict(
    area=5381.0, w_y=628400.0, w_z=125200.0,
    iy=8.356e7, iz=6.038e6, it=1.975e5, iw=1.2426e11,
    curve_y="a", curve_z="b", curve_lt="b", fy=275.0, section_class=1,
)

CASES = [
    dict(n_ed=300.0, my_ed=0.0, mz_ed=0.0, lcr_y=4000.0, lcr_z=4000.0),
    dict(n_ed=300.0, my_ed=50.0, mz_ed=0.0, lcr_y=4000.0, lcr_z=4000.0,
         l_lt=4000.0, cmy=0.9, cmz=0.9, cm_lt=0.9),
    dict(n_ed=200.0, my_ed=40.0, mz_ed=10.0, lcr_y=6000.0, lcr_z=3000.0,
         cmy=0.9, cmz=0.9, cm_lt=0.9),
    dict(n_ed=300.0, my_ed=50.0, mz_ed=0.0, lcr_y=4000.0, lcr_z=4000.0,
         susceptible_lt=False),
]


def _fields_without_details(r):
    d = dataclasses.asdict(r)
    d.pop("details", None)
    return d


@pytest.mark.parametrize("case", CASES)
def test_trace_does_not_change_result(case):
    """The identical-result invariant: trace on/off yields the same result."""
    inp = mb.MemberInput(**case, **IPE300)
    r_plain = mb.eurocode3_member_check(inp)
    rep = CalcReport(title="test")
    r_trace = mb.eurocode3_member_check(inp, trace=rep)
    assert _fields_without_details(r_plain) == _fields_without_details(r_trace)
    # details dict is untouched by tracing too
    assert r_plain.details == r_trace.details


def test_report_structure_and_key_steps():
    inp = mb.MemberInput(n_ed=300.0, my_ed=50.0, mz_ed=10.0,
                         lcr_y=6000.0, lcr_z=3000.0, l_lt=3000.0,
                         cmy=0.9, cmz=0.9, cm_lt=0.9, **IPE300)
    rep = CalcReport(title="Member M12 — EC3 §6.3.3")
    mb.eurocode3_member_check(inp, trace=rep)

    # sections in order
    titles = [s.title for s in rep.sections]
    assert titles[0] == "Inputs"
    assert any("Flexural buckling" in t for t in titles)
    assert any("Combined check" in t for t in titles)

    # every step has a symbol and a value
    steps = [st for s in rep.sections for st in s.steps]
    assert steps and all(st.symbol for st in steps)

    # the two interaction equations are verifications (carry an ok flag)
    by_symbol = {st.symbol: st for st in steps}
    assert by_symbol["Eq. (6.61)"].ok in (True, False)
    assert by_symbol["Eq. (6.62)"].ok in (True, False)
    # a representative step carries clause + expr + latex
    chi = by_symbol["χ_y"]
    assert chi.clause and chi.expr and chi.latex


def test_renderers():
    inp = mb.MemberInput(n_ed=300.0, my_ed=50.0, lcr_y=4000.0, lcr_z=4000.0,
                         cmy=0.9, cmz=0.9, cm_lt=0.9, **IPE300)
    rep = CalcReport(title="report")
    mb.eurocode3_member_check(inp, trace=rep)

    d = rep.to_dict()
    assert d["schema_version"] == SCHEMA_VERSION
    assert d["sections"] and d["sections"][0]["steps"]

    md = rep.to_markdown()
    assert "# report" in md
    assert "Eq. (6.61)" in md


# ── §6.2 cross-section check ────────────────────────────────────────────────

from eurocodepy.ec3.uls import cross_section as cs

IPE300_SEC = dict(
    kind="I", section_class=1, fy=275.0, gamma_M0=1.0,
    area=5381.0, b=150.0, h=300.0, tw=7.1, tf=10.7, hw=248.6, eps=0.924,
    wpl_y=628400.0, wpl_z=125200.0, wel_y=557000.0, wel_z=80500.0,
    wt=20100.0, av_y=3210.0, av_z=2568.0,
)
SEC_FORCES = [
    cs.SectionForces(n_ed=300.0, my_ed=80.0, mz_ed=10.0, vz_ed=120.0),
    cs.SectionForces(n_ed=100.0, my_ed=40.0, vy_ed=50.0, vz_ed=200.0, t_ed=3.0),
    cs.SectionForces(n_ed=500.0),
]


@pytest.mark.parametrize("forces", SEC_FORCES)
def test_section_trace_does_not_change_result(forces):
    inp = cs.SectionResistanceInput(**IPE300_SEC)
    r_plain = cs.eurocode3_section_check(inp, forces)
    rep = CalcReport()
    r_trace = cs.eurocode3_section_check(inp, forces, trace=rep)
    assert _fields_without_details(r_plain) == _fields_without_details(r_trace)
    assert r_plain.details == r_trace.details


def test_section_report_structure():
    inp = cs.SectionResistanceInput(**IPE300_SEC)
    rep = CalcReport(title="Section IPE300 — EC3 §6.2")
    cs.eurocode3_section_check(inp, SEC_FORCES[1], trace=rep)  # N+M+V+T case
    titles = [s.title for s in rep.sections]
    assert titles[0] == "Inputs"
    assert any("Shear resistance" in t for t in titles)
    assert any("Torsion" in t for t in titles)
    assert any("Combined" in t for t in titles)
    steps = {st.symbol: st for s in rep.sections for st in s.steps}
    assert steps["Utilisation"].ok in (True, False)
    assert steps["V_pl,Rd,y"].clause and steps["V_pl,Rd,y"].subst


# ── EC2 §6.1 flexure + axial (rectangular RC) ───────────────────────────────

from eurocodepy.ec2.uls.bend_axial import calc_asl_nm

RC_CASES = [
    dict(b=0.30, h=0.50, d1=0.05, d2=0.05, med=150.0, ned=0.0,
         fck=30.0, fyk=500.0),
    dict(b=0.30, h=0.60, d1=0.05, d2=0.05, med=400.0, ned=200.0,
         fck=30.0, fyk=500.0),
]


@pytest.mark.parametrize("case", RC_CASES)
def test_ec2_flexure_trace_does_not_change_result(case):
    r_plain = calc_asl_nm(**case)
    rep = CalcReport()
    r_trace = calc_asl_nm(**case, trace=rep)
    assert r_plain == r_trace


def test_ec2_flexure_report_structure():
    rep = CalcReport(title="RC section — EC2 §6.1")
    calc_asl_nm(**RC_CASES[1], trace=rep)
    steps = {st.symbol: st for s in rep.sections for st in s.steps}
    assert steps["μ"].clause and steps["μ"].latex
    assert "f_cd" in steps and "A_s1 (tension)" in steps


# ── EC5 timber cross-section / member ───────────────────────────────────────

def _timber_fixture():
    from eurocodepy.ec5.uls.cross_section import (TimberSectionInput,
                                                  TimberForces)
    from eurocodepy.ec5.materials import (TimberClass, ServiceClass,
                                          LoadDuration)
    from eurocodepy.utils import RectangularCrossSection
    inp = TimberSectionInput(
        section=RectangularCrossSection(0.10, 0.24),
        timber=TimberClass("C24"),
        service_class=ServiceClass.SC1,
        load_duration=LoadDuration.MediumDuration,
        l_0y=3000.0, l_0z=3000.0, l_0m=3000.0)
    forces = TimberForces(n_ed=-50.0, my_ed=8.0, vz_ed=10.0)
    return inp, forces


def test_ec5_trace_does_not_change_result():
    from eurocodepy.ec5.uls.cross_section import eurocode5_section_check
    inp, forces = _timber_fixture()
    r_plain = eurocode5_section_check(inp, forces)
    rep = CalcReport()
    r_trace = eurocode5_section_check(inp, forces, trace=rep)
    assert _fields_without_details(r_plain) == _fields_without_details(r_trace)


def test_ec5_report_structure():
    from eurocodepy.ec5.uls.cross_section import eurocode5_section_check
    inp, forces = _timber_fixture()
    rep = CalcReport(title="Timber section — EC5")
    eurocode5_section_check(inp, forces, trace=rep)
    titles = [s.title for s in rep.sections]
    assert any("Stability" in t for t in titles)
    assert any("Bending + axial" in t for t in titles)
    assert any("Shear" in t for t in titles)
    steps = {st.symbol: st for s in rep.sections for st in s.steps}
    assert steps["Utilisation"].ok in (True, False)


# ── EC2 §6.2 shear (composite) ──────────────────────────────────────────────

from eurocodepy.ec2.uls.shear_check import (eurocode2_shear_check, ShearInput)
from eurocodepy.ec2.uls import calc_vrdc, calc_asws

SHEAR_INP = ShearInput(b=0.30, d=0.55, fck=30.0, fyk=500.0, as_long=0.0016)


@pytest.mark.parametrize("v_ed", [80.0, 300.0, 3000.0])
def test_ec2_shear_trace_does_not_change_result(v_ed):
    r0 = eurocode2_shear_check(SHEAR_INP, v_ed)
    rep = CalcReport()
    r1 = eurocode2_shear_check(SHEAR_INP, v_ed, trace=rep)
    assert _fields_without_details(r0) == _fields_without_details(r1)


def test_ec2_shear_regimes():
    assert eurocode2_shear_check(SHEAR_INP, 80.0).mode == "no_shear_reinf"
    assert eurocode2_shear_check(SHEAR_INP, 300.0).mode == "stirrups"
    assert eurocode2_shear_check(SHEAR_INP, 3000.0).crushing is True


def test_ec2_shear_matches_scalar_helpers():
    """Parity guard for the Phase-3 migration: the composite must reproduce the
    scalar formulae it orchestrates."""
    i = SHEAR_INP
    rho_l = min(i.as_long / (i.b * i.d), 0.02)
    _vmin, _vc, vrdc = calc_vrdc(i.b, i.d, i.fck, i.gamma_c, rho_l)
    # below V_Rd,c → no designed stirrups (only the §9.2.2 minimum)
    below = eurocode2_shear_check(i, 0.5 * vrdc)
    assert below.mode == "no_shear_reinf"
    assert below.vrd_c == pytest.approx(float(vrdc))
    # above → stirrups at cot θ = 2.5, matching calc_asws at that angle
    v = 2.0 * float(vrdc)
    asw25, _ = calc_asws(i.b, i.d, i.fck, i.gamma_c, i.fyk, i.gamma_s, 2.5, v)
    r = eurocode2_shear_check(i, v)
    assert r.cot == 2.5 and r.asw_s == pytest.approx(float(asw25))


def test_ec2_shear_report_structure():
    rep = CalcReport(title="RC shear — EC2 §6.2")
    eurocode2_shear_check(SHEAR_INP, 300.0, trace=rep)
    titles = [s.title for s in rep.sections]
    assert any("Concrete shear" in t for t in titles)
    assert any("truss" in t.lower() for t in titles)
    steps = {st.symbol: st for s in rep.sections for st in s.steps}
    assert steps["A_sw /s"].clause and steps["V_Rd,max"].clause


# ── EC2 §6.4 punching (composite) ───────────────────────────────────────────

from eurocodepy.ec2.uls.punch_check import (eurocode2_punching_check,
                                            PunchInput)


@pytest.mark.parametrize("edition", ["2004", "2023"])
def test_ec2_punching_trace_does_not_change_result(edition):
    inp = PunchInput(d=0.21, bx=0.40, by=0.40, fck=30.0, fyk=500.0,
                     edition=edition)
    r0 = eurocode2_punching_check(inp, n_ed=400.0, rho_l=0.008)
    rep = CalcReport()
    r1 = eurocode2_punching_check(inp, n_ed=400.0, rho_l=0.008, trace=rep)
    assert _fields_without_details(r0) == _fields_without_details(r1)


def test_ec2_punching_2004_vrd_max_is_strut_crushing():
    """Parity guard: :2004 v_Rd,max = 0.5·ν·f_cd."""
    inp = PunchInput(d=0.21, bx=0.40, by=0.40, fck=30.0, fyk=500.0,
                     gamma_c=1.5, alpha_cc=1.0, edition="2004")
    r = eurocode2_punching_check(inp, n_ed=400.0, rho_l=0.008)
    nu = 0.6 * (1.0 - 30.0 / 250.0)
    fcd = 1.0 * 30.0 / 1.5
    assert r.v_rd_max == pytest.approx(0.5 * nu * fcd)


def test_ec2_punching_2023_vrd_max_is_eta_sys_vrdc():
    """Parity guard: :2023 v_Rd,max = η_sys·v_Rd,c."""
    inp = PunchInput(d=0.21, bx=0.40, by=0.40, fck=30.0, fyk=500.0,
                     eta_sys=1.5, edition="2023")
    r = eurocode2_punching_check(inp, n_ed=400.0, rho_l=0.008)
    assert r.v_rd_max == pytest.approx(1.5 * r.v_rdc)


def test_ec2_punching_report_structure():
    inp = PunchInput(d=0.21, bx=0.20, by=0.20, fck=30.0, fyk=500.0,
                     edition="2023")
    rep = CalcReport(title="Punching — prEN 2023")
    eurocode2_punching_check(inp, n_ed=700.0, rho_l=0.006, trace=rep)
    titles = [s.title for s in rep.sections]
    assert any("Control perimeters" in t for t in titles)
    assert any("Resistance" in t for t in titles)
    assert titles[-1] == "Verdict"


if __name__ == "__main__":  # allow `python tests/test_calc_report.py`
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
