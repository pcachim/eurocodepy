# Naming coherence review — `ec2.uls` / `ec2.uls2023`

A review of the public function / class names in the EC2 ULS packages, and how
they relate across editions and to the EC3 / EC5 conventions. No code changed by
this review — it records findings and recommendations.

## Inventory

`ec2.uls` (full package):

| Module | Public names |
|--------|--------------|
| `beam` | `calc_asl`, `calc_mrd`, `get_bend_params`, `RCBeam` |
| `bend_axial` | `calc_asl_nm`, `design_rcbeam_nm` |
| `bend_circ` | `sign`, `epsilon`, `conc_stress`, `concreteforces`, `steelforces`, `bend_circular` |
| `punch` | `calc_perimeters`, `calc_vedp`, `calc_vrdcp`, `calc_vrdcminp` |
| `punch_check` | `eurocode2_punching_check`, `PunchInput`, `PunchResult` |
| `shear` | `calc_vrd`, `calc_vrdmax`, `calc_asws`, `calc_vrdc` |
| `shear_check` | `eurocode2_shear_check`, `ShearInput`, `ShearResult` |
| `shell` | `calc_reinf_plane`, `cal_reinf_shell_plan`, `calc_reinf_shell` |
| `torsion` | `calc_torsion` |

`ec2.uls2023`: **only** `punch` (`calc_perimeters`, `calc_vedp`, `calc_vrdcp`,
`calc_vrdcminp`).

## Findings

### 1. Package-scope asymmetry (biggest issue)
`ec2.uls2023` contains **only punching**, yet the name promises the whole :2023
ULS. A caller importing `uls2023` expects the :2023 flexure/shear too and finds
nothing. The edition split effectively exists only for punching but is packaged
as a full ULS. Cross-code this is also inconsistent: `ec3` has no `uls2023`
(only `uls`); `ec5` has `uls` + `uls2025`.

Also, the in-force base (2004) lives in an **unsuffixed** `uls` while the draft
is `uls2023`; when :2023 becomes the base, `uls` (no year) turns ambiguous.

### 2. `calc_` prefix — mostly consistent, with outliers
Most helpers use `calc_*`. Off-pattern:
- **`cal_reinf_shell_plan`** (`shell.py`) — looks like a **typo**: missing “c”
  (`cal_` vs `calc_`) and `plan` vs `plane`. Next to `calc_reinf_plane` /
  `calc_reinf_shell` it clearly destoa; likely should be renamed or made private.
- **`get_bend_params`** — `get_` instead of `calc_`, the only one.
- **`bend_circ.py`** — breaks the convention entirely (`sign`, `epsilon`,
  `conc_stress`, `concreteforces`, `steelforces`, `bend_circular`): no prefix and
  mixed styles (`conc_stress` abbreviated+underscored vs `concreteforces` /
  `steelforces` unseparated). Several read like helpers that should be private.

### 3. Punching `…p` suffix is cryptic and asymmetric
Punching appends `p`: `calc_vedp`, `calc_vrdcp`, `calc_vrdcminp`. Shear does not
(`calc_vrdc`). So `vrdc` (shear) vs `vrdcp` (punching) differ by one trailing
letter, and `vrdcminp` is dense. The module (`shear` vs `punch`) already
disambiguates, so the `p` is redundant and hurts readability.

### 4. Composite naming — the new ones align, flexure does not
The new composites `eurocode2_shear_check` / `eurocode2_punching_check` (with
`ShearInput/Result`, `PunchInput/Result`) follow the cross-code convention
`eurocodeN_*_check` (cf. `eurocode3_section_check`, `eurocode3_member_check`,
`eurocode5_section_check`). But this exposes two EC2 inconsistencies:
- The **flexure composite** is `calc_asl_nm` (and `design_rcbeam_nm`), not
  `eurocode2_*_check` — so EC2 now mixes two composite styles, and
  `design_rcbeam_nm` vs `calc_asl_nm` even use different verbs for the same
  domain.
- EC3 and EC5 each have a **single unified** section check (N+M+V+T); EC2 has no
  `eurocode2_section_check` — it is split into flexure + shear + punching.

## Recommendations (priority order)

1. **Fix the typo** `cal_reinf_shell_plan` → `calc_reinf_shell_plan` (or make it
   private if it is an internal helper).
2. **Resolve the `uls2023` scope**: either complete the :2023 edition or make the
   name reflect that only punching exists there; decide a consistent
   edition-splitting strategy across EC2/EC3/EC5.
3. **Uniformise conventions**: bring `bend_circ` and `get_bend_params` onto the
   `calc_*` pattern (or `_`-prefix true internals).
4. **Align the composites**: consider `eurocode2_*_check` names for the EC2
   flexure composite, and possibly a unified `eurocode2_section_check`, to match
   EC3/EC5.
5. **(Nice-to-have)** reconsider the punching `…p` suffix for readability.

Any rename is a public-API change → deprecate-and-alias, and bump the version.
