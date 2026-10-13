# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT

"""National annexes: one file per country, applied as patches on the Eurocode values.

The values of the Eurocodes (``data/eurocodes.json``) are the recommended ones.
What a National Annex changes is a *patch* kept in its own file,
``data/national_annexes/<COUNTRY>.json``::

    {
      "country": "PT",
      "name": "Portugal",
      "source": "...", "version": "...",
      "loads": {"wind": {...}, "seismic": {...}, "live": {...}},
      "editions": {
        "ec2": {
          "2023": {
            "source": "...",
            "overrides": {"Concrete.Parameters": {"fck_ref": 40.0}},
            "partial_factors": {"gamma_SH": 1.0}
          }
        }
      }
    }

* ``loads`` is the country data of an action (``wind``, ``seismic``, ``live``): the
  same structure as the ``locale``/``Locale`` entry of the EU data.
* ``editions.<eurocode>.<edition>`` has the same shape as ``Editions.<eurocode>.<edition>``
  in ``eurocodes.json``: ``overrides`` are dot-path deltas on ``Materials``
  and every other key is a section merged into the section of that name.

Passing ``annex="PT"`` to the functions that take it (``dbase.get_edition_data``,
``dbase.get_edition_params``, ``ec2.Concrete`` ...) applies the patch. ``None`` is the
recommended values. A file is read the first time it is needed; users can add
their own with :func:`register_annex`. Every function returns copies: the registry
is never exposed.
"""

import copy
import json
from pathlib import Path

_DIR = Path(__file__).parent / "data" / "national_annexes"
LOAD_KINDS = ("wind", "seismic", "live")
_TOP_KEYS = {"country", "name", "source", "version", "loads", "editions"}
_registry: dict[str, dict] = {}
_builtin_read = False


def _norm(country: str) -> str:
    return str(country).strip().upper()


def _validate(data: dict, origin: str) -> str:
    """Check the structure of an annex and return its normalised country code."""
    if not isinstance(data, dict) or "country" not in data:
        msg = f"{origin}: a national annex needs a 'country' key"
        raise ValueError(msg)
    unknown = set(data) - _TOP_KEYS
    if unknown:
        msg = f"{origin}: unknown keys {sorted(unknown)}; allowed: {sorted(_TOP_KEYS)}"
        raise ValueError(msg)
    country = _norm(data["country"])
    if not country:
        msg = f"{origin}: 'country' is empty"
        raise ValueError(msg)
    loads = data.get("loads", {})
    if not isinstance(loads, dict) or set(loads) - set(LOAD_KINDS):
        msg = f"{origin}: 'loads' must be an object with keys in {LOAD_KINDS}"
        raise ValueError(msg)
    editions = data.get("editions", {})
    if not isinstance(editions, dict):
        msg = f"{origin}: 'editions' must be an object"
        raise TypeError(msg)
    for eurocode, eds in editions.items():
        if not isinstance(eds, dict):
            msg = f"{origin}: editions.{eurocode} must be an object of editions"
            raise TypeError(msg)
        for ed, patch in eds.items():
            if not isinstance(patch, dict):
                msg = f"{origin}: editions.{eurocode}.{ed} must be an object"
                raise TypeError(msg)
            if not isinstance(patch.get("overrides", {}), dict):
                msg = f"{origin}: editions.{eurocode}.{ed}.overrides must be an object"
                raise TypeError(msg)
    return country


def _read_builtin() -> None:
    global _builtin_read  # noqa: PLW0603
    if _builtin_read:
        return
    _builtin_read = True
    for path in sorted(_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        country = _validate(data, path.name)
        _registry.setdefault(country, data)


def register_annex(source: str | Path | dict, *, replace: bool = False) -> str:
    """Add a national annex from a JSON file or a dict and return its country code.

    Raises ``ValueError`` if the country is already registered (the built-in ones
    included) unless ``replace=True``, or if the structure is not valid.
    """
    _read_builtin()
    if isinstance(source, dict):
        data, origin = copy.deepcopy(source), "annex"
    else:
        path = Path(source)
        origin = path.name
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    country = _validate(data, origin)
    if country in _registry and not replace:
        msg = f"national annex '{country}' is already registered (use replace=True)"
        raise ValueError(msg)
    _registry[country] = data
    return country


def unregister_annex(country: str) -> None:
    """Remove a registered national annex (built-in ones come back on a new process)."""
    _read_builtin()
    _registry.pop(_norm(country), None)


def available_annexes() -> list[str]:
    """Return the country codes of the registered national annexes."""
    _read_builtin()
    return sorted(_registry)


def get_annex(country: str) -> dict:
    """Return a copy of the national annex of ``country``.

    Raises ``ValueError`` listing the available ones if there is none.
    """
    _read_builtin()
    code = _norm(country)
    if code not in _registry:
        msg = f"Unknown national annex '{country}'. Available annexes: {available_annexes()}"
        raise ValueError(msg)
    return copy.deepcopy(_registry[code])


def get_edition_patch(country: str, eurocode: str, edition: str | None) -> dict:
    """Return a copy of the patch of ``country`` for one eurocode edition (``{}`` if none)."""
    annex = get_annex(country)
    return annex.get("editions", {}).get(eurocode, {}).get(edition, {})


def get_loads(country: str, kind: str) -> dict | None:
    """Return a copy of the ``kind`` (wind, seismic, live) data of an annex, or ``None``."""
    return get_annex(country).get("loads", {}).get(kind)
