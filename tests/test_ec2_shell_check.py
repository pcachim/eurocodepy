"""Sandwich-model shell design: EN 1992-1-1:2004 basis (ec2.uls) and 2023 Annex G.4 (ec2.uls2023)."""
import math
import warnings

import numpy as np
import pytest

from eurocodepy.calc_report import CalcReport
from eurocodepy.ec2 import uls, uls2023
from eurocodepy.ec2.uls import shell_check as sc

FYD = 500.0 / 1.15


def _inp(cls=uls.ShellInput, **kw):
    base = {"n_xx": 100.0, "n_yy": 50.0, "n_xy": 20.0, "m_xx": 20.0, "m_yy": 10.0,
            "m_xy": 5.0, "fck": 30.0, "fyk": 500.0, "thickness": 0.2, "cover": 0.04}
    base.update(kw)
    if cls is uls.ShellInput:
        base.setdefault("check_cracking", False)    # these tests are about the sandwich model itself
    return cls(**base)


def test_layer_stresses_are_the_sandwich_equations():
    t, z = 0.08, 0.12
    s = sc.layer_stresses((10.0, 5.0, 2.0), (20.0, 10.0, 5.0), t, z)
    assert s["bottom"] == pytest.approx((0.5 * 10 / t + 20 / (t * z), 0.5 * 5 / t + 10 / (t * z),
                                         0.5 * 2 / t - 5 / (t * z)))
    assert s["top"] == pytest.approx((0.5 * 10 / t - 20 / (t * z), 0.5 * 5 / t - 10 / (t * z),
                                      0.5 * 2 / t + 5 / (t * z)))
    # the same as the 2023 Annex G functions
    g = uls2023.annex_g.sandwich_stresses((10.0, 5.0, 2.0), (20.0, 10.0, 5.0), t, z)
    assert s == {k: pytest.approx(v) for k, v in g.items()}


def test_the_composite_is_calc_reinf_shell_with_forces_and_the_layers_named_as_annex_g():
    r = uls.eurocode2_shell_check(_inp())
    t = 0.08
    old = uls.calc_reinf_shell(100.0, 50.0, 20.0, 20.0, 10.0, 5.0, 0.04, 0.2)
    # calc_reinf_shell's "top" layer is the bottom layer here; its values are per unit of thickness
    assert r.asx_bot == pytest.approx(old[0] * t / (FYD * 1e3))
    assert r.asy_bot == pytest.approx(old[1] * t / (FYD * 1e3))
    assert r.asx_top == pytest.approx(old[4] * t / (FYD * 1e3))
    assert r.asy_top == pytest.approx(old[5] * t / (FYD * 1e3))
    assert r.details["t_layer"] == pytest.approx(t) and r.details["z"] == pytest.approx(0.12)


def test_pure_bending_gives_m_over_z_fyd_in_the_tension_layer():
    r = uls.eurocode2_shell_check(_inp(n_xx=0.0, n_yy=0.0, n_xy=0.0, m_xx=30.0, m_yy=0.0, m_xy=0.0))
    assert r.asx_bot == pytest.approx(30.0 / 0.12 / (FYD * 1e3))
    assert r.asy_bot == r.asx_top == r.asy_top == 0.0
    top = r.details["layers"]["top"]                     # uniaxial compression in x, no steel
    assert top["cot"] == math.inf and top["ftdx"] == top["ftdy"] == 0.0
    hog = uls.eurocode2_shell_check(_inp(n_xx=0.0, n_yy=0.0, n_xy=0.0, m_xx=-30.0, m_yy=0.0, m_xy=0.0))
    assert hog.asx_top == pytest.approx(r.asx_bot) and hog.asx_bot == 0.0


def test_axial_tension_is_shared_by_the_two_layers():
    r = uls.eurocode2_shell_check(_inp(n_xx=200.0, n_yy=0.0, n_xy=0.0, m_xx=0.0, m_yy=0.0, m_xy=0.0))
    assert r.asx_bot == r.asx_top == pytest.approx(100.0 / (FYD * 1e3))


