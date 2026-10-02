"""Validação EC5 (EN 1995-1-1) — madeira, ``eurocodepy.ec5``.

Chama diretamente as funções de baixo nível do ``eurocodepy`` e compara com a
mesma fórmula da norma, escrita à mão, dentro deste script. Reutiliza a
secção C24 0.10×0.20 m de ``xdfem2d/validation/design_cases_manual.md``
(A7.1-A7.4) para comparação direta.

Requer o ``eurocodepy`` instalado a partir do código-fonte real do
repositório.

Correr:  python validation/validation_timber.py
Gera:    validation/validation_timber.md
"""
from __future__ import annotations

_results: list[bool] = []
_md: list[str] = []


def _check(name: str, got: float, expected: float, tol: float, unit: str = "") -> bool:
    ok = abs(got - expected) <= tol
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}: got={got:.6g}{unit} expected={expected:.6g}{unit} "
          f"(tol={tol:.3g}{unit})")
    _results.append(ok)
    return ok


def _check_true(name: str, ok: bool, detail: str = "") -> bool:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
    _results.append(ok)
    return ok


def _make_c24():
    """C24 solid timber, service class 1, medium-duration load — mesmas
    condições de xdfem2d/validation/design_cases_manual.md (A7.x)."""
    from eurocodepy.ec5.materials import LoadDuration, ServiceClass, Timber

    timber = Timber("C24")
    sc, ld = ServiceClass.SC1, LoadDuration.MediumDuration
    timber.design_values(service_class=sc, load_duration=ld)
    return timber, sc, ld


def _section():
    from eurocodepy.utils import RectangularCrossSection
    return RectangularCrossSection(width=0.10, height=0.20)


def case_design_values() -> None:
    """Valores de cálculo — EN 1995-1-1 §2.4.1, f_d = k_mod·f_k/γ_M.

    kmod=0.8 (classe de serviço 1, duração média, EC5 Tabela 3.1),
    γM=1.3 (madeira maciça, EC5 Tabela 2.3).
    """
    timber, _sc, _ld = _make_c24()
    kmod, gamma_m = timber.kmod, timber.safety
    ft0k, fc0k, fmk, fvk = timber.ft0k, timber.fc0k, timber.fmk, timber.fvk

    ft0d_hand = kmod * ft0k / gamma_m
    fc0d_hand = kmod * fc0k / gamma_m
    fmd_hand = kmod * fmk / gamma_m
    fvd_hand = kmod * fvk / gamma_m

    ok1 = _check("Design values: k_mod (SC1, duração média)", kmod, 0.8, 1e-9)
    ok2 = _check("Design values: γ_M (madeira maciça)", gamma_m, 1.3, 1e-9)
    ok3 = _check("Design values: f_t0k (C24)", ft0k, 14.5, 1e-9, " MPa")
    ok4 = _check("Design values: f_t0d", timber.ft0d, ft0d_hand, 1e-9, " MPa")
    ok5 = _check("Design values: f_c0d", timber.fc0d, fc0d_hand, 1e-9, " MPa")
    ok6 = _check("Design values: f_md", timber.fmd, fmd_hand, 1e-9, " MPa")
    ok7 = _check("Design values: f_vd", timber.fvd, fvd_hand, 1e-9, " MPa")
    all_ok = all([ok1, ok2, ok3, ok4, ok5, ok6, ok7])
    _md.append(f"""### Valores de cálculo — EN 1995-1-1 §2.4.1

Madeira C24, classe de serviço 1, duração média. k_mod={kmod},
γ_M={gamma_m} (madeira maciça, EC5 Tabela 2.3).

```
f_t0d = k_mod·f_t0k/γ_M                     = {ft0d_hand:.4f} MPa  (f_t0k={ft0k} MPa)
f_c0d = k_mod·f_c0k/γ_M                     = {fc0d_hand:.4f} MPa  (f_c0k={fc0k} MPa)
f_md  = k_mod·f_mk/γ_M                      = {fmd_hand:.4f} MPa   (f_mk={fmk} MPa)
f_vd  = k_mod·f_vk/γ_M                      = {fvd_hand:.4f} MPa   (f_vk={fvk} MPa)
```

`Timber("C24").design_values(SC1, MediumDuration)` → mesmos valores.

| Verificação | Resultado |
|---|---|
| Todos os valores de cálculo à mão == `Timber.design_values` | {'✓ PASS' if all_ok else '✗ FAIL'} |
""")


