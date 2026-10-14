# Changelog

Versions up to 2026.7.28 are MIT-licensed; from 2027.0.0 on the package is licensed under the
GNU Lesser General Public License v3.0 or later.

## 2027.0.11 — 2026-10-14
### Added
- `UnitSystem.density` and `UnitSystem.power`; `convert_to` / `convert_from` support `TEMPERATURE` (differences), `DENSITY`, `WORK`,
  `ENERGY` and `POWER`.
- Documentation:
  - The home page is generated from `README.md` (`mkdocs/scripts/gen_index.py`: what is marked `docs:skip` goes, links to repository
    files become GitHub links, the navigation is added), so there is one text instead of two. The README is rewritten to the current API
    (grades, 2023 edition, annexes, units, reports; its examples ran against signatures that no longer exist).
  - The clause map and the EC2 pages link to the code reference.
  - `tests/test_docs_examples.py` also runs the code of the README and checks the code fences of every page.
- `tools/publish_release.sh` builds the documentation with `--strict` before tagging and deploys it (`mkdocs gh-deploy`) after the release.

### Changed
- `ec2/uls2023/__init__.py` lists the 2004 names it re-exports explicitly instead of `from eurocodepy.ec2.uls import *` (same result at
  run time). The code reference documented the 2004 functions under `ec2.uls2023.shear`, `torsion`, `punch`, `column` and
  `shear_torsion`, because `griffe` resolved those names through the star import.
- The code reference has no pages for private modules or for files that are not importable names (a stray `forces copy.py` had one).
- The 131 docstring warnings of the API reference are fixed (parameters documented with their types and the names of the signature,
  return annotations added where only the docstring had the type); `mkdocs build --strict` passes.
- `.gitignore`: `mkdocs/scripts/` is no longer ignored (the pattern `[Ss]cripts` hid `gen_ref_pages.py` and the other generators, which the
  documentation build needs).

### Fixed
- Unit systems (`units`, `ec1.forces`, `ec1.stresses`):
  - `SlabForce` and `ShellForce` converted `m_xx`, `m_yy`, `m_xy` as moments, but they are moments per unit width (kNm/m), which
    have the dimension of a force: `kN_m → N_mm` gave a factor 1·10⁶ instead of 1·10³ and `kN_m → kN_mm` 1·10³ instead of 1.
  - `TemperatureUnit.C` and `.K` had the same value, so `Enum` made `C` an alias of `K` (no Celsius at all); each member now carries
    `(scale, name)`. `UnitSystem.convert_temperature` compared a number with an enum member and used wrong formulas for every
    scale; it is rewritten through kelvin.
  - `convert_to` and `convert_from` returned 0.0 silently for `TEMPERATURE`, `DENSITY`, `WORK`, `ENERGY` and `POWER`; an unsupported
    type now raises `ValueError`.
  - `BaseStress.convert_to` did not convert and `Stresses3d.convert_to` / `Stresses2d.convert_to` raised `AttributeError`
    (they scaled fields that do not exist); adding stresses of different systems ignored the conversion. Stresses convert
    as pressures, return a copy, and `+` and `-` convert the second operand.

## 2027.0.10 — 2026-10-13
### Added
- Documentation: `modules/ec2` split into an index with the unit and sign conventions, EN 1992-1-1:2004, EN 1992-1-1:2023 and membranes/slabs/shells
  pages; a generated clause map of `uls2023` (`mkdocs/scripts/gen_clause_map.py`); a page on editions, national annexes and the `dbobj`
  migration; EC2 examples corrected. `tests/test_docs_examples.py` runs the code blocks of every page.
- **EN 1992-1-1:2023 Clause 4 (basis of design) in the database** (`Editions.ec2["2023"].partial_factors`):
  Table 4.3 (`γs`, `γc`, `γce` incl. the tested-`Ecm` value 1,3, `γv` for persistent/transient, fatigue,
  accidental and serviceability), `γSH` (4.3.1), `k_cip` (4.3.3(4)), Table 4.2 (`γP,fav/unfav`,
  `γΔP,sup/inf`) and Table 4.1 (`r_sup`/`r_inf` by type of prestress).
  `ec2.material_partial_factors(edition, situation)` and `ec2.prestress_partial_factors(edition)` read them.
