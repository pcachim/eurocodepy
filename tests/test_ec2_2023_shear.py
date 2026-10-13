"""EN 1992-1-1:2023 Clause 8.2 shear: ec2.uls2023.shear and ec2.uls2023.shear_check.

Hand values: b = 0,3 m, d = 0,5 m, fck = 30 MPa, rho_l = 1 %, D_lower = 20 mm
(ddg = 36 mm), gamma_v = 1,4, fyd = 500/1,15 MPa.
"""
import math

import pytest

from eurocodepy.calc_report import CalcReport
from eurocodepy.ec2 import uls, uls2023
from eurocodepy.ec2.uls2023 import shear as s

FYD = 500.0 / 1.15
TOL = 1e-9


def test_uls2023_shear_is_the_2023_module():
    assert uls2023.shear.__name__ == "eurocodepy.ec2.uls2023.shear"
    assert uls.shear.__name__ == "eurocodepy.ec2.uls.shear"
    assert uls2023.eurocode2_shear_check is not uls.eurocode2_shear_check
    # the 2004 shear functions are still reachable by their names
    assert uls2023.calc_vrd is uls.calc_vrd


def test_ddg_eq_8_2_1_4():
    assert s.calc_ddg(30.0, 20.0) == 36.0
    assert s.calc_ddg(30.0, 32.0) == 40.0                       # capped at 40 mm
    assert s.calc_ddg(90.0, 20.0) == pytest.approx(16.0 + 20.0 * (60.0 / 90.0) ** 2)


def test_taurdc_min_eq_8_20_and_taurdc_eq_8_27():
    t_min = 11.0 / 1.4 * math.sqrt(30.0 / FYD * 36.0 / 500.0)
    assert s.calc_taurdc_min(30.0, FYD, 0.5) == pytest.approx(t_min, abs=TOL)
    assert t_min == pytest.approx(0.5538, abs=1e-4)
    t = 0.66 / 1.4 * (100 * 0.01 * 30.0 * 36.0 / 500.0) ** (1 / 3)
    assert s.calc_taurdc(0.01, 30.0, 0.5, FYD) == pytest.approx(t, abs=TOL)
    assert t == pytest.approx(0.6094, abs=1e-4)
    # tiny rho_l: the minimum governs
    assert s.calc_taurdc(0.0005, 30.0, 0.5, FYD) == pytest.approx(t_min)


def test_shear_span_and_axial_force_eqs_8_29_to_8_31():
    assert s.calc_acs(100.0, 100.0, 0.5) == 1.0
    assert s.calc_acs(10.0, 100.0, 0.5) == 0.5                  # >= d
    assert s.calc_av(1.0, 0.5) == pytest.approx(math.sqrt(1.0 * 0.5 / 4.0))
    assert s.calc_av(2.0, 0.5) == pytest.approx(0.5)            # continuous at acs = 4d
    assert s.calc_av(3.0, 0.5) == 0.5
    # av < d raises the resistance
    assert (s.calc_taurdc(0.01, 30.0, 0.5, FYD, d_shear=s.calc_av(1.0, 0.5))
            > s.calc_taurdc(0.01, 30.0, 0.5, FYD))
    assert s.calc_kvp(0.0, 100.0, 0.5, 1.0) == 1.0
    assert s.calc_kvp(-300.0, 100.0, 0.5, 1.0) == pytest.approx(1.0 - 3.0 * 0.5 / 3.0)
    assert s.calc_kvp(-3000.0, 100.0, 0.5, 1.0) == 0.1          # floor
    assert s.calc_kvp(100.0, 100.0, 0.5, 1.0) > 1.0             # tension lowers tau


def test_taurdc_axial_eqs_8_32_to_8_35():
    r = s.calc_taurdc_axial(0.01, 30.0, 0.5, FYD, n_ed=-600.0, a_c=0.3 * 0.55,
                            b_w=0.3, e_p=0.0, a_cs0=1.0)
    z = 0.45
    k1 = 0.5 / 1.0 * (0.0 + 0.5 / 3.0) * (0.165 / (0.3 * z))
    assert r["k1"] == pytest.approx(min(k1, 0.18 * 0.165 / (0.3 * z)))
    assert r["sigma_cp"] == pytest.approx(-600.0 / 0.165 / 1000.0)
    t0 = 0.66 / 1.4 * (100 * 0.01 * 30.0 * 36.0 / 500.0) ** (1 / 3)
    assert r["tau_rdc0"] == pytest.approx(t0)
    assert r["tau_rdc_max"] == pytest.approx(min(2.15 * t0 * 2.0 ** (1 / 6), 2.7 * t0))
    assert r["tau_rdc"] > t0                                    # compression helps
    assert r["tau_rdc"] <= r["tau_rdc_max"]
    tens = s.calc_taurdc_axial(0.01, 30.0, 0.5, FYD, n_ed=600.0, a_c=0.165,
                               b_w=0.3, e_p=0.0, a_cs0=1.0)
    assert tens["tau_rdc"] < t0
    assert tens["tau_rdc"] >= tens["tau_rdc_min"]


