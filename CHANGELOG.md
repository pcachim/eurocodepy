# Changelog

Versions up to 2026.7.28 are MIT-licensed; from 2027.0.0 on the package is licensed under the
GNU Lesser General Public License v3.0 or later.

## 2027.0.10 — 2026-10-13
### Added
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
  Tables G.2/G.3 and the minimum reinforcement of Eq. (12.1), and warn when `|mEdxy| ≥ 0,07·d²·fcd`.
- `ec2.concrete_strength_factors(fck, edition, loading)` returns `(η_cc, k_tc, k_tt)`.
### Deprecated
- `eurocodepy.dbobj` (and `eurocodepy.dbase.dbobj`): it was a snapshot of `db` built at import that did not follow
  national annexes registered later. It is now built only when asked for, with a `DeprecationWarning`, and is no longer in
  `__all__`; use dictionary access on `db` instead. It will be removed in 2028.
### Changed
- **Behaviour change (EN 1992-1-1:2004 membranes and slabs):**
  - `ec2.uls.eurocode2_membrane_check` verifies the concrete against `ν·fcd`, `ν = 0,6·(1 − fck/250)` (the `ν` of the shear
    struts; EN 1992-1-1:2004 gives none for membranes), and against `fcd` only where no reinforcement is required (biaxial
    compression). It compared with `fcd`, which was unsafe. `MembraneResult.details` has `nu` and `case`. Trace clauses now say
    "Annex F" (there is no §6.109 in EN 1992-1-1:2004).
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
