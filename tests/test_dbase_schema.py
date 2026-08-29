"""Schema validation for eurocodes.json (dev/dbase_versioning.md phase 5).

A light structural check -- required keys and leaf types for the entries
that eurocodepy actually indexes into (e.g. ``Concrete.Grade.*.fck``) --
not a full pin of every value. It exists to catch the kind of regression
that would otherwise only surface as a runtime KeyError deep in some
calculation: a new grade added without ``fck``, a malformed ``Editions``
entry, and so on.
"""
import json
from pathlib import Path

import jsonschema
import pytest

DATA_DIR = Path(__file__).parent.parent / "src" / "eurocodepy" / "data"
SCHEMA_PATH = DATA_DIR / "eurocodes.schema.json"
DATA_PATH = DATA_DIR / "eurocodes.json"


@pytest.fixture(scope="module")
def schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def data():
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def test_schema_file_is_itself_valid_json_schema(schema):
    jsonschema.Draft7Validator.check_schema(schema)


def test_eurocodes_json_validates_against_schema(schema, data):
    jsonschema.validate(instance=data, schema=schema)


def test_missing_fck_on_a_concrete_grade_is_rejected(schema, data):
    import copy
    bad = copy.deepcopy(data)
    del bad["Eurocodes"]["Materials"]["Concrete"]["Grade"]["C30_37"]["fck"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=bad, schema=schema)


def test_missing_required_top_level_section_is_rejected(schema, data):
    import copy
    bad = copy.deepcopy(data)
    del bad["Eurocodes"]["Loads"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=bad, schema=schema)


def test_editions_section_with_arbitrary_extra_metadata_is_accepted(schema, data):
    # Editions.<eurocode>.<edition> is deliberately permissive
    # (additionalProperties: true) beyond default/source/overrides/
    # punch_params, so a future edition-specific key doesn't need a schema
    # change just to be added.
    import copy
    ok = copy.deepcopy(data)
    ok["Eurocodes"]["Editions"].setdefault("ec5", {})["2025"] = {
        "default": False,
        "some_future_field": {"anything": "goes"},
    }
    jsonschema.validate(instance=ok, schema=schema)