- `Concrete`, `Concrete.from_fck`, `Reinforcement` and `Prestress` take `edition=` and `situation=`.
  With `edition="2023"`, `Concrete` uses the 2023 grades (incl. C100/115) and `Ecm`, and
  `fcd = η_cc·k_tc·fck/γc` (Eqs. 5.3-5.4, `η_cc = (40/fck)^(1/3) ≤ 1`) and `fctd = k_tt·fctk,0.05/γc`
  (Eq. 5.5), with the new attributes `eta_cc`, `k_tc`, `k_tt`, `gamma_ce`, `gamma_v`. `loading="late"`
  (default, `k_tc` = 1,0, `k_tt` = 0,8) or `"other"` (0,85 / 0,7) selects `k_tc`/`k_tt`; `k_cip=` multiplies `γc`.
  The 2023 `fcd` is not rounded. The default edition (2004) is unchanged.
- `ShearInput`, `SlabInput`, `MembraneInput`, `ShearTorsionInput` and `PunchInput` have
  `from_partial_factors(edition, situation, **fields)`, which sets `gamma_c`, `gamma_s` and `gamma_v` (Table 4.3)
  for the design situation (and `edition` in `PunchInput`), so the accidental/fatigue values need not be typed in.
- **EN 1992-1-1:2023 shear (Clause 8.2)**: `ec2.uls2023.shear` has the formulae of 8.2.1-8.2.6 (units m, MPa, kN):
  `ddg`, `τEd`, `τRdc,min` (8.20), `τRd,c` (8.27), the shear span `acs`/`av`/`kvp` (8.29-8.31), the effect of an
  axial force or prestress (8.32-8.37), planar members (8.21-8.26, 8.38-8.40), `cot θmin` (8.41), the
  compression field with vertical or inclined reinforcement (8.42-8.44, 8.58-8.63), the strain-based `ν` and chord
  forces (8.45-8.53, 8.56), concentrated loads near supports (8.55, 8.57), ducts (8.54), shear with transverse
  bending (8.64), web-flange shear (8.65-8.72) and interfaces (8.73-8.78, Table 8.2 in
  `Editions.ec2["2023"].shear_interface`). `ec2.uls2023.ShearInput` / `eurocode2_shear_check` /
  `ShearResult` run the 8.2.1 procedure (τRdc,min, τRd,c, then the flattest non-crushing strut with
  `ν = 0,5`, `cot θ ≤ cot θmin`) with `trace=` support. The 2004 shear functions keep their names in
  `uls2023`. Not covered: 8.2.2(8)-(11).
- **EN 1992-1-1:2023 detailing (Clause 12)**: `ec2.uls2023.detailing` has the minimum reinforcement rules (Eqs. 12.1-12.4,
  `ρw,min` with the class B/C reductions, `kdc`, `Mcr`), the beam (Table 12.1), slab (Table 12.2), column (Table 12.3)
  and wall/deep beam (Table 12.4) requirements, the shift of the moment curve (12.5)-(12.6), the punching-shear
  reinforcement limits (`φw,max`, Eqs. 12.7-12.9, spacings of Figure 12.7) and the integrity reinforcement against
  progressive collapse (Eqs. 12.10-12.12). The tables are NDPs (EC values).
- `uls2023.ShearInput.asw_min_s` now defaults to `None`: the minimum shear reinforcement is `ρw,min` of Eq. (12.4);
  `0.0` omits it.
- **National annexes** (`eurocodepy.annex`): one file per country in `data/national_annexes/<COUNTRY>.json`, applied as
  patches on the recommended values. Its `editions.<eurocode>.<edition>` has the shape of `Editions.<eurocode>.<edition>`
  (`overrides` dot-paths and sections, deep-merged), and `loads` (`wind`, `seismic`, `live`) hold the country data of an
  action. `register_annex` (file or dict, validated), `unregister_annex`, `available_annexes`, `get_annex` (a copy);
  an unknown country raises `ValueError` listing the available ones. `dbase.get_edition_data` / `get_edition_params` /
  `EurocodeMaterials` take `annex=`, as do `Concrete`, `Concrete.from_fck`, `Reinforcement`, `Prestress`,
  `material_partial_factors`, `prestress_partial_factors`, `concrete_strength_factors`,
  `PartialFactorsMixin.from_partial_factors`, `PunchInput.annex`, `uls2023.ShearInput.annex`,
  `uls2023.shear.interface_coefficients` / `calc_tau_rdi` and the table-based functions of `uls2023.detailing`.