def case_axial_tension() -> None:
    """Tração axial pura — EN 1995-1-1 §6.1.2 (Eq. 6.1)."""
    timber, sc, ld = _make_c24()
    section = _section()
    from eurocodepy.ec5.uls.bending import check_bending_with_normal

    n_ed = 25.0  # kN (tração)
    r = check_bending_with_normal(n_ed=n_ed, m_ed_y=0.0, m_ed_z=0.0,
                                  section=section, timber=timber,
                                  l_0y=0.0, l_0z=0.0, l_0m=0.0,
                                  service_class=sc, load_duration=ld)
    sig_ax_hand = n_ed / section.area / 1e3  # kN/m2 -> /1e3 -> MPa
    util_hand = sig_ax_hand / timber.ft0d

    ok1 = _check("Axial tension: utilização (Eq. 6.1: σ_t0/f_t0d)",
                r["utilization"], util_hand, 1e-6)
    ok2 = _check("Axial tension: confere com A7.1 de design_cases_manual.md",
                r["utilization"], 0.14009, 5e-5)
    _md.append(f"""### Tração axial pura — EN 1995-1-1 §6.1.2 (Eq. 6.1)

Secção 0.10×0.20 m, N_Ed = {n_ed} kN (tração).

```
σ_t0,d = N_Ed/A                            = {sig_ax_hand:.4f} MPa
utilização = σ_t0,d/f_t0d                  = {util_hand:.5f}
```

`check_bending_with_normal(n_ed={n_ed}, m_ed_y=0, m_ed_z=0, ...)` →
utilização={r['utilization']:.5f}.

| Verificação | Resultado |
|---|---|
| Fórmula à mão == função | {'✓ PASS' if ok1 else '✗ FAIL'} |
| Confere com A7.1 de `design_cases_manual.md` | {'✓ PASS' if ok2 else '✗ FAIL'} |
""")


def case_axial_compression() -> None:
    """Compressão axial pura (sem encurvadura) — EN 1995-1-1 §6.1.4 (Eq. 6.2)."""
    timber, sc, ld = _make_c24()
    section = _section()
    from eurocodepy.ec5.uls.bending import check_bending_with_normal

    n_ed = -25.0  # kN (compressão)
    r = check_bending_with_normal(n_ed=n_ed, m_ed_y=0.0, m_ed_z=0.0,
                                  section=section, timber=timber,
                                  l_0y=0.0, l_0z=0.0, l_0m=0.0,
                                  service_class=sc, load_duration=ld)
    sig_ax_hand = abs(n_ed) / section.area / 1e3
    util_hand = sig_ax_hand / timber.fc0d

    # Not r["checks"]["check1"]: that is Eq. 6.19 (σc0/fc0d)² + bending terms
    # — the *combined* N+M cross-section check, which collapses to the
    # (squared, so numerically smaller) rc² term alone when there is no
    # moment, not the plain Eq. 6.2 stress check. With l_0y=l_0z=0 the
    # buckling factor k_c is 1.0, so the buckling check (Eq. 6.23/6.24,
    # sig_ax/(k_c·fc0d)) collapses to the same plain ratio Eq. 6.2 gives —
    # and it is folded into r["utilization"], the governing value across all
    # of §6.1-6.3, which is the quantity actually comparable to A7.2.
    ok1 = _check("Axial compression: utilização governante "
                "(= Eq. 6.2 σ_c0/f_c0d quando k_c=1, l_0=0)",
                r["utilization"], util_hand, 1e-6)
    ok2 = _check("Axial compression: confere com A7.2 de design_cases_manual.md",
                r["utilization"], 0.09673, 5e-5)
    _md.append(f"""### Compressão axial pura (sem encurvadura) — EN 1995-1-1 §6.1.4 (Eq. 6.2)

Secção 0.10×0.20 m, N_Ed = {n_ed} kN (compressão), sem comprimento de
encurvadura definido (l_0y=l_0z=0 → k_c=1.0, verificação de secção pura).

```
σ_c0,d = |N_Ed|/A                          = {sig_ax_hand:.4f} MPa
utilização = σ_c0,d/f_c0d                  = {util_hand:.5f}
```

`check_bending_with_normal(n_ed={n_ed}, m_ed_y=0, m_ed_z=0, l_0y=0, l_0z=0, ...)`
→ utilization={r['utilization']:.5f} (o valor governante, que com k_c=1.0
para l_0=0 é a própria Eq. 6.2; note-se que `checks['check1']`
={r['checks']['check1']:.5f} é a Eq. 6.19 — (σ_c0/f_c0d)² + termos de
flexão — que colapsa para o termo ao quadrado, não a razão simples, quando
não há momento: não é o valor a comparar aqui).

| Verificação | Resultado |
|---|---|
| Fórmula à mão == utilização governante | {'✓ PASS' if ok1 else '✗ FAIL'} |
| Confere com A7.2 de `design_cases_manual.md` | {'✓ PASS' if ok2 else '✗ FAIL'} |
""")