def test_strut_check_uses_nu_fcd_and_fcd_without_reinforcement():
    # a heavy torsion: both layers need reinforcement and the struts exceed ν·fcd
    kw = {"n_xx": 0.0, "n_yy": 0.0, "n_xy": 0.0, "m_xx": 0.0, "m_yy": 0.0, "m_xy": 60.0}
    with pytest.warns(UserWarning, match="bottom and top layer.*ν·f_cd"):
        r = uls.eurocode2_shell_check(_inp(**kw))
    nu = 0.6 * (1 - 30.0 / 250.0)                          # Annex F.1(4): ν·fcd, Expression (6.5)
    assert r.crushing and r.details["layers"]["bottom"]["nu"] == pytest.approx(nu)
    # EN 1992-2 §6.109 gives the same here: pure torsion has θ = θel = 45°, no reduction
    with pytest.warns(UserWarning):
        r109 = uls.eurocode2_shell_check(_inp(strut_model="6.109", **kw))
    assert r109.details["layers"]["bottom"]["strut"]["delta_theta"] == pytest.approx(0.0)
    assert r109.details["layers"]["bottom"]["nu"] == pytest.approx(nu)
    # σcd = 2|τ| = 2·60/(t·z) = 12.5 MPa > 0.528·20 = 10.6 MPa, but < fcd = 20 MPa
    assert 0.528 * 20.0 < r.details["layers"]["bottom"]["sigma_cd"] / 1e3 < 20.0
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        ok = uls.eurocode2_shell_check(_inp(**{**kw, "m_xy": 30.0}))
    assert not ok.crushing
    # compression with no reinforcement needed: fcd (F.1(3)); EN 1992-2 Eq. (6.110) as the option
    cmp_kw = {"n_xx": -600.0, "n_yy": -500.0, "n_xy": 20.0, "m_xx": 0.0, "m_yy": 0.0, "m_xy": 0.0}
    both = uls.eurocode2_shell_check(_inp(**cmp_kw))
    assert both.details["layers"]["bottom"]["nu"] == 1.0 and not both.crushing
    lay = uls.eurocode2_shell_check(_inp(strut_model="6.109", **cmp_kw)).details["layers"]["bottom"]
    assert lay["strut"]["case"] == "biaxial_compression"
    assert lay["nu"] == pytest.approx(0.85 * (1 + 3.8 * lay["strut"]["alpha"]) / (1 + lay["strut"]["alpha"]) ** 2)
    assert 0.85 <= lay["nu"] <= 1.1
    with pytest.raises(ValueError, match="strut_model"):
        uls.eurocode2_shell_check(_inp(strut_model="x"))
    assert both.asx_bot == both.asy_bot == 0.0


def test_input_errors_and_trace_and_partial_factors():
    with pytest.raises(ValueError, match="do not fit"):
        uls.eurocode2_shell_check(_inp(thickness=0.08))
    with pytest.raises(ValueError, match="do not fit"):
        uls.eurocode2_shell_check(_inp(cover=0.0))
    rep = CalcReport(title="shell")
    uls.eurocode2_shell_check(_inp(), trace=rep)
    symbols = {st.symbol for sec in rep.sections for st in sec.steps}
    assert {"t", "z", "layer bottom", "σ_cd (top)", "A_sx,bot"} <= symbols
    inp = uls.ShellInput.from_partial_factors(
        "2023", "accidental", n_xx=1.0, n_yy=1.0, n_xy=1.0, m_xx=1.0, m_yy=1.0, m_xy=1.0,
        fck=30.0, fyk=500.0, thickness=0.2, cover=0.04)
    assert (inp.gamma_c, inp.gamma_s) == (1.15, 1.0)
    assert "CRUSHING" not in str(uls.eurocode2_shell_check(_inp()))


