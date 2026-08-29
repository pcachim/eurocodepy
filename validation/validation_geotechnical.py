"""Validação EC7 (EN 1997-1) — geotecnia, ``eurocodepy.ec7``.

Chama diretamente as funções de baixo nível do ``eurocodepy`` e compara com
a mesma fórmula da norma, escrita à mão, dentro deste script.

Requer o ``eurocodepy`` instalado a partir do código-fonte real do
repositório.

Correr:  python validation/validation_geotechnical.py
Gera:    validation/validation_geotechnical.md
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


def case_rankine() -> None:
    """Coeficientes de impulso de Rankine — muro vertical, terrapleno
    horizontal (θ=β=0): K_a=(1−sinφ)/(1+sinφ), K_p=1/K_a."""
    from eurocodepy.ec7.earth_pressures import pressure_coefficients

    phi_deg = 30.0
    phi = math.radians(phi_deg)
    ka, kp, kaq, kpq, *_ = pressure_coefficients(phi, 0.0, 0.0, 0.0, method="rankine")

    sphi = math.sin(phi)
    ka_hand = (1.0 - sphi) / (1.0 + sphi)
    kp_hand = 1.0 / ka_hand

    ok1 = _check("Rankine: K_a = (1−sinφ)/(1+sinφ)", ka, ka_hand, 1e-9)
    ok2 = _check("Rankine: K_p = 1/K_a", kp, kp_hand, 1e-9)
    ok3 = _check("Rankine: K_a(φ=30°) ≈ 1/3", ka, 1.0 / 3.0, 1e-3)
    ok4 = _check("Rankine: K_p(φ=30°) = 3.0", kp, 3.0, 1e-3)
    _md.append(f"""### Coeficientes de impulso de Rankine — EN 1997-1 (Anexo C)

Muro vertical, terrapleno horizontal (θ=β=0), φ={phi_deg}°.

```
K_a = (1 − sinφ)/(1 + sinφ)                = {ka_hand:.5f}
K_p = 1/K_a                                = {kp_hand:.5f}
```

`eurocodepy.ec7.earth_pressures.pressure_coefficients({phi:.5f}, 0, 0, 0, method="rankine")`
→ K_a={ka:.5f}, K_p={kp:.5f}.

| Verificação | Resultado |
|---|---|
| K_a à mão == função | {'✓ PASS' if ok1 else '✗ FAIL'} |
| K_p à mão == função | {'✓ PASS' if ok2 else '✗ FAIL'} |
| K_a(30°) ≈ 1/3 | {'✓ PASS' if ok3 else '✗ FAIL'} |
| K_p(30°) = 3.0 | {'✓ PASS' if ok4 else '✗ FAIL'} |
""")


def case_at_rest() -> None:
    """Coeficiente de impulso em repouso — fórmula de Jáky (aproximação
    normalmente citada K0=1−sinφ), com fator OCR."""
    from eurocodepy.ec7.earth_pressures import pressure_coefficients

    phi = math.radians(30.0)
    ka, kp, *_ = pressure_coefficients(phi, 0.0, 0.0, 0.0, method="inrest")
    k0_hand = (1.0 - math.sin(phi)) * math.sqrt(1.0)  # OCR=1, betha=0

    ok1 = _check("At-rest: K0 = (1−sinφ)·√OCR (Jáky, OCR=1, β=0)", ka, k0_hand,
                1e-9)
    ok2 = _check("At-rest: K0(φ=30°) = 0.5", ka, 0.5, 1e-9)
    _md.append(f"""### Coeficiente de impulso em repouso K0 — fórmula de Jáky

φ=30°, OCR=1 (solo normalmente consolidado), terrapleno horizontal.

```
K0 = (1 − sinφ)·√OCR                       = {k0_hand:.5f}
```

`pressure_coefficients({phi:.5f}, 0, 0, 0, method="inrest")` → K0={ka:.5f}.

