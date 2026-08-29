"""Validação EC1 (EN 1991) — ações, ``eurocodepy.ec1``.

Chama diretamente as funções de baixo nível do ``eurocodepy`` e compara com
a mesma fórmula da norma, escrita à mão, dentro deste script.

Cobre: pressão dinâmica do vento (EN 1991-1-4 §4), tensões principais 3D
(usadas nas verificações de resistência de placas/cascas), e um caso simples
de combinação ULS (EN 1990 §6.4.3.2, Eq. 6.10). ``ec1/snow/`` está vazio no
`eurocodepy` atual (só o docstring do módulo, sem funções) — não há nada
para validar aí ainda, e fica registado como tal, não omitido em silêncio.

Requer o ``eurocodepy`` instalado a partir do código-fonte real do
repositório.

Correr:  python validation/validation_actions.py
Gera:    validation/validation_actions.md
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


def case_wind_pressure() -> None:
    """Pressão dinâmica de pico q_p(z) — EN 1991-1-4 §4, terreno plano.

    Categoria de terreno II (z0=0.05 m, zmin=2 m), vb,0=27 m/s (zona A,
    tipicamente), z=10 m, sem orografia (c_o=1, terreno plano — Lu grande).
    """
    from eurocodepy.ec1.wind.pressure import c_o, c_r, q_p, v_b, v_m

    z0, z0ii, zmin = 0.05, 0.05, 2.0
    z, vb0 = 10.0, 27.0
    k_r_hand = 0.19 * (z0 / z0ii) ** 0.07
    cr_hand = k_r_hand * math.log(max(z, zmin) / z0)
    vb_hand = vb0

    cr = c_r(z, zmin, z0, z0ii)
    co = c_o(z, 0.0, 0.0)  # H=0 -> terreno plano, c_o=1 por definição
    vb = v_b(vb0)

    ok1 = _check("Wind: c_r (fator de rugosidade)", cr, cr_hand, 1e-9)
    ok2 = _check("Wind: c_o = 1.0 (terreno plano, H=0)", co, 1.0, 1e-12)
    ok3 = _check("Wind: v_b = v_b,0 (sem fatores sazonal/direcional)", vb, vb_hand, 1e-9,
                " m/s")

    vm = v_m(z, vb, cr, co)
    vm_hand = cr_hand * co * vb_hand
    ok4 = _check("Wind: v_m(z) = c_r·c_o·v_b", vm, vm_hand, 1e-9, " m/s")

    k_i = 1.0
    iv_hand = k_i / (co * math.log(max(z, zmin) / z0))
    qp_hand = 0.5 * (1.0 + 7.0 * iv_hand) * vm_hand**2 * 1.25
    qp = q_p(z, vb, zmin, z0, cr, co, rho=1.25, k_I=k_i)
    ok5 = _check("Wind: q_p(z) = 0.5·(1+7·I_v)·v_m²·ρ", qp, qp_hand, 1e-6, " Pa")
    _md.append(f"""### Pressão dinâmica de pico q_p(z) — EN 1991-1-4 §4

Terreno categoria II (z0={z0} m, z0,II={z0ii} m, zmin={zmin} m), sem
orografia (terreno plano, c_o=1). v_b,0={vb0} m/s, z={z} m, ρ=1.25 kg/m³.

```
k_r = 0.19·(z0/z0,II)^0.07                 = {k_r_hand:.5f}
c_r(z) = k_r·ln(max(z,zmin)/z0)            = {cr_hand:.5f}
v_b = c_season·c_dir·v_b,0  (=1·1·{vb0})    = {vb_hand:.3f} m/s
v_m(z) = c_r·c_o·v_b                       = {vm_hand:.4f} m/s
I_v(z) = k_I/(c_o·ln(max(z,zmin)/z0))       = {iv_hand:.5f}
q_p(z) = 0.5·(1+7·I_v)·v_m²·ρ               = {qp_hand:.3f} Pa  ({qp_hand/1000:.4f} kN/m²)
```

`eurocodepy.ec1.wind.pressure.q_p({z}, {vb:.3f}, {zmin}, {z0}, {cr:.5f}, {co}, rho=1.25)`
→ q_p={qp:.3f} Pa.

| Verificação | Resultado |
|---|---|
| c_r à mão == `c_r` | {'✓ PASS' if ok1 else '✗ FAIL'} |
| c_o == 1 (terreno plano) | {'✓ PASS' if ok2 else '✗ FAIL'} |
| v_b à mão == `v_b` | {'✓ PASS' if ok3 else '✗ FAIL'} |
| v_m à mão == `v_m` | {'✓ PASS' if ok4 else '✗ FAIL'} |
| q_p à mão == `q_p` | {'✓ PASS' if ok5 else '✗ FAIL'} |
""")


def case_principal_stresses() -> None:
    """Tensões principais 2D (estado plano de tensão) — decomposição espectral.

    σxx=100, σyy=0, τxy=40 MPa, resto zero. Fórmula fechada clássica:
    σ1,2 = (σxx+σyy)/2 ± √[((σxx−σyy)/2)² + τxy²].
    """
    from eurocodepy.utils.stress import principals

    sigxx, sigyy, sigxy = 100.0, 0.0, 40.0
    eigvals, _eigvecs = principals(sigxx, sigyy, 0.0, sigxy, 0.0, 0.0)

    avg = (sigxx + sigyy) / 2.0
    r = math.sqrt(((sigxx - sigyy) / 2.0) ** 2 + sigxy**2)
    s1_hand, s2_hand = avg + r, avg - r
    # np.linalg.eigh returns eigenvalues in ascending order.
    got_sorted = sorted(eigvals)
    hand_sorted = sorted([s1_hand, s2_hand, 0.0])

    ok1 = _check("Principal stresses: σ_max", got_sorted[-1], hand_sorted[-1],
                1e-9, " MPa")
    ok2 = _check("Principal stresses: σ_min", got_sorted[0], hand_sorted[0],
                1e-9, " MPa")
    ok3 = _check("Principal stresses: σ_mid == σ_zz == 0 (estado plano)",
                got_sorted[1], 0.0, 1e-9, " MPa")
    _md.append(f"""### Tensões principais (decomposição espectral 3D) — EN 1991 (uso geral)

