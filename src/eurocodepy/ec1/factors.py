# Copyright (c) 2024 Paulo Cachim
# SPDX-License-Identifier: MIT
"""Default partial and combination factors of the actions (EN 1990).

``action_factors`` answers "what do I put in :class:`~eurocodepy.ec1.combos.Load`
for this action?" so that callers do not carry their own copy of EN 1990
Table A1.1. The numbers live in ``data/action_factors.json`` (non-live actions)
and in ``Loads/Live/Locale`` of ``eurocodes.json`` (the live-load categories).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

from eurocodepy import dbase

from .combos import LoadType

_DATA = Path(__file__).resolve().parent.parent / "data" / "action_factors.json"

_KIND_OF_TYPE = {
    LoadType.PERMANENT: "permanent",
    LoadType.LIVE: "live",
    LoadType.WIND: "wind",
    LoadType.SNOW: "snow",
    LoadType.EARTHQUAKE: "earthquake",
    LoadType.TEMPERATURE: "temperature",
    LoadType.FIRE: "fire",
    LoadType.ACCIDENTAL: "accidental",
    LoadType.OTHER: "other",
}


class ActionFactors(NamedTuple):
    """(gamma_fav, gamma_unf, psi0, psi1, psi2) of one action."""

    gamma_fav: float
    gamma_unf: float
    psi0: float
    psi1: float
    psi2: float


@lru_cache(maxsize=1)
def _table() -> dict:
    with _DATA.open(encoding="utf-8") as fh:
        return json.load(fh)["Actions"]


def _row(entry: dict) -> ActionFactors:
    return ActionFactors(*(float(entry[k]) for k in ActionFactors._fields))


def action_factors(
    kind: LoadType | str,
    category: str | None = None,
    locale: str = "EU",
) -> ActionFactors:
    """Default EN 1990 factors of an action.

    Args:
        kind: a :class:`LoadType`, or one of ``permanent``, ``live``, ``wind``,
            ``snow``, ``temperature``, ``construction``, ``earthquake``,
            ``accidental``, ``fire``, ``other``.
        category: for ``live``, the EN 1991-1-1 usage category (``"A"`` to
            ``"J"``; a subcategory such as ``"A1"`` is accepted); for ``snow``,
            ``"<=1000"`` (default) or ``">1000"`` (site altitude in metres).
            Ignored by the other kinds.
        locale: ``"EU"`` or ``"PT"``; selects the live-load category table.

    Raises:
        KeyError: unknown kind, category or locale.

    """
    name = _KIND_OF_TYPE[kind] if isinstance(kind, LoadType) else str(kind).lower()
    table = _table()
    if name not in table:
        msg = f"Unknown action kind {kind!r}; expected one of {sorted(table)}"
        raise KeyError(msg)

    if name == "live" and category:
        cats = dbase.Loads["Live"]["Locale"][locale]
        key = category[0].upper()
        if key not in cats:
            msg = f"Unknown live-load category {category!r}; expected one of {sorted(cats)}"
            raise KeyError(msg)
        c = cats[key]
        base = table["live"]
        return ActionFactors(base["gamma_fav"], base["gamma_unf"],
                             float(c["psi_0"]), float(c["psi_1"]), float(c["psi_2"]))

    if name == "snow":
        variants = table["snow"]
        key = category or "<=1000"
        if key not in variants:
            msg = f"Unknown snow variant {category!r}; expected one of {sorted(variants)}"
            raise KeyError(msg)
        return _row(variants[key])

    return _row(table[name])


class LiveLoadValues(NamedTuple):
    """Characteristic values of a live-load usage category (EN 1991-1-1 6.3).

    ``q_k`` is the uniformly distributed load [kN/m²] and ``Q_k`` the
    concentrated load [kN]; the recommended value and the range a National
    Annex may choose within are given.
    """

    q_k: float
    Q_k: float
    q_k_min: float
    q_k_max: float
    Q_k_min: float
    Q_k_max: float


def live_load_values(usage: str, locale: str = "EU") -> LiveLoadValues:
    """Characteristic live-load values of a usage category.

    Args:
        usage: ``"B"``, ``"F"``, ``"H"`` ... for a category that has one set
            of values, or the subcategory (``"A1"``, ``"C2"``, ``"D2"``,
            ``"E1"`` ...) for one that is divided.
        locale: ``"EU"`` or ``"PT"``.

    Raises:
        KeyError: unknown usage, or a category with no distributed-load
            values (``"I"``, ``"J"``) or one that needs its subcategory.

    """
    cats = dbase.Loads["Live"]["Locale"][locale]
    key = usage.strip().upper()
    entry = cats[key[0]]
    if len(key) > 1:
        entry = entry[key]
    try:
        return LiveLoadValues(float(entry["q_k_rec"]), float(entry["Q_k_rec"]),
                              float(entry["q_k_min"]), float(entry["q_k_max"]),
                              float(entry["Q_k_min"]), float(entry["Q_k_max"]))
    except KeyError:
        msg = (f"Live-load category {usage!r} has no single set of "
               "characteristic values; give a subcategory such as 'A1' or 'C2'")
        raise KeyError(msg) from None