| Verificação | Resultado |
|---|---|
| K0 à mão == função | {'✓ PASS' if ok1 else '✗ FAIL'} |
| K0(φ=30°) = 0.5 | {'✓ PASS' if ok2 else '✗ FAIL'} |
""")


def case_bearing_capacity() -> None:
    """Capacidade de carga de fundação superficial — EN 1997-1 Anexo D.

    Sapata contínua (aproximada por B=2 m, L=10⁶ m, para que B/L→0 e os
    fatores de forma s_q,s_γ→1, o caso "sapata corrida" clássico dos
    manuais), φ=30°, sem coesão, sem sobrecarga, carga centrada (H=0).
    """
    from eurocodepy.ec7.bearing_capacity import bearing_resistance

    phi_deg, gamma_soil = 30.0, 18.0
    phi = math.radians(phi_deg)
    b_width = 2.0
    r = bearing_resistance(Bx=b_width, By=1.0e6, Hx=0.0, Hy=0.0, N=1.0,
                           phi=phi, gamma=gamma_soil, q=0.0, c=0.0, drained=True)

    tanphi = math.tan(phi)
    nq_hand = math.exp(math.pi * tanphi) * math.tan(math.pi / 4.0 + phi / 2.0) ** 2
    nc_hand = (nq_hand - 1.0) / tanphi
    ng_hand = 2.0 * (nq_hand - 1.0) * tanphi
    bearing_hand = 0.5 * gamma_soil * b_width * ng_hand  # q=0, c=0, s≈1, i=1 (H=0)

    ok1 = _check("Bearing: N_q (EC7 Anexo D)", nq_hand, 18.401, 5e-3)
    ok2 = _check("Bearing: N_c", nc_hand, 30.140, 5e-3)
    ok3 = _check("Bearing: N_γ", ng_hand, 20.093, 5e-3)
    ok4 = _check("Bearing: R/A' (sapata corrida, sem coesão nem sobrecarga)",
                r, bearing_hand, 1e-3, " kN/m²")
    _md.append(f"""### Capacidade de carga de fundação superficial — EN 1997-1 Anexo D

Sapata corrida (aproximada por B={b_width} m, L→∞), φ={phi_deg}°, γ={gamma_soil} kN/m³,
c=0, q=0 (sem sobrecarga), carga centrada (H=0, sem inclinação).

```
N_q = e^(π·tanφ)·tan²(45°+φ/2)             = {nq_hand:.4f}
N_c = (N_q−1)/tanφ                         = {nc_hand:.4f}
N_γ = 2·(N_q−1)·tanφ                       = {ng_hand:.4f}
R/A' = 0.5·γ·B·N_γ  (s_γ≈1, i_γ=1, c=q=0)   = {bearing_hand:.3f} kN/m²
```

`eurocodepy.ec7.bearing_capacity.bearing_resistance(Bx={b_width}, By=1e6, Hx=0, Hy=0, N=1, phi={phi:.5f}, gamma={gamma_soil}, q=0, c=0)`
→ R/A'={r:.3f} kN/m².

| Verificação | Resultado |
|---|---|
| N_q à mão | {'✓ PASS' if ok1 else '✗ FAIL'} |
| N_c à mão | {'✓ PASS' if ok2 else '✗ FAIL'} |
| N_γ à mão | {'✓ PASS' if ok3 else '✗ FAIL'} |
| Fórmula completa à mão == função | {'✓ PASS' if ok4 else '✗ FAIL'} |
""")


def _write_md(path: str) -> None:
    n_pass, n_total = sum(_results), len(_results)
    header = f"""# Validação EC7 (EN 1997-1) — geotecnia

Cálculo independente: as expressões do Eurocódigo 7 são escritas aqui
diretamente a partir do texto da norma (Anexos C e D) e comparadas com o
resultado real das funções do `eurocodepy.ec7`. **{n_pass}/{n_total}**
comparações numéricas OK.

"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(_md))
        f.write(f"\n\n## Resumo\n\n{n_pass}/{n_total} verificações OK.\n")


def main() -> int:
    case_rankine()
    case_at_rest()
    case_bearing_capacity()
    _write_md("validation/validation_geotechnical.md")
    n_pass, n_total = sum(_results), len(_results)
    print(f"\n{n_pass}/{n_total} PASS")
    return 0 if n_pass == n_total else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
