"""Shift-roster checker.

See ``SPEC-B.md`` for the format, the public API (``Shift``, ``RosterError``,
``parse_roster``, ``find_conflicts``, ``hours_by_person``) and the
``python -m roster check <file>`` command line.
"""

from __future__ import annotations

from roster._conflicts import find_conflicts, hours_by_person
from roster._parse import parse_roster
from roster._shift import RosterError, Shift

__all__ = ["Shift", "RosterError", "parse_roster", "find_conflicts", "hours_by_person"]