def test_prestressed_depth_eqs_8_36_8_37():
    d = s.calc_d_prestressed(0.5, 0.001, 0.4, 0.0005)
    assert d == pytest.approx((0.25 * 0.001 + 0.16 * 0.0005) / (0.5 * 0.001 + 0.4 * 0.0005))
    assert s.calc_rho_l_prestressed(0.5, 0.001, 0.4, 0.0005, 0.3, d) == pytest.approx(
        (0.5 * 0.001 + 0.4 * 0.0005) / (0.3 * d**2))


def test_planar_members_eqs_8_21_to_8_26_and_8_38_to_8_40():
    assert s.planar_shear_force(30.0, 40.0) == 50.0
    assert s.planar_effective_depth(100.0, 40.0, 0.2, 0.18) == 0.2          # <= 0,5
    assert s.planar_effective_depth(100.0, 100.0, 0.2, 0.18) == pytest.approx(0.19)
    assert s.planar_effective_depth(100.0, 250.0, 0.2, 0.18) == 0.18        # >= 2
    assert s.planar_effective_depth(0.0, 50.0, 0.2, 0.18) == 0.18           # vx = 0
    a = math.atan2(100.0, 100.0)
    assert s.planar_effective_depth(100.0, 100.0, 0.2, 0.18, smooth=True) == pytest.approx(
        0.2 * math.cos(a) ** 2 + 0.18 * math.sin(a) ** 2)
    assert s.planar_rho_l(100.0, 40.0, 0.01, 0.02) == 0.01
    assert s.planar_rho_l(100.0, 250.0, 0.01, 0.02) == 0.02
    assert s.planar_rho_l(100.0, 100.0, 0.01, 0.02) == pytest.approx(
        0.01 * 0.5**2 + 0.02 * 0.5**2)


def test_cot_theta_min_eq_8_41():
    assert s.calc_cot_theta_min() == 2.5
    assert s.calc_cot_theta_min(significant_compression=True) == 3.0
    assert s.calc_cot_theta_min(n_ed=50.0, v_ed=100.0) == pytest.approx(2.45)
    assert s.calc_cot_theta_min(n_ed=1e6, v_ed=100.0) == 1.0
    assert s.calc_cot_theta_min(ductility="A") == pytest.approx(2.0)


def test_compression_field_eqs_8_42_8_44_and_note():
    fcd, nu = 20.0, 0.5
    rho_w = 0.002
    assert s.calc_tau_rd_sy(rho_w, FYD, 2.0) == pytest.approx(rho_w * FYD * 2.0)
    assert s.calc_sigma_cd(1.2, 2.0) == pytest.approx(1.2 * (2.0 + 0.5))
    assert s.calc_tau_rd(rho_w, FYD, nu, fcd, 2.0) == pytest.approx(
        min(rho_w * FYD * 2.0, nu * fcd / (2.0 + 0.5)))
    # simultaneous yielding and crushing
    c = s.calc_cot_theta_opt(rho_w, FYD, nu, fcd, 2.5)
    assert c == pytest.approx(min(math.sqrt(nu * fcd / (rho_w * FYD) - 1), 2.5))
    # crushing limit: sigma_cd = nu*fcd
    cc = s.calc_cot_theta_crush(1.5, nu, fcd)
    assert s.calc_sigma_cd(1.5, cc) == pytest.approx(nu * fcd)
    assert s.calc_cot_theta_crush(5.1, nu, fcd) is None       # 2·tau > nu·fcd
    assert s.calc_cot_theta_crush(0.0, nu, fcd) == math.inf


