# Changelog

Versions up to 2026.7.28 are MIT-licensed; from 2027.0.0 on the package is licensed under the
GNU Lesser General Public License v3.0 or later.

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
