"""Shift-roster checker.

See ``SPEC-B.md`` for the format, the public API (``Shift``, ``RosterError``,
``parse_roster``, ``find_conflicts``, ``hours_by_person``) and the
``python -m roster check <file>`` command line.
"""

from __future__ import annotations

from roster.analysis import find_conflicts, hours_by_person
from roster.models import RosterError, Shift
from roster.parser import parse_roster

__all__ = [
    "Shift",
    "RosterError",
    "parse_roster",
    "find_conflicts",
    "hours_by_person",
]