def test_asw_and_vrd_forms_agree():
    z, cot = 0.45, 2.0
    asw = s.calc_asw_s(200.0, z, FYD, cot)
    assert asw == pytest.approx(200.0 / (z * FYD * cot) / 1000.0)
    assert s.calc_vrd_s(asw, z, FYD, cot) == pytest.approx(200.0)
    assert s.calc_vrd_max(0.3, z, 0.5, 20.0, cot) == pytest.approx(
        0.5 * 20.0 * 0.3 * z / (cot + 1 / cot) * 1000.0)


def test_inclined_reinforcement_eqs_8_58_to_8_62():
    a = 60.0
    ca = 1.0 / math.tan(math.radians(a))
    cot = 1.5
    assert s.calc_tau_rd_sy(0.002, FYD, cot, a) == pytest.approx(
        0.002 * FYD * (cot + ca) * math.sin(math.radians(a)))
    assert s.calc_sigma_cd(1.0, cot, a) == pytest.approx(
        1.0 * (1 + cot**2) / (cot + ca))
    assert s.calc_n_vd(100.0, cot, a) == pytest.approx(100.0 * (cot - ca))
    cc = s.calc_cot_theta_crush(2.0, 0.5, 20.0, a)
    assert s.calc_sigma_cd(2.0, cc, a) == pytest.approx(10.0, rel=1e-6)
    with pytest.raises(ValueError, match="alpha_w"):
        s.calc_asw_s(100.0, 0.45, FYD, 2.0, alpha_w=30.0)
    # alpha = 90 degrees recovers the vertical formulae
    assert s.calc_tau_rd_sy(0.002, FYD, cot, 90.0) == pytest.approx(0.002 * FYD * cot)


def test_chord_forces_and_strain_eqs_8_45_to_8_52():
    r = s.calc_chord_forces(m_ed=200.0, v_ed=150.0, n_ed=0.0, z=0.45, cot=2.0)
    assert r["n_vd"] == 300.0
    assert r["f_td"] == pytest.approx(200.0 / 0.45 + 150.0)
    assert r["f_cd"] == pytest.approx(200.0 / 0.45 - 150.0)
    eps = s.calc_eps_x(r["f_td"], 0.0015, 200000.0, r["f_cd"], a_cc=0.05, e_c=33000.0)
    xt = r["f_td"] / (0.0015 * 200000.0 * 1000.0)
    xc = -r["f_cd"] / (0.05 * 33000.0 * 1000.0)
    assert eps == pytest.approx(max(0.5 * (xt + xc), 0.0))
    with pytest.raises(ValueError, match="a_cc"):
        s.calc_eps_x(100.0, 0.001, 200000.0, 50.0)
    assert s.calc_nu(0.0, 1.0) == pytest.approx(1.0 / (1.0 + 110.0 * 0.001))
    assert s.calc_nu(0.0, 2.5) == pytest.approx(1.0 / (1.0 + 110.0 * 0.001 * 6.25))
    assert s.calc_nu(-0.0005, 0.5) <= 1.0
    # sigma_swd for cot < 1 is limited to fywd; 90 degrees reduces to Eq. (8.56)
    sw = s.calc_sigma_swd(0.002, 0.8, 200000.0, FYD)
    assert sw == pytest.approx(min(200000.0 * (0.8**2 * 0.003 - 0.001), FYD))


def test_concentrated_loads_near_support_eqs_8_55_8_57():
    t = s.calc_tau_rd_near_support(0.5, 20.0, 0.002 * FYD, 2.0, 1.0)
    expect = 0.5 * 20.0 * (2.0 - 1.0) / 5.0 + 0.002 * FYD * 1.0
    assert t == pytest.approx(min(expect, 0.5 * 20.0 * 2.0 / 5.0))
    assert s.calc_delta_m_ed(1.0, 0.5, 2.0, 0.45, 0.3, 1.0, 0.2) == pytest.approx(
        (1.0 - 0.5 * 2.0) * 0.45 * 0.3 * (0.5 - 0.2) * 1000.0)


def test_duct_width_eq_8_54():
    assert s.calc_bw_nom(0.3, 0.03) == 0.3                      # sum phi <= bw/8
    assert s.calc_bw_nom(0.3, 0.06, "grouted_steel") == pytest.approx(0.27)
    assert s.calc_bw_nom(0.3, 0.06, "grouted_plastic") == pytest.approx(0.252)
    assert s.calc_bw_nom(0.3, 0.06, "other") == pytest.approx(0.228)
    with pytest.raises(ValueError, match="duct"):
        s.calc_bw_nom(0.3, 0.06, "none")