- The NDP values of Tables 12.1-12.4 are in `Editions.ec2["2023"].detailing` (they were constants in code).
- **EN 1992-1-1:2023 torsion (Clause 8.3)**: `ec2.uls2023.torsion` has the thin-walled model (`t_eff`, `Ak`, `uk`, Eqs. 8.79-8.80),
  the reduced cover of 8.3.4(5), the resistances `τt,Rd,sw`, `τt,Rd,sl`, `τt,Rd,max` and their minimum (Eqs. 8.81-8.84), the
  `cot θ` range of Eq. (8.85), the share of `TEd` among sub-sections (8.3.1(3)) and the interaction of Eq. (8.86).
  `uls2023.calc_torsion` (same arguments and result keys as the 2004 one) designs the closed stirrups (8.82) and the
  longitudinal steel (8.83); `calc_torsion_resistance` gives the resistance of a section with given steel. `ν` (Annex G, not
  from Annex G): 0,60 at `cot θ = 1` (8.3.4(3)), otherwise Eq. (G.9) with `ε1 = max(G.10, G.11)` and the steel strain `fyd/Es`
  (0,38 at `cot θ = 2`, 0,29 at `cot θ = 2,5`); `nu=` overrides it.
- `uls2023.ShearTorsionInput` / `eurocode2_shear_torsion_check` are now the 2023 ones: the shear check of 8.2 and the torsion
  design of 8.3 with the shared `cot θ`, and the interaction of Eq. (8.86). `ShearTorsionResult` and
  `distribute_torsion_longitudinal` are shared with 2004.
- **EN 1992-1-1:2023 Annex G (membrane, shell and slab elements)**: `ec2.uls2023.annex_g` has the optimum reinforcement of
  membranes (Table G.1), the resistances for a chosen strut inclination (G.3-G.5), the deformation-capacity limits
  (G.6-G.7), `ν` (G.8-G.11, with the `ε1` estimates of G.3(7)), the sandwich model (G.12-G.17, `shell_design`), the slab
  formulae and optimum capacities (G.18-G.21, Tables G.2 and G.3) and the refined crack control of membranes (G.22-G.27,
  `cot θ` from the quartic G.27). `uls2023.MembraneInput` / `eurocode2_membrane_check` design the membrane with Table G.1
  and check `σcd ≤ ν·fcd` (`nu_mode="simple"` 0,4 or `"strain"`; `fcd` where no reinforcement is needed);
  `uls2023.slab_design.SlabInput` / `eurocode2_slab_check` size the four layers from `mEdx`, `mEdy`, `mEdxy` with
  Tables G.2/G.3 and the minimum reinforcement of Eq. (12.1). Where `|mEdxy| ≥ 0,07·d²·fcd` (or with in-plane forces
  `n_x`, `n_y`, `n_xy`) `method="auto"` (default) uses the **sandwich model** of G.4(1)-(3): two layers of thickness
  `2·c` at the lever arm `z = h − t`, each designed as a membrane (Table G.1, `As = ftd·t/fyd`) with the strut
  check `σcd ≤ ν·fcd` per layer (`nu_mode` "simple" 0,4 or "strain", Eq. G.9; `details["crushing"]`, `UserWarning`);
  `method="optimum"` forces the tables (warning outside their range), `"sandwich"` the layers.