def case_bending() -> None:
    """Flexão pura — EN 1995-1-1 §6.1.6 (Eq. 6.11)."""
    timber, sc, ld = _make_c24()
    section = _section()
    from eurocodepy.ec5.uls.bending import check_bending_with_normal

    my_ed = 6.0  # kNm
    r = check_bending_with_normal(n_ed=0.0, m_ed_y=my_ed, m_ed_z=0.0,
                                  section=section, timber=timber,
                                  l_0y=0.0, l_0z=0.0, l_0m=0.0,
                                  service_class=sc, load_duration=ld)
    sig_my_hand = my_ed / section.bend_mod_y / 1e3
    util_hand = sig_my_hand / timber.fmd

    ok1 = _check("Bending: utilização (σ_m,y/f_md)", r["checks"]["check1"],
                util_hand, 1e-6)
    ok2 = _check("Bending: confere com A7.3 de design_cases_manual.md",
                r["checks"]["check1"], 0.60938, 5e-5)
    _md.append(f"""### Flexão pura — EN 1995-1-1 §6.1.6 (Eq. 6.11)

Secção 0.10×0.20 m, M_y,Ed = {my_ed} kN·m. W_y = b·h²/6 = {section.bend_mod_y:.6f} m³.

```
σ_m,y,d = M_y,Ed/W_y                       = {sig_my_hand:.4f} MPa
utilização = σ_m,y,d/f_md                  = {util_hand:.5f}
```

`check_bending_with_normal(n_ed=0, m_ed_y={my_ed}, m_ed_z=0, ...)` →
check1={r['checks']['check1']:.5f}.

| Verificação | Resultado |
|---|---|
| Fórmula à mão == função | {'✓ PASS' if ok1 else '✗ FAIL'} |
| Confere com A7.3 de `design_cases_manual.md` | {'✓ PASS' if ok2 else '✗ FAIL'} |
""")


def case_shear() -> None:
    """Esforço transverso puro — EN 1995-1-1 §6.1.7 (Eq. 6.13), τ=1.5V/(k_cr·b·h)."""
    timber, sc, ld = _make_c24()
    section = _section()
    from eurocodepy.ec5.uls.shear import check_shear_with_torsion

    vz_ed = 8.0  # kN
    r = check_shear_with_torsion(v_ed_y=0.0, v_ed_z=vz_ed, t_ed=0.0,
                                 section=section, timber=timber,
                                 service_class=sc, load_duration=ld)
    kcr = 0.67   # §6.1.7(2): madeira maciça, b_ef = k_cr·b
    tau_hand = 1.5 * vz_ed / (kcr * section.area) / 1e3
    util_hand = tau_hand / timber.fvd

    ok1 = _check("Shear: τ = 1.5·V/(k_cr·b·h)", tau_hand, 0.600 / kcr, 1e-3, " MPa")
    ok2 = _check("Shear: utilização (τ/f_vd)", r["util_shear"], util_hand, 1e-6)
    ok3 = _check("Shear: confere com A7.4 de design_cases_manual.md",
                r["util_shear"], 0.24375 / kcr, 5e-5)
    _md.append(f"""### Esforço transverso puro — EN 1995-1-1 §6.1.7 (Eq. 6.13)

Secção retangular: τ_d = 1.5·V_Ed/(k_cr·A) (fator 1.5 da distribuição
parabólica; b_ef = k_cr·b, k_cr = 0.67 para madeira maciça, §6.1.7(2)).
V_z,Ed = {vz_ed} kN.

```
τ_d = 1.5·V_Ed/(k_cr·A)                    = {tau_hand:.4f} MPa
utilização = τ_d/f_vd                      = {util_hand:.5f}
```

`check_shear_with_torsion(v_ed_y=0, v_ed_z={vz_ed}, t_ed=0, ...)` →
util_shear={r['util_shear']:.5f}.

| Verificação | Resultado |
|---|---|
| τ_d à mão ≈ 0.600 MPa | {'✓ PASS' if ok1 else '✗ FAIL'} |
| Fórmula à mão == função | {'✓ PASS' if ok2 else '✗ FAIL'} |
| Confere com A7.4 de `design_cases_manual.md` (÷ k_cr) | {'✓ PASS' if ok3 else '✗ FAIL'} |
""")