def test_2023_has_the_same_areas_and_the_annex_g_nu():
    a04 = uls.eurocode2_shell_check(_inp())
    a23 = uls2023.eurocode2_shell_check(_inp(uls2023.ShellInput, alpha_cc=1.0))
    for k in ("asx_bot", "asy_bot", "asx_top", "asy_top"):
        assert getattr(a23, k) == pytest.approx(getattr(a04, k)), k
    assert a23.details["method"] == "sandwich"
    assert a23.details["layers"]["bottom"]["nu"] == 0.4
    assert a04.details["layers"]["bottom"]["nu"] == pytest.approx(0.528)
    assert a23.details["layers"]["bottom"]["nu"] == 0.4
    # the same strut: 2004 passes (ν = 0,528), 2023 fails (ν = 0,4) between 8 and 10,6 MPa
    kw = {"n_xx": 0.0, "n_yy": 0.0, "n_xy": 0.0, "m_xx": 0.0, "m_yy": 0.0, "m_xy": 45.0}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        c23 = uls2023.eurocode2_shell_check(_inp(uls2023.ShellInput, alpha_cc=1.0, **kw))
        c04 = uls.eurocode2_shell_check(_inp(**kw))
    assert c23.crushing and not c04.crushing
    assert uls2023.eurocode2_shell_check is not uls.eurocode2_shell_check
    assert uls2023.ShellResult is uls.ShellResult


def test_2023_options_nu_mode_eta_cc_and_annex():
    base = _inp(uls2023.ShellInput)
    assert uls2023.eurocode2_shell_check(base).details["f_cd"] == pytest.approx(30.0 / 1.5)
    hi = uls2023.eurocode2_shell_check(_inp(uls2023.ShellInput, fck=60.0))
    assert hi.details["f_cd"] == pytest.approx((40 / 60) ** (1 / 3) * 60 / 1.5)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        strain = uls2023.eurocode2_shell_check(_inp(
            uls2023.ShellInput, nu_mode="strain", m_xy=60.0, m_xx=0.0, m_yy=0.0,
            n_xx=0.0, n_yy=0.0, n_xy=0.0))
    assert strain.details["layers"]["bottom"]["nu"] > 0.4
    with pytest.raises(ValueError, match="Unknown national annex"):
        uls2023.eurocode2_shell_check(_inp(uls2023.ShellInput, annex="ZZ"))


# ── cracking check, EN 1992-2 Annex LL (102)-(107) ───────────────────────────

def test_ottosen_criterion_is_calibrated_at_uniaxial_failure():
    from eurocodepy.ec2.uls.shell import ottosen_phi
    fcm, fctm = 38.0, 0.3 * 30.0 ** (2 / 3)
    assert ottosen_phi(0.0, 0.0, -fcm, fcm, fctm) == pytest.approx(0.0, abs=0.02)     # compressive strength
    assert ottosen_phi(fctm, 0.0, 0.0, fcm, fctm) == pytest.approx(0.0, abs=0.02)     # tensile strength
    assert ottosen_phi(0.0, 0.0, 0.0, fcm, fctm) == pytest.approx(-1.0)
    assert ottosen_phi(0.0, -10.0, -10.0, fcm, fctm) < ottosen_phi(0.0, 0.0, -10.0, fcm, fctm) + 1.0
    # beyond the strengths: Φ > 0
    assert ottosen_phi(1.5 * fctm, 0.0, 0.0, fcm, fctm) > 0 and ottosen_phi(0.0, 0.0, -1.3 * fcm, fcm, fctm) > 0
    # hydrostatic compression: J2 = 0, only the I1 term
    assert ottosen_phi(-5.0, -5.0, -5.0, fcm, fctm) == pytest.approx(
        1.0 / (3.7 * (fctm / fcm) ** 1.1) * (-15.0) / fcm - 1.0)
    # symmetric in the order of the principal stresses
    assert ottosen_phi(1.0, -3.0, -8.0, fcm, fctm) == pytest.approx(ottosen_phi(-8.0, 1.0, -3.0, fcm, fctm))