- **Shell elements by the sandwich model**: `ec2.uls.eurocode2_shell_check` (`ShellInput`, `ShellResult`) designs the four
  orthogonal reinforcements of a shell element (forces `n` and moments `m`) with two layers of thickness `2·c`
  (EN 1992-2 Annex LL, Eqs. LL.113/LL.134-LL.142), each as a membrane (Annex F, as LL.112 asks), `As = ftd·t/fyd`, and
  checks the strut of each layer as the membrane (`strut_model` `"annex_f"` default or `"6.109"`). It first checks whether the
  element is cracked (Annex LL (107), Eqs. LL.101-LL.112, the Ottosen criterion on the principal stresses through the
  thickness, with the transverse shears `v_x`, `v_y`: `uls.shell.ottosen_phi`, `shell_stresses_at_level`, `shell_cracking`);
  an element that is not cracked has zero areas and only `σmin ≤ fcd` is checked (LL (103)); `check_cracking=False` designs it as
  cracked. Out-of-plane shear (LL (106), (109)-(111), (114)b; `ShellInput.v_x`, `v_y`, `check_shear`): the principal shear
  `vEd0 = √(vx² + vy²)` (LL.121-LL.122), the inner layer as a beam of unit width (6.2.2/6.2.3) with `ρl = ρx·cos²φ0 +
  ρy·sin²φ0` (LL.123) and, where stirrups are needed (`ShellResult.asw_s`, m²/m²), the truss force `vEd0·cot θ` added to the outer
  layers (LL.124-LL.127, LL.143-LL.148); `details["shear"]`. `uls2023.slab_design` / `eurocode2_shell_check` verify the shear
  with 8.2 (G.4(4); Eqs. 8.21-8.26, 8.38-8.40, 8.27, 8.44) and add the chord force (8.2.3(8), as Annex LL) to the sandwich layers.
  Not covered from Annex LL: the eccentric reinforcement of (115)c and the general `zn ≠ zt` of (108).
  `ν = 0,4` or Eq. G.9, `ηcc·ktc`), built on `slab_design`'s sandwich method. Tension and sagging moments are positive;
  `calc_reinf_shell` follows Annex LL (its "top" layer, `m` positive for tension on the top face).
- `ec2.get_concrete(concrete, edition=None, situation=, loading=, k_cip=, annex=)` builds the `Concrete` of an edition from a
  string or a `ConcreteClass` (it only accepted a string or a `Concrete`); a `Concrete` of another edition than the one
  asked for is refused instead of being used silently.
- **EN 1992-1-1:2023 Annex B (time-dependent behaviour)**: `ec2.time_dependent2023` — strength and stiffness development
  (`βcc`, `fcm(t)`, `fctm(t)`, `Ecm(t)`, Table B.2, Eqs. B.1-B.4), temperature-adjusted age and `t0,adj` (B.17-B.18), creep
  (`creep_basic`, `creep_drying`, `creep_coefficient`, non-linear B.19, characteristic values, `creep_strain`, creep function
  and superposition B.40-B.41), shrinkage (`shrinkage_basic`, `shrinkage_drying`, `shrinkage_total`, `αNDP`), the test
  calibration factors `ξ` (B.7), the simplified values after 50 years of Tables 5.2 and 5.3 (`creep_coefficient_50y`,
  `shrinkage_50y`; data in `Editions.ec2["2023"].creep_shrinkage`, Table 5.3 is an NDP: `annex=`) and the relaxation of
  prestressing steel (Table B.4, Eqs. B.43-B.44). Scalar and validated (RH 20-100 %, 12 ≤ fck ≤ 100 MPa, `t0 ≥ 1 d`, class
  CS/CN/CR); the functions of ages, humidity and strength accept numpy arrays. The equations reproduce Tables 5.2 and 5.3.
  `ec2.sls.creep_coef` / `shrink_strain` were already this Annex B model (array-friendly, without validation); they now
  delegate to it, so the arguments are validated (RH 20-100 %, 12 ≤ fck ≤ 100 MPa, `t0 ≥ 1 d`, `t ≥ t0`) and a strength
  development class other than CS/CN/CR is an error instead of a silent CN. The individual `beta`/`epsilon` helpers of
  those modules are unchanged.
- `ec2.concrete_strength_factors(fck, edition, loading)` returns `(η_cc, k_tc, k_tt)`.
### Deprecated
- `eurocodepy.dbobj` (and `eurocodepy.dbase.dbobj`): it was a snapshot of `db` built at import that did not follow
  national annexes registered later. It is now built only when asked for, with a `DeprecationWarning`, and is no longer in
  `__all__`; use dictionary access on `db` instead. It will be removed in 2028.