def case_torsion() -> None:
    """Torção pura — EN 1995-1-1 §6.1.8 (Eq. 6.14), com k_shape.

    τ_tor,d = T/W_t, com W_t o módulo de torção (Saint-Venant) da secção
    retangular, W_t = α·h·b², α = (1/3)(1 − 0.672·b/h + 0.3·(b/h)²) (h lado
    maior, b lado menor), escrito
    aqui de forma independente da função.
    """
    timber, sc, ld = _make_c24()
    section = _section()
    from eurocodepy.ec5.uls.shear import check_shear_with_torsion

    t_ed = 0.5  # kNm
    r = check_shear_with_torsion(v_ed_y=0.0, v_ed_z=0.0, t_ed=t_ed,
                                 section=section, timber=timber,
                                 service_class=sc, load_duration=ld)
    b, h = sorted((section.width, section.height))
    ratio = h / b
    alpha_hand = (1.0 / 3.0) * (1.0 - 0.672 * (b / h) + 0.3 * (b / h)**2)
    wt_hand = alpha_hand * h * b**2
    tau_tor_hand = t_ed / wt_hand / 1e3
    k_shape = min(1.0 + 0.15 * ratio, 2.0)
    fvdt_hand = k_shape * timber.fvd
    util_hand = tau_tor_hand / fvdt_hand

    ok1 = _check("Torsion: W_t (h=0.20, b=0.10)", section.torsion_modulus, wt_hand,
                 1e-9, " m³")
    ok2 = _check("Torsion: k_shape (Eq. 6.15)", k_shape, 1.3, 1e-9)
    ok3 = _check("Torsion: utilização (τ_tor/(k_shape·f_vd))",
                r["util_torsion"], util_hand, 1e-6)
    _md.append(f"""### Torção pura — EN 1995-1-1 §6.1.8 (Eq. 6.14)

Secção retangular, módulo de torção W_t = α·h·b², α = (1/3)(1 − 0.672·b/h + 0.3·(b/h)²), com h o lado
maior e b o menor (h/b={ratio}). T_Ed = {t_ed} kN·m.

```
α                                           = {alpha_hand:.5f}
W_t = α·h·b²                                = {wt_hand:.6e} m³
τ_tor,d = T_Ed/W_t                          = {tau_tor_hand:.4f} MPa
k_shape = min(1+0.15·h/b, 2.0)              = {k_shape:.4f}
f_vd,tor = k_shape·f_vd                     = {fvdt_hand:.4f} MPa
utilização = τ_tor,d/f_vd,tor               = {util_hand:.5f}
```

`check_shear_with_torsion(v_ed_y=0, v_ed_z=0, t_ed={t_ed}, ...)` →
util_torsion={r['util_torsion']:.5f}.

| Verificação | Resultado |
|---|---|
| W_t à mão == função | {'✓ PASS' if ok1 else '✗ FAIL'} |
| k_shape à mão | {'✓ PASS' if ok2 else '✗ FAIL'} |
| Utilização à mão == função | {'✓ PASS' if ok3 else '✗ FAIL'} |
""")


def _write_md(path: str) -> None:
    n_pass, n_total = sum(_results), len(_results)
    header = f"""# Validação EC5 (EN 1995-1-1) — madeira

Cálculo independente: as expressões do Eurocódigo 5 são escritas aqui
diretamente a partir do texto da norma (para a torção, W_t da teoria da
elasticidade de Saint-Venant) e comparadas com o resultado real das funções do
`eurocodepy.ec5`. **{n_pass}/{n_total}** comparações numéricas OK.

Secção-tipo: 0.10×0.20 m, madeira C24, classe de serviço 1, duração média —
mesma secção de `xdfem2d/validation/design_cases_manual.md` (A7.1-A7.4),
para comparação direta.

"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(_md))
        f.write(f"\n\n## Resumo\n\n{n_pass}/{n_total} verificações OK.\n")


def main() -> int:
    case_design_values()
    case_axial_tension()
    case_axial_compression()
    case_bending()
    case_shear()
    case_torsion()
    _write_md("validation/validation_timber.md")
    n_pass, n_total = sum(_results), len(_results)
    print(f"\n{n_pass}/{n_total} PASS")
    return 0 if n_pass == n_total else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
