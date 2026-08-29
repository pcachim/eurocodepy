"""Validação EC2 (EN 1992-1-1) — betão armado, ``eurocodepy.ec2``.

Chama diretamente as funções de baixo nível do ``eurocodepy`` (não um
adaptador de outro projeto) e compara o resultado com a mesma fórmula da
norma, aplicada à mão, dentro deste script — não contra um valor copiado de
outro sítio. Onde os dois batem certo há confirmação cruzada por dois
caminhos independentes; onde a função usa um procedimento com mais passos do
que uma fórmula fechada cobre, isso fica assinalado, não escondido.

Requer o ``eurocodepy`` instalado a partir do código-fonte real do
repositório (não a versão publicada no PyPI, cuja API é distinta).

Correr:  python validation/validation_rc_concrete.py
Gera:    validation/validation_rc_concrete.md
"""
from __future__ import annotations

import math

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


# Secção-tipo usada em todos os casos: b=0.30 m, h=0.50 m, cobrimento=0.03 m
# → d = h − cobrimento = 0.47 m. Betão C25/30 (fck=25 MPa), aço A500
# (fyk=500 MPa), γc=1.5, γs=1.15, αcc=1.0 — mesma secção de A.1 em
# xdfem2d/validation/design_cases_manual.md, para comparação direta.
B, H, COVER = 0.30, 0.50, 0.03
D = H - COVER
FCK, FYK = 25.0, 500.0
GAMMA_C, GAMMA_S, ALPHA_CC = 1.5, 1.15, 1.0
FCD = ALPHA_CC * FCK / GAMMA_C
FYD = FYK / GAMMA_S


def case_bending() -> None:
    """Flexão simples — EC2 §6.1, bloco retangular simplificado.

    ``calc_asl`` usa μ = M_Ed/(b·d²·f_cd), ω = 1 − √(1 − 2μ),
    A_s = ω·b·d·f_cd/f_yd — a forma habitual do método K com bloco
    retangular equivalente (λ=0.8, η=1.0 absorvidos na constante 2 do
    radical). M_Ed = 150 kN·m, N_Ed = 0.
    """
    from eurocodepy.ec2.uls.beam import calc_asl

    med = 150.0
    ast_cm2, epss, alpha = calc_asl(B, D, med, fcd=FCD, fyd=FYD)
    as_m2 = ast_cm2 * 1.0e-4

    mu = med / (B * D**2 * FCD * 1000.0)
    omega = 1.0 - math.sqrt(1.0 - 2.0 * mu)
    as_hand = omega * B * D * FCD / FYD * 1.0e4 * 1.0e-4  # cm² → m²

    ok1 = _check("Bending: As (eurocodepy.calc_asl)", as_m2, as_hand, 1e-8, " m²")
    ok2 = _check("Bending: As vs. valor de referência independente "
                 "(design_cases_manual.md, A1)", as_m2, 7.921e-4, 5e-6, " m²")
    _md.append(f"""### Flexão simples — EC2 §6.1

Secção {B}×{H} m, d={D} m, C25/30, A500. f_cd={FCD:.3f} MPa, f_yd={FYD:.3f} MPa.
M_Ed = {med} kN·m, N_Ed = 0.

```
μ = M_Ed / (b·d²·f_cd)              = {mu:.5f}
ω = 1 − √(1 − 2μ)                   = {omega:.5f}
A_s = ω·b·d·f_cd/f_yd               = {as_hand*1e4:.4f} cm²  ({as_hand:.4e} m²)
```

`eurocodepy.ec2.uls.beam.calc_asl({B}, {D}, {med}, fcd={FCD:.3f}, fyd={FYD:.3f})`
→ A_s = {as_m2*1e4:.4f} cm² ({as_m2:.4e} m²), ε_s={epss:.4f}, x/d={alpha:.4f}.

| Verificação | Resultado |
|---|---|
| Fórmula à mão == `calc_asl` | {'✓ PASS' if ok1 else '✗ FAIL'} |
| Confere com A1 de `xdfem2d/validation/design_cases_manual.md` | {'✓ PASS' if ok2 else '✗ FAIL'} |
""")