def test_transverse_bending_and_flange_eqs_8_64_to_8_72():
    assert s.calc_taurdm(2.0, 50.0, 100.0) == pytest.approx(2.0 * math.sqrt(0.5))
    assert s.transverse_bending_negligible(0.3, 2.0, 50.0, 100.0)      # tau/tau_rd < 0,2
    assert not s.transverse_bending_negligible(1.0, 2.0, 50.0, 100.0)
    assert s.calc_tau_ed_flange(60.0, 0.15, 2.0) == pytest.approx(0.2)
    assert s.flange_cot_theta_range(compression_flange=True) == (1.0, 3.0)
    assert s.flange_cot_theta_range(compression_flange=False) == (1.0, 1.25)
    assert s.calc_asf_sf(0.2, 0.15, FYD, 2.0) == pytest.approx(0.2 * 0.15 / (FYD * 2.0))
    assert s.flange_crushing_ok(0.2, 2.0, 20.0)
    assert not s.flange_crushing_ok(5.0, 2.0, 20.0)
    assert s.flange_check_omitted(0.1, 1e-4, 0.2, 0.15, FYD)


def test_interface_table_8_2_and_eqs_8_74_to_8_78():
    assert s.interface_coefficients("rough") == {
        "c_v1": 0.15, "mu_v": 0.7, "c_v2": 0.08, "k_v": 0.5, "k_dowel": 0.9}
    assert s.interface_coefficients("keyed")["c_v1"] == 0.37
    with pytest.raises(ValueError, match="roughness"):
        s.interface_coefficients("polished")
    fcd = 20.0
    # no reinforcement: cv1·sqrt(fck)/gamma_c + mu·sigma_n
    t = s.calc_tau_rdi(30.0, 1.5, fcd, "rough", sigma_n=1.0)
    assert t == pytest.approx(0.15 * math.sqrt(30.0) / 1.5 + 0.7)
    # tension kills the cohesion and friction
    assert s.calc_tau_rdi(30.0, 1.5, fcd, "rough", sigma_n=-0.5) == 0.0
    # sigma_n limited to 0,6 fcd; total limited to 0,30 fcd
    big = s.calc_tau_rdi(30.0, 1.5, fcd, "very_rough", sigma_n=50.0)
    assert big == pytest.approx(0.30 * fcd)
    # with reinforcement (8.76), alpha = 90: rho·fyd·mu
    t = s.calc_tau_rdi(30.0, 1.5, fcd, "rough", rho_i=0.005, f_yd=FYD, alpha=90.0)
    assert t == pytest.approx(0.15 * math.sqrt(30.0) / 1.5 + 0.005 * FYD * 0.7)
    # not anchored (8.77), topping raises cv2 by 1,2; capped at 0,25 fcd
    t = s.calc_tau_rdi(30.0, 1.5, fcd, "rough", rho_i=0.005, f_yd=FYD,
                       anchored=False, topping=True)
    expect = (0.08 * 1.2 * math.sqrt(30.0) / 1.5 + 0.5 * 0.005 * FYD * 0.7
              + 0.9 * 0.005 * math.sqrt(FYD * fcd))
    assert t == pytest.approx(min(expect, 0.25 * fcd))
    assert s.calc_tau_rdi(30.0, 1.5, fcd, "rough", rho_i=0.005, f_yd=FYD,
                          anchored=False, dowel=False) < t
    with pytest.raises(ValueError, match="keyed"):
        s.calc_tau_rdi(30.0, 1.5, fcd, "keyed", anchored=False)
    with pytest.raises(ValueError, match="alpha"):
        s.calc_tau_rdi(30.0, 1.5, fcd, "smooth", alpha=120.0)
    assert s.calc_tau_edi(150.0, 0.3) == pytest.approx(0.5)
    assert s.calc_tau_edi_composite(0.4, 150.0, 0.45, 0.3) == pytest.approx(
        0.4 * 150.0 / (0.45 * 0.3) / 1000.0)
    assert s.calc_as_min_interface(0.05, 2.9, 500.0) == pytest.approx(0.05 * 2.9 / 500.0)


# ── check procedure ─────────────────────────────────────────────────────────

def _inp(**kw):
    base = {"b": 0.3, "d": 0.5, "fck": 30.0, "fyk": 500.0, "as_long": 0.0015}
    base.update(kw)
    return uls2023.ShearInput(**base)


