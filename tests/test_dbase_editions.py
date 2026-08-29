"""Regression tests for the additive edition-aware layer in ``dbase.py``.

These confirm phase 1+2 of dev/dbase_versioning.md: an empty ``Editions``
section in eurocodes.json is a no-op, the existing module-level convenience
variables (``ConcreteParams``, ``SteelGrades``, etc.) keep resolving exactly
as before, and the new ``get_edition_data``/``EurocodeMaterials`` API is
additive, copy-based, and never mutates the shared global state.
"""
import copy

import pytest

from eurocodepy import dbase


def test_editions_key_present_and_empty_by_default():
    assert "Editions" in dbase.db
    # No edition overrides have been populated yet for any eurocode.
    assert dbase.db["Editions"] == {} or all(
        isinstance(v, dict) for v in dbase.db["Editions"].values()
    )


def test_convenience_variables_unchanged():
    # These must keep pointing at the exact same sub-dicts as before the
    # Editions section existed.
    assert dbase.ConcreteGrades is dbase.ConcreteMaterial["Grade"]
    assert dbase.ConcreteParams is dbase.ConcreteMaterial["Parameters"]
    assert dbase.SteelGrades is dbase.SteelMaterial["Grade"]
    assert dbase.SteelParams is dbase.SteelMaterial["Parameters"]
    assert dbase.TimberGrades is dbase.TimberMaterial["Grade"]
    assert dbase.ReinforcementGrades is dbase.ReinforcementMaterial["Grade"]
    assert dbase.PrestressGrades is dbase.PrestressMaterial["Grade"]
    assert dbase.BoltGrades is dbase.Bolts["Grade"]


def test_get_edition_data_without_editions_returns_base_copy():
    base = dbase.get_edition_data("ec2")
    assert base == dbase.Materials
    assert base is not dbase.Materials
    assert base["Concrete"] is not dbase.Materials["Concrete"]


def test_get_edition_data_is_never_a_shared_reference():
    base = dbase.get_edition_data("ec2")
    base["Concrete"]["Grade"]["C30_37"]["fck"] = -1.0
    assert dbase.ConcreteGrades["C30_37"]["fck"] != -1.0


def test_get_edition_data_applies_overrides_and_preserves_siblings():
    original_editions = copy.deepcopy(dbase.db.get("Editions", {}))
    try:
        dbase.db["Editions"] = {
            "ec2": {
                "2004": {"default": True},
                "2023": {
                    "default": False,
                    "overrides": {
                        "Concrete.Parameters": {"alpha_cc": 1.0, "kcc": 1.0},
                    },
                },
            }
        }
        d2023 = dbase.get_edition_data("ec2", "2023")
        assert d2023["Concrete"]["Parameters"]["alpha_cc"] == 1.0
        assert d2023["Concrete"]["Parameters"]["kcc"] == 1.0
        # sibling fields not touched by the override must survive
        assert "gamma_cc" in d2023["Concrete"]["Parameters"]

        d2004_explicit = dbase.get_edition_data("ec2", "2004")
        d2004_default = dbase.get_edition_data("ec2")
        assert d2004_explicit == d2004_default == dbase.Materials
    finally:
        dbase.db["Editions"] = original_editions


def test_unknown_edition_falls_back_to_base():
    base = dbase.get_edition_data("ec2", "does-not-exist")
    assert base == dbase.Materials


def test_eurocode_materials_wrapper_read_access():
    original_editions = copy.deepcopy(dbase.db.get("Editions", {}))
    try:
        dbase.db["Editions"] = {
            "ec2": {
                "2004": {"default": True},
                "2023": {
                    "default": False,
                    "overrides": {"Concrete.Parameters": {"alpha_cc": 1.0}},
                },
            }
        }
        mats = dbase.EurocodeMaterials("ec2", "2023")
        assert mats.Concrete["Parameters"]["alpha_cc"] == 1.0
        assert mats["Concrete"]["Parameters"]["alpha_cc"] == 1.0
        with pytest.raises(AttributeError):
            mats.NotARealField
    finally:
        dbase.db["Editions"] = original_editions
