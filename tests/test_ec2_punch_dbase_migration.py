"""Regression test for dev/dbase_versioning.md phase 4: migrating
``PunchInput.dmax``/``PunchInput.eta_sys`` off hard-coded dataclass defaults
and onto ``dbase.get_edition_params("ec2", "punch_params", "2023")`` (i.e.
``Editions.ec2.2023.punch_params`` in eurocodes.json).

Run on Python >= 3.11 with eurocodepy importable (same requirement as the
rest of the punching-shear test suite).
"""
import copy

from eurocodepy import dbase
from eurocodepy.ec2.uls.punch_check import PunchInput


def _new_input(**kw):
    base = dict(d=0.2, bx=0.3, fck=30.0, fyk=500.0)
    base.update(kw)
    return PunchInput(**base)


def test_defaults_are_unchanged_after_the_migration():
    # The whole point of the migration is that consumers see no behaviour
    # change: these are the same 20.0 / 1.5 values the dataclass used to
    # hard-code as Python literals.
    i2004 = _new_input(edition="2004")
    assert i2004.dmax == 20.0
    assert i2004.eta_sys == 1.5

    i2023 = _new_input(edition="2023")
    assert i2023.dmax == 20.0
    assert i2023.eta_sys == 1.5


def test_2023_defaults_come_from_editions_data_not_from_python_literals():
    # Prove real consumption (not coincidental equal literals): change the
    # versioned data and confirm the dataclass default follows it.
    original = copy.deepcopy(dbase.db["Editions"]["ec2"]["2023"]["punch_params"])
    try:
        dbase.db["Editions"]["ec2"]["2023"]["punch_params"] = {
            "dmax": 32.0, "eta_sys": 1.8,
        }
        i2023 = _new_input(edition="2023")
        assert i2023.dmax == 32.0
        assert i2023.eta_sys == 1.8
    finally:
        dbase.db["Editions"]["ec2"]["2023"]["punch_params"] = original


def test_explicit_constructor_args_still_win_over_editions_data():
    i2023 = _new_input(edition="2023", dmax=16.0, eta_sys=1.2)
    assert i2023.dmax == 16.0
    assert i2023.eta_sys == 1.2


def test_2004_edition_never_reads_punch_params_section():
    # "2004" has no punch_params section at all; the dataclass must still
    # fall back to its literal defaults rather than erroring out.
    assert dbase.get_edition_params("ec2", "punch_params", "2004") == {}
    i2004 = _new_input(edition="2004")
    assert i2004.dmax == 20.0
    assert i2004.eta_sys == 1.5