Estado plano de tensão: σxx={sigxx}, σyy={sigyy}, τxy={sigxy} MPa, resto zero.

```
σ_méd = (σxx+σyy)/2                        = {avg:.4f} MPa
R = √[((σxx−σyy)/2)²+τxy²]                 = {r:.4f} MPa
σ1 = σ_méd + R                             = {s1_hand:.4f} MPa
σ2 = σ_méd − R                             = {s2_hand:.4f} MPa
σ3 = σzz                                   = 0 MPa
```

`eurocodepy.utils.stress.principals({sigxx}, {sigyy}, 0.0, {sigxy}, 0.0, 0.0)`
(decomposição espectral 3×3 completa, `numpy.linalg.eigh`) → eigenvalues=
{[round(float(v), 4) for v in sorted(eigvals)]}.

| Verificação | Resultado |
|---|---|
| σ_max à mão == eigh | {'✓ PASS' if ok1 else '✗ FAIL'} |
| σ_min à mão == eigh | {'✓ PASS' if ok2 else '✗ FAIL'} |
| σ_mid == 0 (fora do plano) | {'✓ PASS' if ok3 else '✗ FAIL'} |
""")


def case_uls_combo() -> None:
    """Combinação ULS simples — EN 1990 §6.4.3.2, Eq. 6.10: 1.35G+1.5Q.

    Um caso permanente (G) e um variável (Q, ψ0=0.6) — a combinação
    resultante deve reduzir-se exatamente à forma clássica 1.35G+1.5Q,
    porque com uma só ação variável não há termo de acompanhamento (ψ0) a
    aplicar a mais nenhuma ação.
    """
    from eurocodepy.ec1.combos import Load, Loads, LoadType

    loads = Loads()
    loads.add(Load(name="G", load_type=LoadType.PERMANENT,
                   gamma_fav=1.0, gamma_unf=1.35, psi0=0.0, psi1=0.0, psi2=0.0))
    loads.add(Load(name="Q", load_type=LoadType.LIVE,
                   gamma_fav=0.0, gamma_unf=1.5, psi0=0.6, psi1=0.0, psi2=0.3))
    combos = loads.get_ULS_combos()

    assert len(combos) == 1, f"esperado 1 combinação, obtidas {len(combos)}"
    combo = next(iter(combos.values()))
    factor_g = combo.factors["G"][1]
    factor_q = combo.factors["Q"][1]

    ok1 = _check("ULS combo: fator de G (Eq. 6.10)", factor_g, 1.35, 1e-9)
    ok2 = _check("ULS combo: fator de Q (Eq. 6.10, ação variável de base)",
                factor_q, 1.5, 1e-9)
    _md.append(f"""### Combinação ULS — EN 1990 §6.4.3.2, Eq. 6.10

Uma ação permanente G (γ_unf=1.35) e uma variável Q (γ_unf=1.5, ψ0=0.6). Com
uma só ação variável, a Eq. 6.10 (Σγ_G·G + γ_Q·Q) não tem termos de
acompanhamento a aplicar — o resultado é diretamente 1.35G+1.5Q.

`Loads` com G e Q, `.get_ULS_combos()` → combinação "{combo.name}", com
factors={{ {', '.join(f'{k}: {v[1]}' for k, v in combo.factors.items())} }}.

| Verificação | Resultado |
|---|---|
| Fator de G == 1.35 | {'✓ PASS' if ok1 else '✗ FAIL'} |
| Fator de Q == 1.5 | {'✓ PASS' if ok2 else '✗ FAIL'} |
""")


def case_snow_not_implemented() -> None:
    """``eurocodepy.ec1.snow`` está vazio — nada a validar ainda."""
    import eurocodepy.ec1.snow as snow_mod

    public_names = [n for n in dir(snow_mod) if not n.startswith("_")]
    _check_true("Snow (EC1-1-3): módulo vazio, confirmado (não omitido em "
                "silêncio)", public_names == [],
                f"nomes públicos encontrados: {public_names}")
    _md.append(f"""### Neve (EN 1991-1-3)

`eurocodepy.ec1.snow` existe como pacote mas está **vazio** (só o docstring
do módulo, sem funções) — confirmado por introspeção
(`dir(eurocodepy.ec1.snow)` sem nomes públicos), não assumido. Sem código
para validar aqui ainda.
""")


def _write_md(path: str) -> None:
    n_pass, n_total = sum(_results), len(_results)
    header = f"""# Validação EC1 (EN 1991 / EN 1990) — ações

Cálculo independente: as expressões do Eurocódigo 1 (e da combinação de
ações do EN 1990) são escritas aqui diretamente a partir do texto da norma e
comparadas com o resultado real das funções do `eurocodepy.ec1`.
**{n_pass}/{n_total}** comparações numéricas OK.

"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(_md))
        f.write(f"\n\n## Resumo\n\n{n_pass}/{n_total} verificações OK.\n")


def main() -> int:
    case_wind_pressure()
    case_principal_stresses()
    case_uls_combo()
    case_snow_not_implemented()
    _write_md("validation/validation_actions.md")
    n_pass, n_total = sum(_results), len(_results)
    print(f"\n{n_pass}/{n_total} PASS")
    return 0 if n_pass == n_total else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
