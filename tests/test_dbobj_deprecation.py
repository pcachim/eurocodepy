"""dbobj is deprecated: built on request, with a warning, and never at import."""
import subprocess
import sys

import pytest

import eurocodepy as ec
from eurocodepy import dbase


def test_dbobj_warns_and_still_works():
    with pytest.warns(DeprecationWarning, match="dbobj is deprecated.*2028"):
        obj = ec.dbobj
    assert obj.Materials.Concrete.Grade.C30_37.fck == dbase.ConcreteGrades["C30_37"]["fck"]
    with pytest.warns(DeprecationWarning):
        assert dbase.dbobj.Materials.Concrete.Parameters.gamma_cc == 1.5


def test_dbobj_is_a_fresh_snapshot_each_time():
    ec.register_annex({"country": "DB", "loads": {"wind": {
        "base_velocity": {"Z": {"vb0": 1.0}}, "terrain": {}, "cprob": 1.0, "k_I": 1.0}}})
    try:
        with pytest.warns(DeprecationWarning):
            assert ec.dbobj.Loads.Wind.locale.DB.base_velocity.Z.vb0 == 1.0
    finally:
        ec.unregister_annex("DB")
    with pytest.warns(DeprecationWarning):
        assert not hasattr(ec.dbobj.Loads.Wind.locale, "DB")


def test_unknown_attributes_still_raise_and_dbobj_is_not_exported():
    with pytest.raises(AttributeError, match="no attribute 'nothing'"):
        _ = ec.nothing
    with pytest.raises(AttributeError, match="no attribute 'nothing'"):
        _ = dbase.nothing
    assert "dbobj" not in ec.__all__


def test_importing_the_package_does_not_build_or_warn():
    code = ("import warnings; warnings.simplefilter('error'); import eurocodepy; "
            "from eurocodepy import *; import eurocodepy.dbase as d; "
            "assert 'dbobj' not in vars(d), 'built at import'")
    r = subprocess.run([sys.executable, "-W", "error", "-c", code],  # noqa: S603
                       capture_output=True, text=True, check=False)
    assert r.returncode == 0, r.stderr
