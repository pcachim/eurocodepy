# Copyright (c) 2026 Paulo Cachim
# SPDX-License-Identifier: MIT
"""Small standard-library compatibility shims.

``StrEnum`` was added in Python 3.11. This provides an identical fallback so the
package imports on 3.9/3.10 without changing any behaviour (members are still
strings and ``str(member)`` returns the value).
"""
from __future__ import annotations

try:
    from enum import StrEnum  # Python >= 3.11
except ImportError:  # pragma: no cover - exercised only on older interpreters
    from enum import Enum

    class StrEnum(str, Enum):
        """Backport of :class:`enum.StrEnum` for Python < 3.11."""

        __str__ = str.__str__

__all__ = ["StrEnum"]
