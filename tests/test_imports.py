"""Import smoke tests for the whole eurocodepy package.

These catch broken modules, bad `__init__` re-exports, and `__all__` entries
that do not actually resolve. Run on Python >= 3.11:

    pytest tests/test_imports.py
or:
    python tests/test_imports.py
"""
import importlib
import pkgutil

import eurocodepy


def _all_module_names():
    """Every importable module/sub-package under `eurocodepy`."""
    names = [eurocodepy.__name__]
    for info in pkgutil.walk_packages(eurocodepy.__path__,
                                      eurocodepy.__name__ + "."):
        names.append(info.name)
    return names


def test_import_top_level():
    assert eurocodepy is not None
    assert hasattr(eurocodepy, "__version__")


def test_all_submodules_import():
    """Importing every submodule must not raise."""
    failures = {}
    for name in _all_module_names():
        try:
            importlib.import_module(name)
        except Exception as exc:                       # noqa: BLE001
            failures[name] = f"{type(exc).__name__}: {exc}"
    assert not failures, "modules failed to import:\n" + "\n".join(
        f"  {k}: {v}" for k, v in sorted(failures.items()))


def test_all_exports_resolve():
    """Every name listed in a package `__all__` must be accessible on it."""
    missing = []
    for name in _all_module_names():
        try:
            mod = importlib.import_module(name)
        except Exception:                              # noqa: BLE001
            continue  # reported by test_all_submodules_import
        for attr in getattr(mod, "__all__", []):
            if not hasattr(mod, attr):
                missing.append(f"{name}.{attr}")
    assert not missing, "names in __all__ that don't resolve:\n" + "\n".join(
        f"  {m}" for m in sorted(missing))


def test_key_public_api():
    """A few representative public symbols are importable from the top level."""
    from eurocodepy import dbase, ec1, ec2, ec3, ec5, ec7, ec8, units, utils
    from eurocodepy.ec1.combos import Loads, Load, LoadType
    from eurocodepy.ec8.spectrum import calc_spectrum, calc_elastic_spectrum
    from eurocodepy.ec2.uls import calc_asws, calc_vrd, calc_vrdmax, RCBeam
    from eurocodepy.ec3.uls import eurocode3_combined_check, calc_Ncr_TF
    from eurocodepy.ec2.sls import crack_opening, is_cracked
    from eurocodepy.ec1.wind import q_p, c_o
    for obj in (dbase, ec1, ec2, ec3, ec5, ec7, ec8, units, utils,
                Loads, Load, LoadType, calc_spectrum, calc_elastic_spectrum,
                calc_asws, calc_vrd, calc_vrdmax, RCBeam,
                eurocode3_combined_check, calc_Ncr_TF,
                crack_opening, is_cracked, q_p, c_o):
        assert obj is not None


if __name__ == "__main__":
    test_import_top_level()
    test_all_submodules_import()
    test_all_exports_resolve()
    test_key_public_api()
    print("OK — all import checks passed (" +
          str(len(_all_module_names())) + " modules)")