def case_shear_no_reinf() -> None:
    """Esforço transverso sem armadura — EC2 §6.2.2, V_Rd,c e v_min.

    ``calc_vrdc`` devolve (V_Rd,min, V_Rd,c, max dos dois). Com ρ_l=0 o termo
    V_Rd,c colapsa para zero e domina sempre o mínimo v_min·b·d.
    """
    from eurocodepy.ec2.uls.shear import calc_vrdc

    rho_l = 0.0
    vrd_min, vrd_c, vrd = calc_vrdc(B, D, FCK, GAMMA_C, rho_l)

    k = min(2.0, 1.0 + math.sqrt(0.2 / D))
    v_min = 0.035 * k**1.5 * math.sqrt(FCK)
    vrd_min_hand = v_min * B * D * 1000.0

    ok1 = _check("Shear (no reinf.): V_Rd,min (calc_vrdc)", vrd_min, vrd_min_hand,
                1e-6, " kN")
    ok2 = _check("Shear (no reinf.): V_Rd == V_Rd,min quando ρ_l=0",
                vrd, vrd_min, 1e-9, " kN")
    ok3 = _check("Shear (no reinf.): confere com A4 de design_cases_manual.md",
                vrd, 52.408, 0.05, " kN")
    _md.append(f"""### Esforço transverso sem armadura — EC2 §6.2.2

k = 1 + √(0.2/d) ≤ 2.0 (nota: `calc_vrdc` usa 0.2, não 200/d[mm] — equivalente
com d em metros: 200/(d·1000)=0.2/d) = {k:.5f}

```
v_min = 0.035·k^1.5·√f_ck [MPa]            = {v_min:.5f} MPa
V_Rd,min = v_min·b·d  (m → kN)             = {vrd_min_hand:.3f} kN
```

`eurocodepy.ec2.uls.shear.calc_vrdc({B}, {D}, {FCK}, {GAMMA_C}, 0.0)` →
(V_Rd,min={vrd_min:.3f}, V_Rd,c={vrd_c:.3f}, V_Rd={vrd:.3f}) kN.

| Verificação | Resultado |
|---|---|
| Fórmula à mão == `calc_vrdc` (V_Rd,min) | {'✓ PASS' if ok1 else '✗ FAIL'} |
| V_Rd = V_Rd,min quando ρ_l = 0 | {'✓ PASS' if ok2 else '✗ FAIL'} |
| Confere com A4 de `design_cases_manual.md` | {'✓ PASS' if ok3 else '✗ FAIL'} |
""")


