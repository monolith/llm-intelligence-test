"""Shift-roster checker.

See ``SPEC-B.md`` for the format, the public API (``Shift``, ``RosterError``,
``parse_roster``, ``find_conflicts``, ``hours_by_person``) and the
``python -m roster check <file>`` command line.
"""

from __future__ import annotations

from roster.conflicts import find_conflicts, hours_by_person
from roster.parsing import RosterError, Shift, parse_roster

__all__ = ["Shift", "RosterError", "parse_roster", "find_conflicts", "hours_by_person"]
