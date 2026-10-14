# Editions and National Annexes

EurocodePy keeps the values of a Eurocode edition and of each National Annex as data, not as code.
Functions that depend on the edition take `edition=` and those that depend on Nationally Determined
Parameters (NDPs) take `annex=` as well.

## Editions

`eurocodes.json` holds the recommended values of the **2004** edition (the default,
`edition=None`) and, under `Editions`, the changes of other editions:

```json
"Editions": {"ec2": {"2023": {
    "overrides": {"Concrete.Grade": {}, "Concrete.Parameters": {}},   // dot-paths replacing 2004 data
    "partial_factors": {},         // sibling sections: Tables 4.1 to 4.3
    "punch_params": {}, "shear_interface": {}, "detailing": {}, "creep_shrinkage": {}
}}}
```

```python
from eurocodepy import dbase, ec2

dbase.get_edition_data("ec2", "2023")                          # {"Concrete": {"Grade", "Parameters"}, ...}
dbase.get_edition_params("ec2", "partial_factors", "2023")     # a sibling section
ec2.get_concrete("C30/37", edition="2023", situation="accidental")
```

`get_concrete` accepts a grade name, a `ConcreteClass` or a `Concrete`; a `Concrete` of another
edition is refused rather than silently converted. The 2023 edition has the grades of Table 5.1
(C12/15 to C100/115); 2004 has C12/15 to C90/105.

## National Annexes

An annex is a patch with the same shape as an `Editions` entry, kept in its own file
(`data/national_annexes/<COUNTRY>.json`) and deep-merged over the recommended values. `PT` is built
in; the package only ships values it can source and never invents an annex.

!!! warning "What the Portuguese annex contains"
    `PT.json` has the **loads** (wind, seismic and live-load data of Portugal) and, so far, **no patch of
    EN 1992-1-1:2023**: `annex="PT"` in `Concrete`, `material_partial_factors`, `detailing`, … returns the values
    recommended by the Eurocode, the same as `annex=None`. The NDPs of the Portuguese annex for the 2023
    edition still have to be added (see `register_annex` to do it yourself) and must be checked against the
    published annex before design use.

| Function | Purpose |
|----------|---------|
| `available_annexes()` | codes of the loaded annexes |
| `get_annex(code)` | the annex's data |
| `register_annex(source, replace=False)` | add an annex (file path or dict) and return its code |
| `unregister_annex(code)` | remove it |

```python
import eurocodepy as ec

ec.register_annex({
    "country": "XX",
    "editions": {"ec2": {"2023": {"partial_factors": {"materials": {"persistent": {"gamma_c": 1.4}}}}}},
    "loads": {"wind": {}, "seismic": {}, "live": {}},   # optional: next to the "EU" data
})
ec.ec2.Concrete("C30/37", edition="2023", annex="XX").gamma_c   # 1.4
ec.ec2.Concrete("C30/37", edition="2023").gamma_c               # 1.5, annex=None: the Eurocode
ec.unregister_annex("XX")
```

An unknown code raises `ValueError` listing the available ones. The `loads` of an annex are merged
into `db["Loads"]`, so `wind_get_params`, `seismic_get_params` and the EC1/EC7/EC8 functions find the
country.

## `dbobj` is deprecated

`eurocodepy.dbobj` was a snapshot of `db` with attribute access, built at import, so it did not
follow annexes registered later. It is now built only when asked for, with a `DeprecationWarning`,
and will be removed in 2028. Use dictionary access on `db`, or the edition-aware functions:

| Before | Now |
|--------|-----|
| `dbobj.Materials.Concrete.Grade` | `db["Materials"]["Concrete"]["Grade"]` |
| `dbobj.Loads.Wind...` | `db["Loads"]["Wind"][...]` |
| the 2023 tables, by hand | `dbase.get_edition_data("ec2", "2023", annex=...)` |
| a section of an edition | `dbase.get_edition_params("ec2", "detailing", "2023", annex=...)` |
