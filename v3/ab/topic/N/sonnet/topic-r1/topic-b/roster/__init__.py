"""Shift-roster checker.

Reads a small plain-text roster, finds scheduling conflicts, and totals
hours per person. See ``SPEC-B.md`` for the format, the public API and the
``python -m roster check <file>`` command line.
"""

from ._core import RosterError, Shift, find_conflicts, hours_by_person, parse_roster

__all__ = [
    "Shift",
    "RosterError",
    "parse_roster",
    "find_conflicts",
    "hours_by_person",
]