def test_uncracked_elements_are_not_designed():
    from eurocodepy.ec2.uls.shell import shell_cracking
    # bending mx: σ = 6m/h² = 0.75 MPa for 5 kNm/m (h = 0,2), 3 MPa for 20 kNm/m (fctm = 2,9 MPa)
    low = uls.eurocode2_shell_check(_inp(n_xx=0.0, n_yy=0.0, n_xy=0.0, m_xx=5.0, m_yy=0.0, m_xy=0.0,
                                         check_cracking=True))
    assert low.details["cracked"] is False and low.details["cracking"]["phi_max"] < 0
    assert (low.asx_bot, low.asy_bot, low.asx_top, low.asy_top) == (0.0, 0.0, 0.0, 0.0)
    assert low.details["layers"] == {} and not low.crushing
    high = uls.eurocode2_shell_check(_inp(n_xx=0.0, n_yy=0.0, n_xy=0.0, m_xx=20.0, m_yy=0.0, m_xy=0.0,
                                          check_cracking=True))
    assert high.details["cracked"] is True and high.asx_bot > 0
    crk = shell_cracking((0.0, 0.0, 0.0), (20.0, 0.0, 0.0), 0.2, 30.0)
    assert crk["cracked"] and crk["z_crit"] == pytest.approx(0.1)      # the bottom face (sagging)
    hog = shell_cracking((0.0, 0.0, 0.0), (-20.0, 0.0, 0.0), 0.2, 30.0)
    assert hog["cracked"] and hog["z_crit"] == pytest.approx(-0.1)     # the top face (hogging)
    assert shell_cracking((0.0, 0.0, 0.0), (20.0, 0.0, 0.0), 0.2, 30.0, f_ctm=4.0)["cracked"] is False


def test_cracking_check_membrane_shear_and_default():
    from eurocodepy.ec2.uls.shell import shell_cracking
    assert shell_cracking((300.0, 0.0, 0.0), (0.0, 0.0, 0.0), 0.2, 30.0)["cracked"] is False   # 1,5 MPa
    assert shell_cracking((700.0, 0.0, 0.0), (0.0, 0.0, 0.0), 0.2, 30.0)["cracked"] is True    # 3,5 MPa
    # transverse shear raises Φ (principal tension of a shear state), 1,5·v/h at the mid-plane
    a = shell_cracking((300.0, 0.0, 0.0), (0.0, 0.0, 0.0), 0.2, 30.0)
    b = shell_cracking((300.0, 0.0, 0.0), (0.0, 0.0, 0.0), 0.2, 30.0, v=(60.0, 0.0))
    assert b["phi_max"] > a["phi_max"]
    # the composite checks cracking by default
    inp = uls.ShellInput(n_xx=0.0, n_yy=0.0, n_xy=0.0, m_xx=5.0, m_yy=0.0, m_xy=0.0,
                         fck=30.0, fyk=500.0, thickness=0.2, cover=0.04)
    assert inp.check_cracking is True
    assert uls.eurocode2_shell_check(inp).details["cracked"] is False
    # the minimum principal stress of an uncracked element must not exceed fcd (LL (103))
    with pytest.warns(UserWarning, match="uncracked shell element"):
        hi = uls.eurocode2_shell_check(uls.ShellInput(
            n_xx=-5000.0, n_yy=0.0, n_xy=0.0, m_xx=0.0, m_yy=0.0, m_xy=0.0, fck=30.0, fyk=500.0,
            thickness=0.2, cover=0.04))              # 25 MPa > fcd = 20 MPa, below fcm = 38 MPa
    assert hi.crushing and hi.details["cracked"] is False
    rep = CalcReport(title="c")
    uls.eurocode2_shell_check(_inp(m_xx=20.0, check_cracking=True), trace=rep)
    assert "Φ" in {st.symbol for sec in rep.sections for st in sec.steps}