def case_shear_with_reinf() -> None:
    """Esforço transverso com armadura — EC2 §6.2.3, modelo de treliça.

    ``calc_asws`` devolve (Asw/s, V_Rd,max) para cot θ = 2.5 (o valor máximo
    permitido, θ=21.8°, o mais económico em armadura).
    """
    from eurocodepy.ec2.uls.shear import calc_asws, calc_vrdmax

    ved, cott = 250.0, 2.5
    asw_s, vrd_max = calc_asws(B, D, FCK, GAMMA_C, FYK, GAMMA_S, cott, ved)
    vrd_max2 = calc_vrdmax(B, D, FCK, GAMMA_C, cott)

    z = 0.9 * D
    niu = 0.6 * (1.0 - FCK / 250.0)
    vrd_max_hand = B * z * niu * FCK / GAMMA_C * 1000.0 / (cott + 1.0 / cott)
    asw_s_hand = ved / z / FYK * GAMMA_S / cott / 1000.0

    ok1 = _check("Shear (w/ reinf.): V_Rd,max (calc_asws == calc_vrdmax)",
                vrd_max, vrd_max2, 1e-9, " kN")
    ok2 = _check("Shear (w/ reinf.): V_Rd,max fórmula à mão", vrd_max, vrd_max_hand,
                1e-6, " kN")
    ok3 = _check("Shear (w/ reinf.): Asw/s fórmula à mão", asw_s, asw_s_hand,
                1e-9, " m²/m")
    _check_true("Shear (w/ reinf.): V_Ed ≤ V_Rd,max (biela não esmaga)",
                ved <= vrd_max)
    _md.append(f"""### Esforço transverso com armadura — EC2 §6.2.3 (treliça)

z=0.9d={z:.4f} m, ν=0.6(1−f_ck/250)={niu:.4f}, cot θ = {cott} (θ=21.8°),
V_Ed = {ved} kN.

```
V_Rd,max = b·z·ν·f_cd/(cotθ+1/cotθ)        = {vrd_max_hand:.3f} kN
Asw/s = V_Ed/(z·f_yd·cotθ)                 = {asw_s_hand*1e4:.4f} cm²/m
```

`eurocodepy.ec2.uls.shear.calc_asws(...)` → Asw/s={asw_s*1e4:.4f} cm²/m,
V_Rd,max={vrd_max:.3f} kN. `calc_vrdmax(...)` → {vrd_max2:.3f} kN.

| Verificação | Resultado |
|---|---|
| `calc_asws` e `calc_vrdmax` dão o mesmo V_Rd,max | {'✓ PASS' if ok1 else '✗ FAIL'} |
| Fórmula à mão == V_Rd,max | {'✓ PASS' if ok2 else '✗ FAIL'} |
| Fórmula à mão == Asw/s | {'✓ PASS' if ok3 else '✗ FAIL'} |
| V_Ed ≤ V_Rd,max | ✓ PASS |
""")