### Changed
- **Behaviour change (EN 1992-1-1:2004 membranes and slabs):**
  - `ec2.uls.eurocode2_membrane_check` verifies the concrete strut as EN 1992-1-1:2004 Annex F.1(3)-(4) asks: `σ ≤ fcd`
    where no reinforcement is required and "not generally exceed `ν·fcd`", `ν = 0,6·(1 − fck/250)` (Expression 6.5), with
    reinforcement. It compared with `fcd`, which was unsafe. `MembraneInput.strut_model="6.109"` uses instead the more detailed
    **EN 1992-2:2005 §6.109(103)** (to which EN 1992-2 Annex F refers): `0,85·fcd·(1 + 3,8α)/(1 + α)²` without reinforcement
    (Eq. 6.110) and `ν'·fcd·(1 − 0,032·|θ − θel|)` with yielding reinforcement (Eq. 6.112; `θ` the strut angle of the
    design, `θel` the elastic principal compression direction, `|θ − θel|` limited to 15°: beyond it
    `details["strut"]["angle_ok"]` is false and the strength is that of 15°). New `uls.shell.annex_f_strut_limit`,
    `membrane_strut_limit`, `strut_limit`, `principal_stresses`, `elastic_compression_angle` and
    `deformation_capacity_ok_2004` (`½·ft* ≤ ft ≤ 2·ft*`, F.1(4)); `MembraneResult.details` has `nu` (= σcd,max/fcd), `case`,
    `strut` and `strut_model`. Trace clauses cite Annex F.1 and §6.109 (there is no §6.109 in EN 1992-1-1:2004: it is EN 1992-2's).
  - `ec2.uls.calc_reinf_plane` returns `cot θ = inf` for `n_xy = 0` with compression in x (was 0) and `nan` where no
    reinforcement is required (the angle is undefined; it was a meaningless number).
  - `ec2.uls.slab_check` (and `uls2023.slab_design`) have `SlabInput.min_reinf`: `"demand"` (default, as before) gives 0 to
    a face whose moment needs no reinforcement; `"bottom"` also gives the minimum reinforcement to the bottom faces
    (§9.3.1.1: the span tension face) and `"all"` to the four faces. The 2004 check also warns when `x/d` exceeds 0,45
    (0,35 above C50/60): over-reinforced strip, no compression reinforcement.
- The Portuguese wind, seismic and live-load data moved from `eurocodes.json` to `data/national_annexes/PT.json`; it is
  merged into `db["Loads"]` at import, so `WindLoads["locale"]["PT"]`, `SeismicLoads["Locale"]["PT"]`,
  `Loads["Live"]["Locale"]["PT"]` and every function that reads them are unchanged.
- `Editions.ec2["2023"].overrides["Concrete.Parameters"]`: `k_tc`/`k_tt` key `short_loading` renamed
  `late_loading` (the condition is a design loading not expected for 3 months after casting).
### Fixed
- `ec8.get_spectrum_parameters` raised `NameError` (a stray `import pandas` had landed inside the docstring) and had `1_3` and `1_4` as the
  integers 15 and 10 instead of 1,5 and 1,0 m/s²; `ec8.draw_spectrum_ec8` raised `NameError` (`plt`) for the same reason.
- `ec5.Timber.design_values` returned `ft90d` under the key `kmod`.
- `ec5.GetTimberDesignValues` could not run (it read the service class and the load duration from the same combination attribute,
  which nothing sets). It now takes `service_class=` and uses the shortest action of each combination for `kmod` (EN 1995-1-1, 3.1.3(2)),
  with `attributes["loadduration"]` as an override; it raises `ValueError` instead of printing when the duration is unknown.
- `ec7.seismic_bearing_resistance` raised `AttributeError` on every call (`append` on an array); for coherent soil `Nmax` used a
  numerical constant instead of `cu`; the cases outside the domain of the criterion (uplift, `N ≥ Nmax`) counted as verified and now do not.
- `ec3.Bolt(d, grade)` with a numeric diameter used the gross area as the thread area, overestimating the tension resistance and the shear
  in the thread by about 28 % (M20: 120,6 kN instead of 94,1 kN). It takes the area of the standard size, else `0,78·A`.
- `ec3.BoltedConnection` against EN 1993-1-8, Table 3.4: `Fv_Rd` had `αv` reversed (0,5 for 4.6 and 5.6 and a non-existent 6.4, 0,6 for
  everything else): it is 0,6 for 4.6, 5.6 and 8.8 and 0,5 for 4.8, 5.8, 6.8 and 10.9 in the threaded plane, so grades 6.8 and 10.9 were 20 %
  unsafe. `Ft_Rd` with countersunk bolts used `k2 = 0,6` (it is 0,63). `Fb_Rd` used the `fu` of the outer plate with the thickness of the thinner one;
  it is now the smaller of the two plates, each with its own. `check()["Check"]` left out the punching check, and `Ft_Ed=None` (allowed by the
  signature) raised. The default `p1` was `REC_P2·d0` (3,0 d0) instead of `REC_P1·d0` (3,75 d0), which lowered `αd` and `Fb_Rd` by 25 %.
- `ec3.WeldConnection` added the inertia of each weld without the parallel-axis term and not about the centroid of the group (two welds
  100 mm apart gave `Iyy` 2083 instead of 2,5·10⁶ mm⁴), the elastic moduli divided by the wrong coordinate, and ignored the welds passed to
  the constructor. It now has `xg`, `yg` and centroidal `inertia_*` and `w_el_*`.
- `ec1.LoadCombinations.evaluate_all` and `worst_case` called a `LoadCombination.evaluate` that did not exist; it now does.
- Documentation: every example of every page now runs (module pages for EC1, EC3, EC5, EC7, EC8 and utils rewritten to the current API,
  tutorials and how-to guides fixed); `tests/test_docs_examples.py` keeps it so.
- `ec2.uls.shear.calc_vrd` returned `max(VRd,s, VRd,max)`; EN 1992-1-1:2004, 6.2.3 asks for the minimum, so the resistance was overestimated
  whenever the stirrups governed. `calc_asl` docstring: it returns three values (the area in cm², the steel strain and x/d).
- **EN 1992-1-1:2023 concrete grades** (`Editions.ec2["2023"]`, `Concrete(..., edition="2023")`): C55/67 to C90/105 had the
  2004 values of `fctm` and `fctk,0.05` (e.g. C60/75 `fctm` 4,4 instead of 4,3) and the reduced `εc2`, `εcu2`, `n` of
  high-strength concrete. They are now Table 5.1 (`fctm`, `fctk,0.05`, `fctk,0.95`, `fcm`) and 8.1.2(1) (`εc2` = 2,0 ‰,
  `εcu` = 3,5 ‰, `n` = 2 for every class); C12/15 and C16/20 are added; `Concrete.from_fck(..., edition="2023")` follows.
  The 2004 data and the creep/shrinkage functions (EN 1992-1-1:2004 3.1.4, Annex B: 2023 has Tables 5.2/5.3) are unchanged.
- `ec2.uls.calc_reinf_shell` (sandwich model, 2004) always raised `TypeError` (it called `cal_reinf_shell_plan` with six
  scalars); it returns the 8 values of the two layers now (`nan` if the layers overlap). Its units and the layer labels
  (its "top" is Annex G's "bottom") are documented.
- `ec2.uls.slab_check` returned `nan` silently where the moment exceeds a singly reinforced strip (`calc_asl` has no
  solution): it issues a `UserWarning`; the strip design is `slab_check.strip_reinforcement`.
- `seismic_get_params` returned the spectrum of the shared database and wrote `ImportanceCoef` into it; it now returns a
  copy and leaves the database untouched. Its "invalid importance class" error listed the seismic types instead of the
  classes. `wind_get_params` raised a bare `KeyError` for an unknown code, zone or terrain; it raises a `ValueError`
  that lists the valid values.
- `Concrete.fctk_05` was the table value times `fctm` (C30/37: 5,8 MPa instead of 2,0), so `Concrete.fctd` was
  too high (3,9 MPa instead of 1,3). `fctk_95` and the rest were not affected.

## 2027.0.9 — 2026-10-12
### Added
- **EN 1995-1-1:2025 timber parameters in the database** (`Editions.ec5["2025"]`, from Tables 4.1-4.5 and
  5.4-5.8): service classes incl. **SC4** (Table 4.2, `Timber.ServiceClassData`), `k_mod` of every product
  of Table 5.4 (ST SC3 0.55-1.00 and SC4 0.50-0.90; GL/LVL/PW SC3 0.55-1.00; panels, CLT, bonded-in rods),
  `k_def` (Table 5.5), `k_h` (Table 5.6, incl. LVL and tension parallel to grain), the material partial
  factors by product (`material_safety`, Table 4.3), the connection partial factors
  (`connection_safety`, Tables 4.4/4.5), `f_c,0,k` factors for SC (`Timber.fc0k_factor`), CLT limits,
  `G0.05/Gmean`, shrinkage and swelling (Tables 5.7/5.8) and the load-duration table.
- `Timber`, `SolidTimber`, `Glulam`, `LVL`, `CLT` and `TimberClass` take `edition=`; `None` (default) is the
  2004 edition, unchanged. `ServiceClass` now also has `SC4`; a grade with no `k_mod` for a service class
  raises a `KeyError` that says so.
### Fixed
- `dbase.get_edition_data` / `get_edition_params` shared lists and dicts of an edition's overrides with the
  global database (editing a result edited the database); they are copied now.
- EC5 §6.4 (`ec5.uls.special_beams`, also in `uls2025` for now): `check_tapered_edge`
  (`k_m,α`, single tapered beams) and `check_apex_zone` (`k_l`, `k_p`, `k_r`, `k_dis`,
  `k_vol`, tension perpendicular to the grain and its interaction with shear) for double
  tapered, curved and pitched cambered beams, with `trace=` support (`CalcReport`). Checked against
  the text of EN 1995-1-1:2004 §6.4; the apex-zone volume of curved beams is passed by the caller
  (`ApexInput.zone_volume`). `ec5.uls2025.special_beams` follows EN 1995-1-1:2025 §8.3.3/§8.3.4: `k_τ`, `k_dis` 1.3/1.15,
  `k_vol = (600/h_ap)^0.3`, the interaction with `k_v`, and the (optional) reinforcement recommendations of §8.3.1. `ApexInput.reinforced` / `a1`: with
  reinforcement Eqs. 8.67 and 8.70 are not applied (§8.3.4.2(1)) and `F_t,90,rf,Ed` (Eq. 8.76) is returned. `PlaneReinforcement`, `check_plane_reinforcement` (Eqs. 8.48-8.51),
  `reinforcement_layout` (Figure 8.11, `k_ka`) and `check_dowel_spacing` (§8.3.4.2(4)).
  New `ec5.uls2025.fasteners` (EN 1995-1-1:2025 §11.2.2: `f_w,k` of screws and rods, Eqs. 11.1, 11.3,
  11.4) and `DowelReinforcement` / `check_dowel_reinforcement` (§8.3.2(8)).

## 2027.0.8 — 2026-10-05
### Fixed
- `CircularCrossSection`: radius of gyration was `r/√2` (the polar radius); now `r/2`.
- `RectangularCrossSection`: `inertia_y` / `inertia_z` were swapped relative to
  `bend_mod_*` and `radius_*`. Now y is the strong axis (`I_y = b·h³/12`) and z the weak axis
  (`I_z = h·b³/12`), following EN 1995-1-1.
- **Behaviour change:** EC5 lateral-torsional buckling (`M_y,crit`, `k_crit`) uses `I_z`, which
  for rectangular sections was returning the strong-axis value. Results for rectangular beams
  change (previously unconservative).

## 2027.0.7 — 2026-10-04
### Added
- Default EN 1990 action factors and characteristic values of live loads.

## 2027.0.6 — 2026-10-04
### Added
- `tools/publish_release.sh`: tag, GitHub release and PyPI upload in one step.
### EC5 / EC3 / data (2026-10-02 and 2026-10-03)
- EC5: shear `k_cr`, torsion modulus, combined shear + torsion; calculation-report fixes.
- EC3 §6.3.3: corrected Annex B `k_zz` (class 1/2) and added Annex A (Method 1).
- Fixed the CHS catalogue: minor-axis properties were in shifted columns.
- Renamed "prEN 1992-1-1:2023" to "EN 1992-1-1:2023".

## 2027.0.1 – 2027.0.5 — 2026-08-29 to 2026-10-01
- EC2: anchorage and lap lengths of ribbed bars (EN 1992-1-1 §8.4, §8.7).
- EC2 N–M (bending + axial) design: corrections and tests.
- Updated material data in `eurocodes.json`.
- Fixed missing subscript underscore in EC2 trace symbols.
- `calc_vedp`: avoid division by zero when `N_Ed = 0`.
- EC3/EC5 cross-section updates; repository clean-up (removed generated files, `.DS_Store`).
- Added a `validation/` suite that checks the package's functions against independent
  hand-written implementations of the Eurocode expressions, plus per-edition data
  (`uls2023`) handling and tests.

## 2027.0.0 — 2026-08-13
### Changed
- **License: MIT → GNU LGPL v3.0 or later.** Added `COPYING`, new `LICENSE.md`, SPDX headers
  (`LGPL-3.0-or-later`), updated README, docs and PyPI classifier.
### Added
- EC2 slab and membrane checks (`slab_check`, `membrane_check`).
- Torsion improvements; EC5 and EC3 cross-section updates; calculation-report updates.