def test_check_stirrups_mode():
    r = uls2023.eurocode2_shear_check(_inp(), 150.0)
    assert r.mode == "stirrups"
    assert not r.crushing
    assert r.cot == 2.5                                         # flattest allowed
    assert r.vrd_c == pytest.approx(0.6094 * 0.3 * 0.45 * 1000.0, rel=1e-3)
    assert r.asw_s == pytest.approx(150.0 / (0.45 * FYD * 2.5) / 1000.0)
    assert r.vrd_max == pytest.approx(0.5 * 20.0 * 0.3 * 0.45 * 2.5 / 7.25 * 1000.0)
    assert r.details["tau_ed"] == pytest.approx(150.0 / (0.3 * 0.45) / 1000.0)
    assert "stirrups" in str(r)


def test_check_no_verification_and_no_shear_reinforcement():
    low = uls2023.eurocode2_shear_check(_inp(asw_min_s=1e-4), 30.0)
    assert low.mode == "no_verification"                        # tau_Ed <= tau_Rdc,min
    assert low.asw_s == 1e-4
    mid = uls2023.eurocode2_shear_check(_inp(asw_min_s=1e-4), 78.0)
    assert mid.mode == "no_shear_reinf"                         # tau_min < tau_Ed <= tau_Rd,c
    assert mid.asw_s == 1e-4


def test_check_cot_theta_decreases_when_the_strut_governs():
    r = uls2023.eurocode2_shear_check(_inp(), 520.0)
    assert r.mode == "stirrups"
    assert 1.0 < r.cot < 2.5
    assert r.vrd_max == pytest.approx(520.0)                    # strut exactly used
    assert r.asw_s == pytest.approx(520.0 / (0.45 * FYD * r.cot) / 1000.0)


def test_check_strut_crushing():
    r = uls2023.eurocode2_shear_check(_inp(), 700.0)
    assert r.crushing
    assert r.mode == "strut_crushing"
    assert r.cot == 1.0


def test_check_axial_force_and_cot_limit():
    comp = uls2023.eurocode2_shear_check(_inp(m_ed=100.0, n_ed=-400.0), 100.0)
    base = uls2023.eurocode2_shear_check(_inp(m_ed=100.0), 100.0)
    assert comp.vrd_c > base.vrd_c
    ten = uls2023.eurocode2_shear_check(_inp(m_ed=100.0, n_ed=100.0), 150.0)
    assert ten.cot == pytest.approx(2.5 - 0.1 * 100.0 / 150.0)
    with pytest.raises(ValueError, match="m_ed"):
        uls2023.eurocode2_shear_check(_inp(n_ed=100.0), 150.0)
    assert uls2023.eurocode2_shear_check(
        _inp(significant_compression=True), 150.0).cot == 3.0


def test_check_shear_span_raises_resistance():
    short = uls2023.eurocode2_shear_check(_inp(m_ed=75.0), 150.0)     # acs = d -> av = d/2
    assert short.details["d_shear"] == pytest.approx(0.25)
    assert short.vrd_c > uls2023.eurocode2_shear_check(_inp(), 150.0).vrd_c


def test_check_fcd_follows_eta_cc_and_k_tc():
    hi = uls2023.eurocode2_shear_check(_inp(fck=60.0), 150.0)
    assert hi.details["f_cd"] == pytest.approx((40.0 / 60.0) ** (1 / 3) * 60.0 / 1.5)
    other = uls2023.eurocode2_shear_check(_inp(k_tc=0.85), 150.0)
    assert other.details["f_cd"] == pytest.approx(0.85 * 30.0 / 1.5)
    given = uls2023.eurocode2_shear_check(_inp(alpha_cc=1.0), 150.0)
    assert given.details["f_cd"] == pytest.approx(20.0)


def test_check_from_partial_factors_and_trace():
    inp = uls2023.ShearInput.from_partial_factors(
        "2023", "accidental", b=0.3, d=0.5, fck=30.0, fyk=500.0, as_long=0.0015)
    assert (inp.gamma_v, inp.gamma_c, inp.gamma_s) == (1.15, 1.15, 1.0)
    rep = CalcReport(title="shear 2023")
    r = uls2023.eurocode2_shear_check(inp, 150.0, trace=rep)
    assert r.mode == "stirrups"
    symbols = [st.symbol for sec in rep.sections for st in sec.steps]
    assert {"τ_Ed", "τ_Rd,c", "cot θ", "A_sw/s"} <= set(symbols)