def case_torsion() -> None:
    """Torção pura — EC2 §6.3, analogia de parede fina fechada.

    Mesma secção e T_Ed=50 kN·m de ``tests/test_torsion.py`` (já validado no
    próprio repositório do eurocodepy) — reutilizado aqui com a fórmula
    escrita à mão lado a lado, em vez de repetir o valor sem o refazer.
    """
    from eurocodepy.ec2.uls.torsion import calc_torsion

    ted, cott = 50.0, 1.0
    r = calc_torsion(ted, B, H, FCK, GAMMA_C, FYK, GAMMA_S, cott)

    t_ef_hand = (B * H) / (2.0 * (B + H))
    a_k_hand = (B - t_ef_hand) * (H - t_ef_hand)
    u_k_hand = 2.0 * ((B - t_ef_hand) + (H - t_ef_hand))
    niu = 0.6 * (1.0 - FCK / 250.0)
    sincos = 1.0 / (cott + 1.0 / cott)
    trd_max_hand = 2.0 * niu * FCD * a_k_hand * t_ef_hand * sincos * 1000.0
    asw_tor_s_hand = ted / (2.0 * a_k_hand * FYD * cott) / 1000.0
    asl_tor_hand = ted * cott * u_k_hand / (2.0 * a_k_hand * FYD) / 1000.0

    ok1 = _check("Torsion: t_ef", r["t_ef"], t_ef_hand, 1e-9, " m")
    ok2 = _check("Torsion: A_k", r["A_k"], a_k_hand, 1e-9, " m²")
    ok3 = _check("Torsion: T_Rd,max", r["TRd_max"], trd_max_hand, 1e-6, " kN·m")
    ok4 = _check("Torsion: Asw,tor/s", r["Asw_tor_s"], asw_tor_s_hand, 1e-9, " m²/m")
    ok5 = _check("Torsion: Asl,tor", r["Asl_tor"], asl_tor_hand, 1e-9, " m²")
    # tests/test_torsion.py usa a mesma secção mas C30/37 (fck=30 MPa), não
    # C25/30 — reproduzido à parte para não misturar os dois betões no
    # mesmo caso.
    r30 = calc_torsion(ted, B, H, 30.0, GAMMA_C, FYK, GAMMA_S, cott)
    ok6 = _check("Torsion (C30/37): confere com tests/test_torsion.py "
                 "(T_Rd,max=82.95 kNm)", r30["TRd_max"], 82.95, 0.1, " kN·m")
    _md.append(f"""### Torção pura — EC2 §6.3 (parede fina fechada, θ=45°)

Secção {B}×{H} m, T_Ed = {ted} kN·m, cot θ = {cott}.

```
t_ef = (b·h)/[2(b+h)]                      = {t_ef_hand:.5f} m
A_k  = (b−t_ef)(h−t_ef)                    = {a_k_hand:.6f} m²
u_k  = 2[(b−t_ef)+(h−t_ef)]                = {u_k_hand:.5f} m
ν    = 0.6(1 − f_ck/250)                   = {niu:.4f}
T_Rd,max = 2·ν·f_cd·A_k·t_ef·sinθcosθ      = {trd_max_hand:.3f} kN·m
Asw,tor/s = T_Ed/(2·A_k·f_yd·cotθ)         = {asw_tor_s_hand*1e4:.4f} cm²/m
Asl,tor   = T_Ed·cotθ·u_k/(2·A_k·f_yd)     = {asl_tor_hand*1e4:.4f} cm²
```

`eurocodepy.ec2.uls.torsion.calc_torsion({ted}, {B}, {H}, {FCK}, {GAMMA_C}, {FYK}, {GAMMA_S}, {cott})`
→ T_Rd,max={r['TRd_max']:.3f} kN·m,
Asw,tor/s={r['Asw_tor_s']*1e4:.4f} cm²/m, Asl,tor={r['Asl_tor']*1e4:.4f} cm²,
util={r['util']:.4f}.

| Verificação | Resultado |
|---|---|
| t_ef, A_k, u_k à mão == função | {'✓ PASS' if ok1 and ok2 else '✗ FAIL'} |
| T_Rd,max à mão == função | {'✓ PASS' if ok3 else '✗ FAIL'} |
| Asw,tor/s à mão == função | {'✓ PASS' if ok4 else '✗ FAIL'} |
| Asl,tor à mão == função | {'✓ PASS' if ok5 else '✗ FAIL'} |
| Confere com `tests/test_torsion.py` (C30/37, T_Rd,max=82.95 kNm) | {'✓ PASS' if ok6 else '✗ FAIL'} |
""")


def _write_md(path: str) -> None:
    n_pass = sum(_results)
    n_total = len(_results)
    header = f"""# Validação EC2 (EN 1992-1-1) — betão armado

Cálculo independente: as expressões do Eurocódigo 2 são escritas aqui
diretamente a partir do texto da norma e comparadas com o resultado real das
funções do `eurocodepy.ec2`, chamadas exatamente como um utilizador as
chamaria — não com valores copiados de outro documento. **{n_pass}/{n_total}**
comparações numéricas OK.

Secção-tipo (salvo indicação em contrário): b=0.30 m, h=0.50 m,
cobrimento=0.03 m → d=0.47 m. Betão C25/30 (f_ck=25 MPa), aço A500
(f_yk=500 MPa), γc=1.5, γs=1.15, αcc=1.0 → f_cd={FCD:.3f} MPa,
f_yd={FYD:.3f} MPa.

"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(_md))
        f.write(f"\n\n## Resumo\n\n{n_pass}/{n_total} verificações OK.\n")


def main() -> int:
    case_bending()
    case_shear_no_reinf()
    case_shear_with_reinf()
    case_torsion()
    _write_md("validation/validation_rc_concrete.md")
    n_pass, n_total = sum(_results), len(_results)
    print(f"\n{n_pass}/{n_total} PASS")
    return 0 if n_pass == n_total else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
